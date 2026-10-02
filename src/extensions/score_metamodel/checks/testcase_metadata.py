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
Checks for Testcase Needs.

The mandatory Testcase metadata (test_type, derivation_technique, description)
is enforced via the metamodel (see metamodel.yaml), while the link levels are
enforced by this graph check.
"""

# req-Id: tool_req__docs_test_metadata_mandatory_1
# req-Id: tool_req__docs_test_metadata_mandatory_2
# req-Id: tool_req__docs_test_metadata_link_levels

from typing import cast

from score_metamodel import (
    CheckLogger,
    graph_check,
)
from sphinx.application import Sphinx
from sphinx_needs.data import NeedsView

# The requirement types that a Testcase may link to via `fully_verifies` /
# `partially_verifies`, per test level.
# See tool_req__docs_test_metadata_link_levels.
_ALLOWED_TARGET_TYPES = {
    "feature_integration_test": {"feat_req"},
    "component_integration_test": {"comp_req"},
    "unit_test": {"comp_req"},
}


@graph_check
def check_testcase_link_levels(
    app: Sphinx,
    all_needs: NeedsView,
    log: CheckLogger,
):
    """
    Check that a Testcase links to requirements (via fully_verifies /
    partially_verifies) on the level that matches its ``test_level``:
    - Feature Integration Test -> Feature Requirement
    - Component Integration Test -> Component Requirement
    - Unit Test -> Component Requirement

    A Testcase without a declared ``test_level`` is not checked, as there is
    not enough information to determine the expected target level.

    Note that external Testcase needs are intentionally included even though
    the other checks skip external needs: these come from local test.xml files
    (see score_source_code_linker) and only lack an in-document node, so they
    carry no docname/lineno. ``external_url`` is appended instead.
    """
    needs_dict = {need["id"]: need for need in all_needs.values()}
    for need in all_needs.values():
        if need["type"] != "testcase":
            continue
        test_level = need.get("test_level")
        if not test_level:
            continue
        allowed_types = _ALLOWED_TARGET_TYPES.get(test_level)
        if allowed_types is None:
            continue
        for link_attr in ("fully_verifies", "partially_verifies"):
            for target_id in cast("list[str]", need.get(link_attr) or []):
                target = needs_dict.get(target_id)
                if target is None:
                    # A link to a non-existing need is reported elsewhere.
                    continue
                if target["type"] in allowed_types:
                    continue
                allowed = " or ".join(sorted(allowed_types))
                source = ""
                if not need.get("docname") and need.get("external_url"):
                    source = f" (source: {need['external_url']})"
                log.warning_for_need(
                    need,
                    f"{link_attr} links to `{target_id}` ({target['type']}), "
                    f"but a `{test_level}` test case may only link to {allowed}.{source}",
                    category="link",
                )
