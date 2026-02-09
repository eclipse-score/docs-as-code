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
"""Transforms the YAML metamodel into sphinx-needs >6 JSON schema definitions.

Reads need types from the parsed metamodel (MetaModelData) and generates a
``schemas.json`` file that sphinx-needs uses to validate each need against
the S-CORE metamodel rules (required fields, regex patterns, link constraints).

Schema structure per need type (sphinx-needs schema format):
  - ``select``  : matches needs by their ``type`` field
  - ``validate.local``   : validates the need's own properties (patterns, required)
  - ``validate.network`` : validates properties of linked needs
"""

import json
from pathlib import Path
from typing import Any

from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx_needs import logging

from src.extensions.score_metamodel.metamodel_types import ScoreNeedType
from src.extensions.score_metamodel.yaml_parser import MetaModelData

# Fields whose values are lists in sphinx-needs (e.g. tags: ["safety", "security"]).
# These need an "array of strings" JSON schema instead of a plain "string" schema.
SN_ARRAY_FIELDS = {
    "tags",
    "sections",
}

# Fields to skip during schema generation.
IGNORE_FIELDS = {
    "content",  # not yet available in ubCode
}

LOGGER = logging.get_logger(__name__)


def write_sn_schemas(app: Sphinx, metamodel: MetaModelData) -> None:
    """Build sphinx-needs schema definitions from the metamodel and write to JSON.

    Iterates over all need types, builds a schema for each one via
    ``_build_need_type_schema``, and writes the result to
    ``<confdir>/schemas.json``.
    """
    config: Config = app.config
    schemas: list[dict[str, Any]] = []

    for need_type in metamodel.needs_types:
        schema = _build_need_type_schema(need_type)
        if schema is not None:
            schemas.append(schema)

    schema_definitions: dict[str, Any] = {"schemas": schemas}

    # Write the complete schema definitions to a JSON file in confdir
    schemas_output_path = Path(app.confdir) / "schemas.json"
    with open(schemas_output_path, "w", encoding="utf-8") as f:
        json.dump(schema_definitions, f, indent=2, ensure_ascii=False)

    # Tell sphinx-needs to load the schema from the JSON file
    config.needs_schema_definitions_from_json = "schemas.json"
    # config.needs_schema_definitions = schema_definitions


def _classify_links(
    links: dict[str, Any], type_name: str, mandatory: bool
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Classify link values into regex patterns vs. target type names.

    In the metamodel YAML, a link value can be either:
      - A regex (starts with "^"), e.g. "^logic_arc_int(_op)*__.+$"
        -> validated locally (the link ID must match the pattern)
      - A plain type name, e.g. "comp"
        -> validated via network (the linked need must have that type)
    Multiple values are comma-separated, e.g. "comp, sw_unit".

    Returns:
        A tuple of (regexes, targets) dicts, keyed by field name.
        ``targets`` maps each field to a list of all allowed type names.
    """
    label = "mandatory" if mandatory else "optional"
    regexes: dict[str, str] = {}
    targets: dict[str, list[str]] = {}

    for field, value in links.items():
        link_values = [v.strip() for v in value.split(",")]
        for link_value in link_values:
            if link_value.startswith("^"):
                if field in regexes:
                    LOGGER.error(
                        f"Multiple regex patterns for {label} link field "
                        f"'{field}' in need type '{type_name}'. "
                        "Only the first one will be used in the schema."
                    )
                regexes[field] = link_value
            else:
                if field not in targets:
                    targets[field] = []
                targets[field].append(link_value)

    return regexes, targets


def _build_local_validator(
    mandatory_fields: dict[str, str],
    optional_fields: dict[str, str],
    mandatory_links_regexes: dict[str, str],
    optional_links_regexes: dict[str, str],
    mandatory_links_targets: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Build the local validator dict for a need type's schema.

    The local validator checks the need's own properties:
      - Mandatory fields must be present and match their regex pattern.
      - Optional fields, if present, must match their regex pattern.
      - Mandatory links must have at least one entry.
    """
    properties: dict[str, Any] = {}
    required: list[str] = []

    # Mandatory fields: must be present AND match the regex pattern
    for field, pattern in mandatory_fields.items():
        if field in IGNORE_FIELDS:
            continue
        required.append(field)
        properties[field] = get_field_pattern_schema(field, pattern)

    # Optional fields: if present, must match the regex pattern
    for field, pattern in optional_fields.items():
        if field in IGNORE_FIELDS:
            continue
        properties[field] = get_field_pattern_schema(field, pattern)

    # Mandatory links (regex): must have at least one entry
    # TODO: regex pattern matching on link IDs is not yet enabled
    for field in mandatory_links_regexes:
        properties[field] = {"type": "array", "minItems": 1}
        required.append(field)

    # Mandatory links (plain target types): must have at least one entry.
    # The type of the linked need is checked via validate.network, but the
    # list length constraint belongs in the local validator.
    # Skip fields already handled by mandatory_links_regexes (mixed regex + plain).
    for field in mandatory_links_targets or {}:
        if field not in properties:
            properties[field] = {"type": "array", "minItems": 1}
            required.append(field)

    # Optional links (regex): allowed but not required
    # TODO: regex pattern matching on link IDs is not yet enabled
    for field in optional_links_regexes:
        properties[field] = {"type": "array"}

    return {
        "properties": properties,
        "required": required,
        # "unevaluatedProperties": False,
    }


def _build_need_type_schema(need_type: ScoreNeedType) -> dict[str, Any] | None:
    """Build a sphinx-needs schema entry for a single need type.

    Returns ``None`` if the need type has no constraints (no mandatory/optional
    fields or links), meaning no schema validation is needed.

    The returned dict has the sphinx-needs schema structure:
      - ``select``: matches needs by their ``type`` field
      - ``validate.local``: validates the need's own properties
      - ``validate.network``: validates linked needs' types
    """
    mandatory_fields = need_type.get("mandatory_options", {})
    optional_fields = need_type.get("optional_options", {})
    mandatory_links = need_type.get("mandatory_links", {})
    optional_links = need_type.get("optional_links", {})

    # Skip need types that have no constraints at all
    if not (mandatory_fields or optional_fields or mandatory_links or optional_links):
        return None

    type_name = need_type["directive"]

    # Classify link values as regex patterns vs. target type names.
    # Note: links are still plain strings at this point (before postprocess_need_links).
    mandatory_links_regexes, mandatory_links_targets = _classify_links(
        mandatory_links, type_name, mandatory=True
    )
    optional_links_regexes, _ = _classify_links(
        optional_links, type_name, mandatory=False
    )

    # Build validate.network for link fields with plain type targets.
    # The network schema uses sphinx-needs' ValidateSchemaType format:
    # each entry's ``items.local`` is a JSON Schema applied to each linked need.
    network: dict[str, Any] = {}

    def add_network_entry(field: str, target_types: list[str]) -> None:
        type_constraint: dict[str, Any] = (
            {"enum": target_types}
            if len(target_types) > 1
            else {"const": target_types[0]}
        )
        network[field] = {
            "type": "array",
            "items": {
                "local": {
                    "properties": {"type": type_constraint},
                    "required": ["type"],
                }
            },
        }

    # Only add network entries for *mandatory* links with exclusively plain
    # type targets.  Two categories are intentionally excluded:
    #
    # 1. Mixed regex+plain fields (e.g. "complies: std_wp, ^std_req__aspice_40__iic.*$"):
    #    The items schema would incorrectly require ALL linked needs to match
    #    the plain type, while some legitimately match the regex instead.
    #
    # 2. Optional links: The Python validate_links() in check_options.py treats
    #    optional link type violations as informational (treat_as_info=True),
    #    but schemas use a single severity ("violation") per need type.
    #    Including optional links would escalate info-level issues to errors.
    #    Optional link types are validated by the Python check instead.
    for field, target_types in mandatory_links_targets.items():
        if field not in mandatory_links_regexes:
            add_network_entry(field, target_types)

    type_schema: dict[str, Any] = {
        "id": f"need-type-{type_name}",
        "severity": "violation",
        "message": "Need does not conform to S-CORE metamodel",
        # Selector: only apply this schema to needs with matching type
        "select": {
            "properties": {"type": {"const": type_name}},
            "required": ["type"],
        },
        "validate": {
            "local": _build_local_validator(
                mandatory_fields,
                optional_fields,
                mandatory_links_regexes,
                optional_links_regexes,
                mandatory_links_targets,
            ),
        },
    }
    if network:
        type_schema["validate"]["network"] = network

    return type_schema


def get_field_pattern_schema(field: str, pattern: str) -> dict[str, Any]:
    """Return the appropriate JSON schema for a field's regex pattern.

    Array-valued fields (like ``tags``) get an array-of-strings schema;
    scalar fields get a plain string schema.
    """
    if field in SN_ARRAY_FIELDS:
        return get_array_pattern_schema(pattern)
    return get_pattern_schema(pattern)


def get_pattern_schema(pattern: str) -> dict[str, str]:
    """Return a JSON schema that validates a string against a regex pattern."""
    return {
        "type": "string",
        "pattern": pattern,
    }


def get_array_pattern_schema(pattern: str) -> dict[str, Any]:
    """Return a JSON schema that validates an array where each item matches a regex."""
    return {
        "type": "array",
        "items": get_pattern_schema(pattern),
    }
