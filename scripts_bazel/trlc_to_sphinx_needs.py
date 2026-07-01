# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

"""
Convert TRLC requirements into a sphinx-needs ``needs.json`` file.

This is the inverse of ``sphinx_needs_to_trlc.py``. It reads a TRLC data file
written against the S-CORE requirements metamodel (package ``ScoreReq``,
https://github.com/eclipse-score/tooling/blob/main/bazel/rules/rules_score/trlc/config/score_requirements_model.rsl)
and emits the corresponding requirement sphinx-needs elements.

Only the S-CORE requirement object types are converted; everything else is
ignored:

* ``ScoreReq.FeatReq``          -> ``feat_req`` (feature requirement)
* ``ScoreReq.CompReq``          -> ``comp_req`` (component requirement)
* ``ScoreReq.AssumedSystemReq`` -> ``stkh_req`` (stakeholder requirement)
* ``ScoreReq.AoU``              -> ``aou_req``  (assumption of use)

``derived_from`` references (e.g. ``SampleSEooC.FEAT_001@1``) are rendered as
sphinx-needs links carrying a version constraint (``FEAT_001[version==1]``).
Several input files can be converted at once so that requirements referenced
across packages (e.g. the feature requirements a component requirement derives
from) end up in the same ``needs.json`` and the links resolve.

The output is a ``needs.json`` document compatible with sphinx-needs and the
S-CORE metamodel (see ``score_metamodel``).
"""

import argparse
import json
import logging
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# ScoreReq metamodel type -> sphinx-needs type (inverse of sphinx_needs_to_trlc).
_TYPE_MAP: dict[str, str] = {
    "FeatReq": "feat_req",
    "CompReq": "comp_req",
    "AssumedSystemReq": "stkh_req",
    "AoU": "aou_req",
}

# Human readable type names as used by sphinx-needs (``type_name``).
_TYPE_NAME: dict[str, str] = {
    "feat_req": "Feature Requirement",
    "comp_req": "Component Requirement",
    "stkh_req": "Stakeholder Requirement",
    "aou_req": "Assumption of Use Requirement",
}

# ScoreReq.Asil enum literal -> sphinx-needs ``safety`` value.
_ASIL_MAP: dict[str, str] = {
    "QM": "QM",
    "B": "ASIL_B",
    "D": "ASIL_D",
}


# -----------------------------------------------------------------------------
# Tokenizer
# -----------------------------------------------------------------------------


class _Token:
    __slots__ = ("kind", "value")

    def __init__(self, kind: str, value: str):
        self.kind = kind
        self.value = value

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Token({self.kind!r}, {self.value!r})"


_PUNCT: dict[str, str] = {
    "{": "LBRACE",
    "}": "RBRACE",
    "[": "LBRACKET",
    "]": "RBRACKET",
    "=": "EQUALS",
    "@": "AT",
    ",": "COMMA",
}


def _tokenize(text: str) -> list[_Token]:  # noqa: C901
    """Turn a TRLC source string into a flat list of tokens.

    Handles ``//`` line comments, ``/* */`` block comments, single and triple
    quoted strings, integers, punctuation and (qualified) names.
    """
    tokens: list[_Token] = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]

        # Whitespace.
        if c.isspace():
            i += 1
            continue

        # Line comment.
        if text.startswith("//", i):
            end = text.find("\n", i)
            i = n if end == -1 else end + 1
            continue

        # Block comment.
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue

        # Triple quoted strings.
        for triple in ('"""', "'''"):
            if text.startswith(triple, i):
                end = text.find(triple, i + 3)
                if end == -1:
                    raise ValueError("Unterminated triple-quoted string")
                tokens.append(_Token("STRING", text[i + 3 : end]))
                i = end + 3
                break
        else:
            # Single quoted string.
            if c == '"':
                j = i + 1
                buf: list[str] = []
                while j < n:
                    ch = text[j]
                    if ch == "\\" and j + 1 < n:
                        buf.append(text[j + 1])
                        j += 2
                        continue
                    if ch == '"':
                        break
                    buf.append(ch)
                    j += 1
                if j >= n:
                    raise ValueError("Unterminated string")
                tokens.append(_Token("STRING", "".join(buf)))
                i = j + 1
                continue

            # Punctuation.
            if c in _PUNCT:
                tokens.append(_Token(_PUNCT[c], c))
                i += 1
                continue

            # Integer.
            if c.isdigit():
                j = i
                while j < n and text[j].isdigit():
                    j += 1
                tokens.append(_Token("INT", text[i:j]))
                i = j
                continue

            # Name (possibly dotted, e.g. ScoreReq.Asil.B).
            if c.isalpha() or c == "_":
                j = i
                while j < n and (text[j].isalnum() or text[j] in "_."):
                    j += 1
                tokens.append(_Token("NAME", text[i:j]))
                i = j
                continue

            raise ValueError(f"Unexpected character {c!r} at offset {i}")
        # Continue outer loop after a triple-quoted string was consumed.
    return tokens


# -----------------------------------------------------------------------------
# Parser
# -----------------------------------------------------------------------------


class _Parser:
    """Minimal recursive-descent parser for TRLC data files."""

    def __init__(self, tokens: list[_Token]):
        self._tokens = tokens
        self._pos = 0

    def _peek(self) -> _Token | None:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _next(self) -> _Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def parse(self) -> list[dict[str, Any]]:
        """Parse the whole file and return a list of object dictionaries."""
        objects: list[dict[str, Any]] = []
        while self._peek() is not None:
            tok = self._peek()
            assert tok is not None
            if tok.kind == "NAME" and tok.value == "package":
                self._next()  # package
                self._next()  # name
                continue
            if tok.kind == "NAME" and tok.value == "import":
                self._next()  # import
                self._next()  # name
                continue
            if tok.kind == "NAME" and tok.value == "section":
                objects.extend(self._parse_section())
                continue
            if tok.kind == "NAME":
                objects.append(self._parse_object())
                continue
            # Unknown token - skip defensively.
            self._next()
        return objects

    def _parse_section(self) -> list[dict[str, Any]]:
        self._next()  # section keyword
        self._next()  # section title (string)
        self._expect("LBRACE")
        objects: list[dict[str, Any]] = []
        while True:
            tok = self._peek()
            if tok is None:
                raise ValueError("Unterminated section")
            if tok.kind == "RBRACE":
                self._next()
                break
            if tok.kind == "NAME" and tok.value == "section":
                objects.extend(self._parse_section())
                continue
            if tok.kind == "NAME":
                objects.append(self._parse_object())
                continue
            self._next()
        return objects

    def _parse_object(self) -> dict[str, Any]:
        type_tok = self._next()  # qualified type, e.g. ScoreReq.AoU
        name_tok = self._next()  # object identifier
        if name_tok.kind != "NAME":
            raise ValueError(f"Expected object name, got {name_tok}")
        self._expect("LBRACE")
        fields: dict[str, Any] = {}
        while True:
            tok = self._peek()
            if tok is None:
                raise ValueError("Unterminated object")
            if tok.kind == "RBRACE":
                self._next()
                break
            field_tok = self._next()
            if field_tok.kind != "NAME":
                raise ValueError(f"Expected field name, got {field_tok}")
            self._expect("EQUALS")
            fields[field_tok.value] = self._parse_value()
        return {
            "type": _short_type(type_tok.value),
            "id": name_tok.value,
            "fields": fields,
        }

    def _parse_value(self) -> Any:
        tok = self._next()
        if tok.kind == "STRING":
            return _dedent(tok.value)
        if tok.kind == "INT":
            return int(tok.value)
        if tok.kind == "NAME":
            return tok.value
        if tok.kind == "LBRACKET":
            return self._parse_list()
        raise ValueError(f"Unexpected value token {tok}")

    def _parse_list(self) -> list[Any]:
        items: list[Any] = []
        while True:
            tok = self._peek()
            if tok is None:
                raise ValueError("Unterminated list")
            if tok.kind == "RBRACKET":
                self._next()
                break
            if tok.kind == "COMMA":
                self._next()
                continue
            item = self._next()
            value = item.value
            # Preserve an optional "@ <version>" suffix on references so links
            # can later be rendered with a version constraint.
            nxt = self._peek()
            if nxt is not None and nxt.kind == "AT":
                self._next()  # @
                version = self._next()  # version int
                value = f"{value}@{version.value}"
            items.append(value)
        return items

    def _expect(self, kind: str) -> _Token:
        tok = self._next()
        if tok.kind != kind:
            raise ValueError(f"Expected {kind}, got {tok}")
        return tok


def _short_type(qualified: str) -> str:
    """Return the last segment of a (possibly qualified) type name."""
    return qualified.rsplit(".", 1)[-1]


def _dedent(text: str) -> str:
    """Strip the surrounding blank lines/indentation of a block literal."""
    if "\n" not in text:
        return text.strip()
    lines = text.splitlines()
    # Drop leading/trailing empty lines kept from the triple-quote layout.
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    indents = [len(ln) - len(ln.lstrip()) for ln in lines if ln.strip()]
    common = min(indents) if indents else 0
    return "\n".join(ln[common:] if len(ln) >= common else ln for ln in lines)


# -----------------------------------------------------------------------------
# Conversion
# -----------------------------------------------------------------------------


def _title_from_id(need_id: str) -> str:
    """Derive a human readable title from a requirement identifier."""
    segment = need_id.split("__")[-1]
    words = re.split(r"[_\s]+", segment.strip())
    title = " ".join(word.capitalize() for word in words if word)
    return title or need_id


def _safety(value: Any) -> str:
    """Map a ScoreReq.Asil enum literal to a sphinx-needs ``safety`` value."""
    literal = _short_type(str(value or "")) if value else ""
    return _ASIL_MAP.get(literal.upper(), "QM")


def _link_ref(raw: str) -> str:
    """Render a TRLC reference as a sphinx-needs link with a version constraint.

    A reference like ``SampleSEooC.FEAT_001@1`` becomes ``FEAT_001[version==1]``:
    the package qualifier is dropped (sphinx-needs ids are flat) and the
    ``@<version>`` suffix is turned into the ``[version==N]`` constraint
    understood by the S-CORE metamodel.
    """
    ref = str(raw)
    version = ""
    if "@" in ref:
        ref, _, version = ref.partition("@")
        version = version.strip()
    target = _short_type(ref.strip())
    if version:
        return f"{target}[version=={version}]"
    return target


def _to_need(obj: dict[str, Any]) -> dict[str, Any] | None:
    """Convert one parsed TRLC object into a sphinx-needs element."""
    score_type = obj["type"]
    need_type = _TYPE_MAP.get(score_type)
    if need_type is None:
        return None

    fields = obj["fields"]
    need_id = str(obj["id"])
    content = str(fields.get("description", "")).strip()

    need: dict[str, Any] = {
        "id": need_id,
        "type": need_type,
        "type_name": _TYPE_NAME.get(need_type, need_type),
        "title": _title_from_id(need_id),
        "content": content,
        "status": _short_type(str(fields.get("status", "valid"))) or "valid",
        "safety": _safety(fields.get("safety")),
        "security": "NO",
        "reqtype": "Functional",
        "version": str(fields.get("version", 1)),
        "tags": ["requirement"],
    }

    note = fields.get("note")
    if note:
        need["note"] = str(note).strip()

    rationale = fields.get("rationale")
    if rationale:
        need["rationale"] = str(rationale).strip()

    derived_from = fields.get("derived_from")
    if isinstance(derived_from, list) and derived_from:
        need["derived_from"] = [_link_ref(ref) for ref in derived_from]

    mitigates = fields.get("mitigates")
    if mitigates:
        need["mitigates"] = str(mitigates).strip()

    return need


def convert(texts: list[str], project: str) -> dict[str, Any]:
    """Convert one or more TRLC source strings into a ``needs.json`` document."""
    objects: list[dict[str, Any]] = []
    for text in texts:
        objects.extend(_Parser(_tokenize(text)).parse())

    needs: dict[str, Any] = {}
    for obj in objects:
        need = _to_need(obj)
        if need is not None:
            needs[need["id"]] = need

    created = datetime.now(UTC).isoformat()
    version = "1.0"
    return {
        "created": created,
        "current_version": version,
        "project": project,
        "versions": {
            version: {
                "created": created,
                "creator": {"program": "trlc_to_sphinx_needs"},
                "needs_amount": len(needs),
                "needs": needs,
            }
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Convert TRLC requirements written against the S-CORE requirements "
            "metamodel (ScoreReq) into a sphinx-needs needs.json file."
        ),
    )
    _ = parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path of the needs.json file to write.",
    )
    _ = parser.add_argument(
        "--project",
        default="Needs",
        help="Project name recorded in the generated needs.json.",
    )
    _ = parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Input TRLC (.trlc) files to convert.",
    )

    args = parser.parse_args()

    texts: list[str] = []
    for path in args.inputs:
        with open(path) as f:
            texts.append(f.read())

    data = convert(texts, project=args.project)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        _ = f.write("\n")

    converted = data["versions"]["1.0"]["needs_amount"]
    logger.info(
        "Converted %d file(s) -> '%s' (%d requirements, project '%s')",
        len(args.inputs),
        args.output,
        converted,
        args.project,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
