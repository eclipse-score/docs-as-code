# *******************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
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
"""Functionality related to reading in the SCORE metamodel.yaml"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from ruamel.yaml import YAML
from sphinx_needs import logging

from src.extensions.score_metamodel.metamodel_types import (
    ProhibitedWordCheck,
    ScoreNeedType,
)

logger = logging.get_logger(__name__)


@dataclass
class MetaModelData:
    needs_types: list[ScoreNeedType]
    needs_extra_links: list[dict[str, str]]
    needs_extra_options: list[str]
    prohibited_words_checks: list[ProhibitedWordCheck]
    needs_graph_check: dict[str, object]


def _parse_prohibited_words(
    checks_dict: dict[str, dict[str, Any]],
) -> list[ProhibitedWordCheck]:
    return [
        ProhibitedWordCheck(
            name=check_name,
            option_check={k: v for k, v in check_config.items() if k != "types"},
            types=check_config.get("types", []),
        )
        for check_name, check_config in checks_dict.items()
    ]


def default_options():
    """
    Helper function to get a list of all default options defined by
    sphinx, sphinx-needs etc.
    """
    return {
        "target_id",
        "id",
        "status",
        "docname",
        "lineno",
        "type",
        "lineno_content",
        "doctype",
        "content",
        "type_name",
        "type_color",
        "type_style",
        "title",
        "full_title",
        "layout",
        "template",
        "id_parent",
        "id_complete",
        "external_css",
        "sections",
        "section_name",
        "type_prefix",
        "constraints_passed",
        "collapse",
        "hide",
        "delete",
        "jinja_content",
        "is_part",
        "is_need",
        "is_external",
        "is_modified",
        "modifications",
        "has_dead_links",
        "has_forbidden_dead_links",
        "tags",
        "arch",
        "parts",
        # Introduced with sphinx-needs 6.3.0
        "is_import",
        "constraints",
    }


def _parse_need_type(
    directive_name: str,
    yaml_data: dict[str, Any],
    global_base_opts: dict[str, Any],
):
    """Build a single ScoreNeedType dict from the metamodel entry, incl defaults."""
    t: ScoreNeedType = {
        "directive": directive_name,
        "title": yaml_data["title"],
        "prefix": yaml_data.get("prefix", f"{directive_name}__"),
        "tags": yaml_data.get("tags", []),
        "parts": yaml_data.get("parts", 3),
        "mandatory_options": yaml_data.get("mandatory_options", {}),
        "optional_options": yaml_data.get("optional_options", {}) | global_base_opts,
        "mandatory_links": yaml_data.get("mandatory_links", {}),
        "optional_links": yaml_data.get("optional_links", {}),
    }

    # Ensure ID regex is set
    if "id" not in t["mandatory_options"]:
        prefix = t["prefix"]
        t["mandatory_options"]["id"] = f"^{prefix}[0-9a-zA-Z_]+$"

    if "color" in yaml_data:
        t["color"] = yaml_data["color"]
    if "style" in yaml_data:
        t["style"] = yaml_data["style"]

    return t


def _parse_needs_types(
    types_dict: dict[str, Any],
    global_base_options_optional_opts: dict[str, Any],
) -> dict[str, ScoreNeedType]:
    """Parse the 'needs_types' section of the metamodel.yaml."""

    needs_types: dict[str, ScoreNeedType] = {}
    for directive_name, directive_data in types_dict.items():
        assert isinstance(directive_name, str)
        assert isinstance(directive_data, dict)

        needs_types[directive_name] = _parse_need_type(
            directive_name, directive_data, global_base_options_optional_opts
        )

    return needs_types


def _parse_links(links_dict: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    """
    Generate 'needs_extra_links' for sphinx-needs.

    It has a slightly different structure than in our metamodel.yaml.
    """
    return [
        {
            "option": k,
            "incoming": v["incoming"],
            "outgoing": v["outgoing"],
        }
        for k, v in links_dict.items()
    ]


def _collect_all_options(needs_types: dict[str, ScoreNeedType]) -> set[str]:
    all_options: set[str] = set()
    for t in needs_types.values():
        all_options.update(set(t["mandatory_options"].keys()))
        all_options.update(set(t["optional_options"].keys()))
    return all_options


def _collect_all_custom_options(
    needs_types: dict[str, ScoreNeedType],
):
    """Generate 'needs_extra_options' for sphinx-needs."""

    defaults = default_options()
    all_options = _collect_all_options(needs_types)

    return sorted(all_options - defaults)


def load_metamodel_data() -> MetaModelData:
    """
    Load metamodel.yaml and prepare data fields as needed for sphinx-needs.
    """
    yaml_path = Path(__file__).resolve().parent / "metamodel.yaml"

    with open(yaml_path, encoding="utf-8") as f:
        data = cast(dict[str, Any], YAML().load(f))

    # Some options are globally enabled for all types
    global_base_options_optional_opts = data.get("needs_types_base_options", {}).get(
        "optional_options", {}
    )

    # Get the stop_words and weak_words as separate lists
    prohibited_words_checks = _parse_prohibited_words(
        data.get("prohibited_words_checks", {})
    )

    # Convert "types" from {directive_name: {...}, ...} to a list of dicts

    needs_types = _parse_needs_types(
        data.get("needs_types", {}), global_base_options_optional_opts
    )

    return MetaModelData(
        needs_types=list(needs_types.values()),
        needs_extra_links=_parse_links(data.get("needs_extra_links", {})),
        needs_extra_options=_collect_all_custom_options(needs_types),
        prohibited_words_checks=prohibited_words_checks,
        needs_graph_check=data.get("graph_checks", {}),
    )
