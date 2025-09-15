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

from src.extensions.score_metamodel.metamodel_types import ProhibitedWordCheck

logger = logging.get_logger(__name__)


@dataclass
class MetaModelData:
    needs_types: list[dict[str, object]]
    needs_extra_links: list[dict[str, str]]
    needs_extra_options: list[str]
    prohibited_words_checks: list[ProhibitedWordCheck]
    needs_graph_check: dict[str, object]


def convert_checks_to_dataclass(
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


def default_options() -> list[str]:
    """
    Helper function to get a list of all default options defined by
    sphinx, sphinx-needs etc.
    """
    return [
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
    ]


def load_metamodel_data() -> MetaModelData:
    """
    Load metamodel.yaml and prepare data fields as needed for sphinx-needs.
    """
    yaml_path = Path(__file__).resolve().parent / "metamodel.yaml"

    yaml = YAML()
    with open(yaml_path, encoding="utf-8") as f:
        data = cast(dict[str, Any], yaml.load(f))

    # Access the custom validation block

    types_dict = cast(dict[str, Any], data.get("needs_types", {}))
    links_dict = cast(dict[str, Any], data.get("needs_extra_links", {}))
    graph_check_dict = cast(dict[str, Any], data.get("graph_checks", {}))
    global_base_options = cast(dict[str, Any], data.get("needs_types_base_options", {}))
    global_base_options_optional_opts = cast(
        dict[str, Any], global_base_options.get("optional_options", {})
    )

    # Get the stop_words and weak_words as separate lists
    proh_checks_dict = cast(
        dict[str, dict[str, Any]], data.get("prohibited_words_checks", {})
    )
    prohibited_words_checks = convert_checks_to_dataclass(proh_checks_dict)

    # Default options by sphinx, sphinx-needs or anything else we need to account for
    default_options_list = default_options()

    # Convert "types" from {directive_name: {...}, ...} to a list of dicts
    needs_types_list = []

    all_options: set[str] = set()
    for directive_name, directive_data in types_dict.items():
        directive_name = cast(str, directive_name)
        directive_data = cast(dict[str, Any], directive_data)
        # Build up a single "needs_types" item
        one_type: dict[str, Any] = {
            "directive": directive_name,
            "title": directive_data.get("title", ""),
            "prefix": directive_data.get("prefix", ""),
        }

        if "color" in directive_data:
            one_type["color"] = directive_data["color"]
        if "style" in directive_data:
            one_type["style"] = directive_data["style"]

        # Store mandatory_options and optional_options directly as a dict
        mandatory_options = cast(
            dict[str, Any], directive_data.get("mandatory_options", {})
        )
        one_type["mandatory_options"] = mandatory_options
        tags = cast(list[str], directive_data.get("tags", []))
        one_type["tags"] = tags
        parts = cast(int, directive_data.get("parts", 3))
        one_type["parts"] = parts

        optional_options = cast(
            dict[str, Any], directive_data.get("optional_options", {})
        )
        optional_options.update(global_base_options_optional_opts)
        one_type["opt_opt"] = optional_options

        all_options.update(list(mandatory_options.keys()))
        all_options.update(list(optional_options.keys()))

        # mandatory_links => "req_link"
        mand_links_yaml = cast(
            dict[str, Any], directive_data.get("mandatory_links", {})
        )
        if mand_links_yaml:
            one_type["req_link"] = [
                (cast(str, k), cast(Any, v)) for k, v in mand_links_yaml.items()
            ]

        # optional_links => "opt_link"
        opt_links_yaml = cast(dict[str, Any], directive_data.get("optional_links", {}))
        if opt_links_yaml:
            one_type["opt_link"] = [
                (cast(str, k), cast(Any, v)) for k, v in opt_links_yaml.items()
            ]

        needs_types_list.append(one_type)

    # Convert "links" dict -> list of {"option", "incoming", "outgoing"}
    needs_extra_links_list: list[dict[str, str]] = []
    for link_option, link_data in links_dict.items():
        link_option = cast(str, link_option)
        link_data = cast(dict[str, Any], link_data)
        needs_extra_links_list.append(
            {
                "option": link_option,
                "incoming": link_data.get("incoming", ""),
                "outgoing": link_data.get("outgoing", ""),
            }
        )

    # We have to remove all 'default options' from the extra options.
    # As otherwise sphinx errors, due to an option being registered twice.
    # They are still inside the extra options we extract to enable
    # constraint checking via regex
    needs_extra_options: list[str] = sorted(all_options - set(default_options_list))

    return MetaModelData(
        needs_types=needs_types_list,
        needs_extra_links=needs_extra_links_list,
        needs_extra_options=needs_extra_options,
        prohibited_words_checks=prohibited_words_checks,
        needs_graph_check=graph_check_dict,
    )
