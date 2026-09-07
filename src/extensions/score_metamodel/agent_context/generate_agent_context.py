#!/usr/bin/env python3
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
"""Generate a vendor-neutral JSON projection of the S-CORE metamodel.

The projection contains the metamodel vocabulary and raw graph-check data
needed by downstream agent-context renderers.  It deliberately does not
evaluate or otherwise interpret graph-check expressions.

Usage:
    generate_agent_context.py --output FILE [METAMODEL_YAML]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import ruamel.yaml


def load_metamodel_yaml(path: Path) -> Mapping[str, Any]:
    """Load a metamodel YAML file, defaulting malformed roots to empty data."""
    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    with path.open(encoding="utf-8") as fh:
        loaded = yaml.load(fh)
    return cast(Mapping[str, Any], loaded if isinstance(loaded, Mapping) else {})


def _as_mapping(value: Any) -> Mapping[str, Any]:
    """Return *value* as a mapping or an empty mapping for missing sections."""
    if isinstance(value, Mapping):
        return cast(Mapping[str, Any], value)
    return {}


def _as_string_mapping(value: Any) -> dict[str, str]:
    """Convert a YAML mapping into a string mapping."""
    mapping = cast(Mapping[object, object], _as_mapping(value))
    return {str(key): str(item) for key, item in mapping.items()}


def _as_string_list(value: Any) -> list[str]:
    """Convert a YAML sequence into a list of strings."""
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        sequence = cast(Sequence[object], value)
        return [str(item) for item in sequence]
    return []


def _split_targets(targets: Any) -> tuple[list[str], bool]:
    """Split comma-separated targets and preserve the ``ANY`` wildcard."""
    target_text = str(targets)
    if target_text == "ANY":
        return [], True
    return (
        [target.strip() for target in target_text.split(",") if target.strip()],
        False,
    )


def _to_plain(value: Any) -> Any:
    """Copy YAML containers into ordinary JSON-compatible containers."""
    if isinstance(value, Mapping):
        mapping = cast(Mapping[object, Any], value)
        return {str(key): _to_plain(item) for key, item in mapping.items()}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        sequence = cast(Sequence[Any], value)
        return [_to_plain(item) for item in sequence]
    return value


def _base_options(data: Mapping[str, Any]) -> dict[str, list[dict[str, str]]]:
    base = _as_mapping(data.get("needs_types_base_options"))
    result: dict[str, list[dict[str, str]]] = {}
    for output_name, source_name in (
        ("mandatory", "mandatory_options"),
        ("optional", "optional_options"),
    ):
        result[output_name] = [
            {"name": name, "pattern": pattern}
            for name, pattern in sorted(
                _as_string_mapping(base.get(source_name)).items()
            )
        ]
    return result


def _type_options(
    raw_type: Mapping[str, Any],
    base: Mapping[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    options: dict[str, dict[str, Any]] = {}
    for required, section in (
        (True, "mandatory"),
        (False, "optional"),
    ):
        for item in base.get(section, []):
            options[item["name"]] = {
                "name": item["name"],
                "pattern": item["pattern"],
                "required": required,
                "inherited": True,
            }

    # Type-level options override inherited options, including their required
    # status.  Mandatory options are applied last if a malformed type repeats a
    # name in both type-level sections.
    for required, source_name in (
        (False, "optional_options"),
        (True, "mandatory_options"),
    ):
        for name, pattern in sorted(
            _as_string_mapping(raw_type.get(source_name)).items()
        ):
            options[name] = {
                "name": name,
                "pattern": pattern,
                "required": required,
                "inherited": False,
            }
    return [options[name] for name in sorted(options)]


def _type_links(raw_type: Mapping[str, Any]) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    for required, source_name in (
        (True, "mandatory_links"),
        (False, "optional_links"),
    ):
        for name, raw_targets in sorted(
            _as_string_mapping(raw_type.get(source_name)).items()
        ):
            targets, any_target = _split_targets(raw_targets)
            links.append(
                {
                    "name": name,
                    "targets": targets,
                    "any_target": any_target,
                    "required": required,
                }
            )
    return sorted(links, key=lambda item: item["name"])


def _need_types(
    data: Mapping[str, Any],
    base: Mapping[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    raw_types = _as_mapping(data.get("needs_types"))
    result: list[dict[str, Any]] = []
    for name, raw_value in sorted(raw_types.items(), key=lambda item: str(item[0])):
        raw_type = _as_mapping(raw_value)
        result.append(
            {
                "name": str(name),
                "title": raw_type.get("title"),
                "prefix": raw_type.get("prefix"),
                "tags": _as_string_list(raw_type.get("tags")),
                "parts": raw_type.get("parts"),
                "options": _type_options(raw_type, base),
                "links": _type_links(raw_type),
            }
        )
    return result


def _prohibited_words(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    checks = _as_mapping(data.get("prohibited_words_checks"))
    for check, raw_value in checks.items():
        raw_check = _as_mapping(raw_value)
        applies_to_tags = _as_string_list(raw_check.get("types"))
        for option, words in raw_check.items():
            if option == "types":
                continue
            result.append(
                {
                    "check": str(check),
                    "option": str(option),
                    "applies_to_tags": applies_to_tags,
                    "words": _as_string_list(words),
                }
            )
    return sorted(result, key=lambda item: (item["check"], item["option"]))


def _link_types(data: Mapping[str, Any]) -> list[dict[str, str | bool | None]]:
    declared = _as_mapping(data.get("needs_extra_links"))
    result: dict[str, dict[str, str | bool | None]] = {}
    for name, raw_value in declared.items():
        raw_link = _as_mapping(raw_value)
        link_name = str(name)
        result[link_name] = {
            "name": link_name,
            "outgoing": (str(raw_link["outgoing"]) if "outgoing" in raw_link else None),
            "incoming": (str(raw_link["incoming"]) if "incoming" in raw_link else None),
            "declared": True,
        }

    # ``links`` is a built-in Sphinx-Needs wildcard used by the metamodel but
    # is not declared in ``needs_extra_links``.  Retain it in the projection,
    # marked as undeclared, so consumers can distinguish it from a declaration.
    for raw_type in _as_mapping(data.get("needs_types")).values():
        for section in ("mandatory_links", "optional_links"):
            for name in _as_mapping(raw_type).get(section, {}):
                link_name = str(name)
                result.setdefault(
                    link_name,
                    {
                        "name": link_name,
                        "outgoing": None,
                        "incoming": None,
                        "declared": False,
                    },
                )
    return sorted(result.values(), key=lambda item: item["name"] or "")


def _graph_rules(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for name, raw_value in _as_mapping(data.get("graph_checks")).items():
        raw_rule = _as_mapping(raw_value)
        raw_needs = _as_mapping(raw_rule.get("needs"))
        result.append(
            {
                "name": str(name),
                "applies_to": _split_targets(raw_needs.get("include", ""))[0],
                "condition_raw": _to_plain(raw_needs.get("condition")),
                "check_raw": _to_plain(raw_rule.get("check")),
                "explanation": raw_rule.get("explanation"),
            }
        )
    return sorted(result, key=lambda item: item["name"])


def build_projection(data: Mapping[str, Any], digest: str) -> dict[str, Any]:
    """Build the ordered JSON projection from parsed YAML and its digest."""
    base = _base_options(data)
    return {
        "schema_version": 1,
        "metamodel_digest": f"sha256:{digest}",
        "base_options": base,
        "prohibited_words": _prohibited_words(data),
        "link_types": _link_types(data),
        "need_types": _need_types(data, base),
        "graph_rules": _graph_rules(data),
    }


def render_projection(projection: Mapping[str, Any]) -> str:
    """Serialize a projection deterministically with a trailing newline."""
    return json.dumps(projection, indent=2, ensure_ascii=False) + "\n"


def resolve_metamodel_path(
    argument: Path | None,
    *,
    workspace: str | None = None,
) -> Path:
    """Resolve the metamodel input path for both direct and Bazel invocations.

    ``bazel run`` executes inside the runfiles tree, so a relative argument is
    resolved against the workspace directory Bazel exports.  Without an
    argument the metamodel packaged next to this generator is used, which
    covers runfiles as well as source-tree execution.
    """
    default_relative = Path("src/extensions/score_metamodel/metamodel.yaml")
    if argument is None:
        packaged = Path(__file__).resolve().parents[1] / "metamodel.yaml"
        if packaged.is_file() or workspace is None:
            return packaged
        return Path(workspace) / default_relative
    if argument.is_absolute() or argument.is_file() or workspace is None:
        return argument
    return Path(workspace) / argument


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate JSON agent context from metamodel.yaml"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("metamodel", type=Path, nargs="?", default=None)
    return parser


def main() -> int:
    args = _argument_parser().parse_args()
    meta_path = resolve_metamodel_path(
        args.metamodel,
        workspace=os.environ.get("BUILD_WORKSPACE_DIRECTORY"),
    )
    if not meta_path.is_file():
        print(f"Error: metamodel.yaml not found at {meta_path}", file=sys.stderr)
        return 1

    raw_bytes = meta_path.read_bytes()
    try:
        data = load_metamodel_yaml(meta_path)
    except Exception as exc:
        print(f"Error parsing YAML: {exc}", file=sys.stderr)
        return 1

    projection = build_projection(
        data,
        hashlib.sha256(raw_bytes).hexdigest(),
    )
    args.output.write_text(render_projection(projection), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
