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
Convert the requirement sphinx-needs elements of a needs.json file into TRLC.

TRLC ("Treat Requirements Like Code", https://github.com/bmw-software-engineering/trlc)
is a requirements-only tooling. Therefore only the S-CORE requirement element
types are converted:

* ``feat_req`` -> ``ScoreReq.FeatReq`` (feature requirement)
* ``comp_req`` -> ``ScoreReq.CompReq`` (component requirement)
* ``aou_req``  -> ``ScoreReq.AoU``     (assumption of use)

All other sphinx-needs elements are ignored.

The generated ``.trlc`` data file targets the S-CORE requirements metamodel
(package ``ScoreReq``) defined in
https://github.com/eclipse-score/tooling/tree/main/bazel/rules/rules_score/trlc
and must be validated together with that metamodel.
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# sphinx-needs type -> ScoreReq metamodel type.
_TYPE_MAP: dict[str, str] = {
    "feat_req": "FeatReq",
    "comp_req": "CompReq",
    "aou_req": "AoU",
}

# ScoreReq type -> the metamodel type its ``derived_from`` references, if any.
# Only references that resolve to an emitted object of this type are rendered.
_DERIVED_FROM_TARGET: dict[str, str] = {
    "FeatReq": "AssumedSystemReq",
    "CompReq": "FeatReq",
}


def _string_literal(value: str) -> str:
    """Return a TRLC string literal for ``value``."""
    text = str(value)
    if "\n" in text:
        if '"""' not in text:
            return f'"""\n{text}\n"""'
        if "'''" not in text:
            return f"'''\n{text}\n'''"
        return '"""\n{text}\n"""'.format(text=text.replace('"""', '\\"\\"\\"'))
    return '"{text}"'.format(text=text.replace('"', '\\"'))


def _asil(value: object) -> str:
    """Map a sphinx-needs safety value to a ScoreReq.Asil enum literal."""
    text = str(value or "").upper().replace("ASIL", "").strip(" _-")
    if text == "B":
        return "ScoreReq.Asil.B"
    if text == "D":
        return "ScoreReq.Asil.D"
    return "ScoreReq.Asil.QM"


def _version(need: dict[str, Any]) -> int:
    """Return the integer version of a need, defaulting to 1."""
    try:
        return int(need.get("version", 1))
    except (TypeError, ValueError):
        return 1


def _identifier(raw: str, used: set[str]) -> str:
    """Turn an arbitrary need id into a unique, valid TRLC identifier."""
    candidate = re.sub(r"[^A-Za-z0-9_]", "_", str(raw))
    if not candidate or not (candidate[0].isalpha() or candidate[0] == "_"):
        candidate = "n_" + candidate
    unique = candidate
    suffix = 2
    while unique in used:
        unique = f"{candidate}_{suffix}"
        suffix += 1
    used.add(unique)
    return unique


def _collect_requirement_needs(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return all needs whose type maps to a ScoreReq requirement, sorted."""
    needs: list[dict[str, Any]] = []
    for version in data.get("versions", {}).values():
        for need in version.get("needs", {}).values():
            if need.get("type") in _TYPE_MAP:
                needs.append(need)
    needs.sort(key=lambda n: (str(n.get("type", "")), str(n.get("id", ""))))
    return needs


def _build_id_map(needs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Map original need id -> {ident, score_type, version} for every need."""
    id_map: dict[str, dict[str, Any]] = {}
    used: set[str] = set()
    for need in needs:
        original = str(need.get("id", "need"))
        id_map[original] = {
            "ident": _identifier(original, used),
            "score_type": _TYPE_MAP[need["type"]],
            "version": _version(need),
        }
    return id_map


def _render_object(need: dict[str, Any], id_map: dict[str, dict[str, Any]]) -> str:
    """Render a single requirement need as a ScoreReq object."""
    info = id_map[str(need.get("id"))]
    score_type = info["score_type"]
    description = str(need.get("content") or need.get("title") or info["ident"])

    lines = [
        "ScoreReq.{score_type} {ident} {{".format(
            score_type=score_type, ident=info["ident"]
        ),
        f"    description = {_string_literal(description)}",
        f"    version     = {_version(need)}",
        "    safety      = {value}".format(value=_asil(need.get("safety"))),
    ]

    target_type = _DERIVED_FROM_TARGET.get(score_type)
    if target_type:
        refs: list[str] = []
        for ref in need.get("derived_from") or []:  # pyright: ignore[reportUnknownVariableType]
            ref_info = id_map.get(str(ref))
            if ref_info and ref_info["score_type"] == target_type:
                refs.append(
                    "{ident} @ {version}".format(
                        ident=ref_info["ident"], version=ref_info["version"]
                    )
                )
        if refs:
            lines.append("    derived_from = [{refs}]".format(refs=", ".join(refs)))

    lines.append("}")
    return "\n".join(lines)


def render_trlc(data: dict[str, Any], package: str) -> str:
    """Render the requirements data file (``.trlc``)."""
    needs = _collect_requirement_needs(data)
    id_map = _build_id_map(needs)

    blocks = [
        f"package {package}",
        "",
        "import ScoreReq",
    ]

    body: list[str] = []
    current_type = None
    section_open = False
    for need in needs:
        type_ = str(need.get("type"))
        if type_ != current_type:
            if section_open:
                body.append("}")
            current_type = type_
            body.append("")
            body.append(f"section {_string_literal(type_)} {{")
            section_open = True
        obj = _render_object(need, id_map)
        body.append("\n".join("    " + line for line in obj.splitlines()))
    if section_open:
        body.append("}")

    blocks.append("\n".join(body))
    return "\n".join(blocks).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Convert the requirement sphinx-needs elements of a needs.json file "
            "into TRLC targeting the S-CORE requirements metamodel (ScoreReq)."
        ),
    )
    _ = parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path of the TRLC data file (.trlc) to write.",
    )
    _ = parser.add_argument(
        "--package",
        default="Needs",
        help="TRLC package name used for the generated requirements.",
    )
    _ = parser.add_argument(
        "input",
        type=Path,
        help="Input needs.json file to convert.",
    )

    args = parser.parse_args()

    package = re.sub(r"[^A-Za-z0-9_]", "_", args.package)
    if not package or not (package[0].isalpha() or package[0] == "_"):
        package = "Needs"

    with open(args.input) as f:
        data = json.load(f)

    objects = render_trlc(data, package=package)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        _ = f.write(objects)

    converted = len(_collect_requirement_needs(data))
    logger.info(
        "Converted '%s' -> '%s' (%d requirements, package '%s')",
        args.input,
        args.output,
        converted,
        package,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
