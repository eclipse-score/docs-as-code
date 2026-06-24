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

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
from typing import Any

from sphinx.application import Sphinx
from pprint import pprint

from src.extensions.score_metamodel import ScoreNeedType

extensions = [
    "sphinx_needs",
    "score_metamodel",
]
# Required to test this for the check in id_contains_feature
required_in_id = ["blabla"]
needs_external_needs = [
    {
        "base_url": "https://eclipse-score.github.io/process_description/main/",
        "json_path": "needs.json",
    }
]
# We add these suppress_warnings here to ease the load of the warnings
# In the future we might want to check if ANY warnings comes in the document
# And then ensure that we error, as this could also be parsing errors etc.
suppress_warnings = ["app.add_directive", "app.add_node", "app.add_role"]


def setup(app: Sphinx):
    add_needs_fields: dict[str, Any] = {
        "check": {
            "description": "Define which 'metamodel' check should be activated for this RST check",
            "schema": {
                "type": "string",
            },
            "nullable": True,
        },
        "expect_not": {
            "description": "Partial string that is not exepcted to be in rst test warnings",
            "schema": {
                "type": "array",
                "items": {"type": "string"},
            },
            "nullable": True,
        },
        "expect": {
            "description": "String that is exepcted to be in rst test warnings",
            "schema": {
                "type": "array",
                "items": {"type": "string"},
            },
            "nullable": True,
        },
        "fully_verifies_list": {
            "description": "List of requirements that this RST test fully verifies",
            "schema": {
                "type": "array",
                "items": {"type": "string"},
            },
            "nullable": True,
        },
        "partially_verifies_list": {
            "description": "List of requirements that this RST test partially verifies",
            "schema": {
                "type": "array",
                "items": {"type": "string"},
            },
            "nullable": True,
        },
    }
    add_options_regex = {
        "check": "^.*$",
        "expect_not": "^.*$",
        "expect": "^.*$",
        "fully_verifies_list": "^.*$",
        "partially_verifies_list": "^.*$",
    }

    test_metadata_need_type: list[ScoreNeedType] = [
        {
            "directive": "test_metadata",
            "title": "Test Metadata",
            "prefix": "test_metadata__",
            "tags": [],
            "parts": 2,
            "mandatory_options": {"id": "^test_metadata__.*$"},
            "optional_options": add_options_regex,
            "mandatory_links_str": {},
            "mandatory_links": {},
            "optional_links_str": {},
            "optional_links": {},
        }
    ]

    # At parse time these are None, as they need to be filled post-parsing when all types are available to resolve the link targets.
    # The dict maps the link name to a list of need types that are allowed as targets for that link.

    changed_needs_types = list(test_metadata_need_type)
    all_needs_types = app.config.needs_types
    if "test_metadata" not in {nt["directive"] for nt in all_needs_types}:
        for need_type in all_needs_types:
            opts: dict[str, Any] = need_type.get("optional_options") or {}
            opts.update(add_options_regex)
            need_type["optional_options"] = opts
            changed_needs_types.append(need_type)
        app.config.needs_types = changed_needs_types
    pprint(app.config.needs_types)
    app.config.needs_fields.update(add_needs_fields)
