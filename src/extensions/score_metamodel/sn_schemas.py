"""Transforms the YAML metamodel into sphinx-needs JSON schema definitions.

Reads need types from the parsed metamodel (MetaModelData) and generates a
``schemas.json`` file that sphinx-needs uses to validate each need against
the S-CORE metamodel rules (required fields, regex patterns, link constraints).

Schema structure per need type (sphinx-needs schema format):
  - ``select``  : matches needs by their ``type`` field
  - ``validate.local``   : validates the need's own properties (patterns, required)
  - ``validate.network`` : validates properties of linked needs (NOT YET ACTIVE)
"""

import json
from pathlib import Path

from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx_needs import logging

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

    For every need type that has at least one constraint (mandatory/optional
    fields or links), a schema entry is created with:

    1. A **selector** that matches needs whose ``type`` equals the directive name.
    2. A **local validator** containing:
       - ``required`` list for mandatory fields/links.
       - ``properties`` with regex ``pattern`` constraints for field values.
       - ``minItems: 1`` for mandatory links (must have at least one target).
    3. A **network validator** (currently disabled) that would check that
       linked needs have the expected ``type``.

    The resulting JSON is written to ``<confdir>/schemas.json`` and registered
    with sphinx-needs via ``config.needs_schema_definitions_from_json``.
    """
    config: Config = app.config
    schemas = []
    schema_definitions = {"schemas": schemas}

    for need_type in metamodel.needs_types:
        # Extract the four constraint categories from the metamodel YAML
        mandatory_fields = need_type.get("mandatory_options", {})
        optional_fields = need_type.get("optional_options", {})
        mandatory_links = need_type.get("mandatory_links", {})
        optional_links = need_type.get("optional_links", {})

        # Skip need types that have no constraints at all
        if not (
            mandatory_fields or optional_fields or mandatory_links or optional_links
        ):
            continue

        # --- Classify link values as regex patterns vs. target type names ---
        # In the metamodel YAML, a link value can be either:
        #   - A regex (starts with "^"), e.g. "^logic_arc_int(_op)*__.+$"
        #     → validated locally (the link ID must match the pattern)
        #   - A plain type name, e.g. "comp"
        #     → validated via network (the linked need must have that type)
        # Multiple values are comma-separated, e.g. "comp, sw_unit"
        mandatory_links_regexes = {}
        mandatory_links_targets = {}
        optional_links_regexes = {}
        optional_links_targets = {}
        value: str
        field: str
        for field, value in mandatory_links.items():
            link_values = [v.strip() for v in value.split(",")]
            for link_value in link_values:
                if link_value.startswith("^"):
                    if field in mandatory_links_regexes:
                        LOGGER.error(
                            "Multiple regex patterns for mandatory link field "
                            f"'{field}' in need type '{type_name}'. "
                            "Only the first one will be used in the schema."
                        )
                    mandatory_links_regexes[field] = link_value
                else:
                    mandatory_links_targets[field] = link_value

        for field, value in optional_links.items():
            link_values = [v.strip() for v in value.split(",")]
            for link_value in link_values:
                if link_value.startswith("^"):
                    if field in optional_links_regexes:
                        LOGGER.error(
                            "Multiple regex patterns for optional link field "
                            f"'{field}' in need type '{type_name}'. "
                            "Only the first one will be used in the schema."
                        )
                    optional_links_regexes[field] = link_value
                else:
                    optional_links_targets[field] = link_value

        # --- Build the schema entry for this need type ---
        type_schema = {
            "id": f"need-type-{need_type['directive']}",
            "severity": "violation",
            "message": "Need does not conform to S-CORE metamodel",
        }
        type_name = need_type["directive"]

        # Selector: only apply this schema to needs with matching type
        selector = {
            "properties": {"type": {"const": type_name}},
            "required": ["type"],
        }
        type_schema["select"] = selector

        # --- Local validation (the need's own properties) ---
        type_schema["validate"] = {}
        validator_local = {
            "properties": {},
            "required": [],
            # "unevaluatedProperties": False,
        }

        # Mandatory fields: must be present AND match the regex pattern
        for field, pattern in mandatory_fields.items():
            if field in IGNORE_FIELDS:
                continue
            validator_local["required"].append(field)
            validator_local["properties"][field] = get_field_pattern_schema(
                field, pattern
            )

        # Optional fields: if present, must match the regex pattern
        for field, pattern in optional_fields.items():
            if field in IGNORE_FIELDS:
                continue
            validator_local["properties"][field] = get_field_pattern_schema(
                field, pattern
            )

        # Mandatory links (regex): must have at least one entry
        # TODO: regex pattern matching on link IDs is not yet enabled
        for field, pattern in mandatory_links_regexes.items():
            validator_local["properties"][field] = {
                "type": "array",
                "minItems": 1,
            }
            validator_local["required"].append(field)
            # validator_local["properties"][field] = get_array_pattern_schema(pattern)

        # Optional links (regex): allowed but not required
        # TODO: regex pattern matching on link IDs is not yet enabled
        for field, pattern in optional_links_regexes.items():
            validator_local["properties"][field] = {
                "type": "array",
            }
            # validator_local["properties"][field] = get_array_pattern_schema(pattern)

        type_schema["validate"]["local"] = validator_local

        # --- Network validation (properties of linked needs) ---
        # TODO: network validation is not yet enabled — the assignments to
        # validator_network are commented out below.
        validator_network = {}
        for field, target_type in mandatory_links_targets.items():
            link_validator = {
                "items": {
                    "local": {
                        "properties": {"type": {"type": "string", "const": target_type}}
                    }
                },
            }
            # validator_network[field] = link_validator
        for field, target_type in optional_links_targets.items():
            link_validator = {
                "items": {
                    "local": {
                        "properties": {"type": {"type": "string", "const": target_type}}
                    }
                },
            }
            # validator_network[field] = link_validator
        if validator_network:
            type_schema["validate"]["network"] = validator_network

        schemas.append(type_schema)

    # Write the complete schema definitions to a JSON file in confdir
    schemas_output_path = Path(app.confdir) / "schemas.json"
    with open(schemas_output_path, "w", encoding="utf-8") as f:
        json.dump(schema_definitions, f, indent=2, ensure_ascii=False)

    # Tell sphinx-needs to load the schema from the JSON file
    config.needs_schema_definitions_from_json = "schemas.json"
    # config.needs_schema_definitions = schema_definitions


def get_field_pattern_schema(field: str, pattern: str):
    """Return the appropriate JSON schema for a field's regex pattern.

    Array-valued fields (like ``tags``) get an array-of-strings schema;
    scalar fields get a plain string schema.
    """
    if field in SN_ARRAY_FIELDS:
        return get_array_pattern_schema(pattern)
    return get_pattern_schema(pattern)


def get_pattern_schema(pattern: str):
    """Return a JSON schema that validates a string against a regex pattern."""
    return {
        "type": "string",
        "pattern": pattern,
    }


def get_array_pattern_schema(pattern: str):
    """Return a JSON schema that validates an array where each item matches a regex."""
    return {
        "type": "array",
        "items": get_pattern_schema(pattern),
    }
