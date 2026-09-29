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
"""Generate JSON Schema from metamodel.yaml for AI agent consumption.

This script reads the S-CORE metamodel YAML and produces a JSON Schema that
describes the structure and validation rules for the metamodel. This schema
can be used by AI agents and other tools to understand and validate metamodel
instances.

Usage:
    generate_schema.py --output FILE [METAMODEL_YAML]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import ruamel.yaml


def load_metamodel_yaml(path: Path) -> Mapping[str, Any]:
    """Load a metamodel YAML file."""
    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    with path.open(encoding="utf-8") as fh:
        loaded = yaml.load(fh)
    return cast(Mapping[str, Any], loaded if isinstance(loaded, Mapping) else {})


def _as_mapping(value: Any) -> Mapping[str, Any]:
    """Return value as a mapping or empty mapping for missing sections."""
    if isinstance(value, Mapping):
        return cast(Mapping[str, Any], value)
    return {}


def _as_string_mapping(value: Any) -> dict[str, str]:
    """Convert a YAML mapping into a string mapping."""
    mapping = cast(Mapping[object, object], _as_mapping(value))
    return {str(key): str(item) for key, item in mapping.items()}


def _as_string_list(value: Any) -> list[str]:
    """Convert a YAML sequence into a list of strings."""
    from collections.abc import Sequence
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        sequence = cast(Sequence[object], value)
        return [str(item) for item in sequence]
    return []


def _build_base_options_schema(data: Mapping[str, Any]) -> dict[str, Any]:
    """Build JSON Schema for base options."""
    base = _as_mapping(data.get("needs_types_base_options"))
    
    schema = {
        "type": "object",
        "description": "Base options inherited by all need types",
        "properties": {
            "mandatory": {
                "type": "object",
                "description": "Mandatory options for all need types",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "pattern": {"type": "string", "format": "regex"}
                    },
                    "required": ["name", "pattern"]
                }
            },
            "optional": {
                "type": "object",
                "description": "Optional options for all need types",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "pattern": {"type": "string", "format": "regex"}
                    },
                    "required": ["name", "pattern"]
                }
            }
        }
    }
    
    return schema


def _build_need_type_schema(type_name: str, type_data: Mapping[str, Any]) -> dict[str, Any]:
    """Build JSON Schema for a single need type."""
    schema = {
        "type": "object",
        "description": f"Definition of {type_name} need type",
        "properties": {
            "title": {"type": "string"},
            "prefix": {"type": "string"},
            "color": {"type": "string"},
            "style": {"type": "string"},
            "tags": {
                "type": "array",
                "items": {"type": "string"}
            },
            "parts": {"type": "integer"},
            "mandatory_options": {
                "type": "object",
                "description": "Mandatory field patterns for this type",
                "additionalProperties": {"type": "string", "format": "regex"}
            },
            "optional_options": {
                "type": "object",
                "description": "Optional field patterns for this type",
                "additionalProperties": {"type": "string", "format": "regex"}
            },
            "mandatory_links": {
                "type": "object",
                "description": "Mandatory link patterns for this type",
                "additionalProperties": {"type": "string"}
            },
            "optional_links": {
                "type": "object",
                "description": "Optional link patterns for this type",
                "additionalProperties": {"type": "string"}
            }
        },
        "required": ["title"]
    }
    
    return schema


def _build_link_type_schema(link_name: str, link_data: Mapping[str, Any]) -> dict[str, Any]:
    """Build JSON Schema for a link type."""
    return {
        "type": "object",
        "description": f"Definition of {link_name} link type",
        "properties": {
            "outgoing": {"type": "string"},
            "incoming": {"type": "string"}
        },
        "required": ["outgoing", "incoming"]
    }


def _build_prohibited_words_schema(data: Mapping[str, Any]) -> dict[str, Any]:
    """Build JSON Schema for prohibited words checks."""
    checks = _as_mapping(data.get("prohibited_words_checks"))
    
    checks_schema = {}
    for check_name, check_data in checks.items():
        check_schema = {
            "type": "object",
            "description": f"Prohibited words check: {check_name}",
            "properties": {
                "types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tag types this check applies to"
                }
            }
        }
        
        # Add dynamic properties for each option being checked
        for option, words in _as_mapping(check_data).items():
            if option != "types":
                check_schema["properties"][option] = {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": f"Prohibited words for {option}"
                }
        
        checks_schema[check_name] = check_schema
    
    return {
        "type": "object",
        "description": "Prohibited words validation rules",
        "properties": checks_schema
    }


def _build_graph_rule_schema(rule_name: str, rule_data: Mapping[str, Any]) -> dict[str, Any]:
    """Build JSON Schema for a graph validation rule."""
    return {
        "type": "object",
        "description": f"Graph validation rule: {rule_name}",
        "properties": {
            "needs": {
                "type": "object",
                "properties": {
                    "include": {"type": "string"},
                    "condition": {"type": "object"}
                }
            },
            "check": {"type": "object"},
            "explanation": {"type": "string"}
        },
        "required": ["needs", "check"]
    }


def build_json_schema(data: Mapping[str, Any], digest: str) -> dict[str, Any]:
    """Build the complete JSON Schema from metamodel data."""
    
    # Build need types schema
    need_types = _as_mapping(data.get("needs_types"))
    need_types_properties = {}
    for type_name, type_data in need_types.items():
        need_types_properties[type_name] = _build_need_type_schema(type_name, _as_mapping(type_data))
    
    # Build link types schema
    link_types = _as_mapping(data.get("needs_extra_links"))
    link_types_properties = {}
    for link_name, link_data in link_types.items():
        link_types_properties[link_name] = _build_link_type_schema(link_name, _as_mapping(link_data))
    
    # Build graph rules schema
    graph_rules = _as_mapping(data.get("graph_checks"))
    graph_rules_properties = {}
    for rule_name, rule_data in graph_rules.items():
        graph_rules_properties[rule_name] = _build_graph_rule_schema(rule_name, _as_mapping(rule_data))
    
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://eclipse-score.github.io/schemas/metamodel-schema.json",
        "title": "S-CORE Metamodel Schema",
        "description": "JSON Schema for the S-CORE requirements metamodel",
        "type": "object",
        "properties": {
            "$schema": {
                "type": "string",
                "const": "https://json-schema.org/draft/2020-12/schema"
            },
            "metamodel_digest": {
                "type": "string",
                "pattern": "^sha256:[a-f0-9]{64}$",
                "description": "SHA256 digest of the source metamodel.yaml"
            },
            "schema_version": {
                "type": "integer",
                "const": 1,
                "description": "Schema version identifier"
            },
            "needs_types_base_options": _build_base_options_schema(data),
            "needs_types": {
                "type": "object",
                "description": "All Sphinx-Needs types (directives)",
                "properties": need_types_properties
            },
            "needs_extra_links": {
                "type": "object",
                "description": "All extra link definitions",
                "properties": link_types_properties
            },
            "prohibited_words_checks": _build_prohibited_words_schema(data),
            "graph_checks": {
                "type": "object",
                "description": "Graph validation rules",
                "properties": graph_rules_properties
            }
        },
        "required": ["$schema", "schema_version", "metamodel_digest"],
        "additionalProperties": False
    }
    
    return schema


def render_schema(schema: Mapping[str, Any]) -> str:
    """Serialize schema deterministically with a trailing newline."""
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


def resolve_metamodel_path(
    argument: Path | None,
    *,
    workspace: str | None = None,
) -> Path:
    """Resolve the metamodel input path for both direct and Bazel invocations."""
    default_relative = Path("src/extensions/score_metamodel/metamodel.yaml")
    if argument is None:
        packaged = Path(__file__).resolve().parents[2] / "metamodel.yaml"
        if packaged.is_file() or workspace is None:
            return packaged
        return Path(workspace) / default_relative
    if argument.is_absolute() or argument.is_file() or workspace is None:
        return argument
    return Path(workspace) / argument


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate JSON Schema from metamodel.yaml"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("metamodel", type=Path, nargs="?", default=None)
    args = parser.parse_args()
    
    meta_path = resolve_metamodel_path(
        args.metamodel,
        workspace=__file__ if "BUILD_WORKSPACE_DIRECTORY" not in __file__ else None,
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
    
    digest = hashlib.sha256(raw_bytes).hexdigest()
    schema = build_json_schema(data, f"sha256:{digest}")
    
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_schema(schema), encoding="utf-8")
    
    print(f"Generated JSON Schema at {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
