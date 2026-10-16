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
"""Validation rules for testcase needs, independent of their source."""

from score_metamodel import CheckLogger, graph_check
from sphinx.application import Sphinx
from sphinx_needs.data import NeedsView
from sphinx_needs.need_item import NeedItem

# Link-level policy is applied only to test types for which the requirement
# defines a mapping. Other test types remain valid without an inferred mapping.
TEST_TYPE_LINK_LEVELS = {
    "Feature Integration Test": "feat_req__",
    "Component Integration Test": "comp_req__",
    "Unit Test": "comp_req__",
}


def _link_ids(need: NeedItem, relation: str) -> list[str]:
    """Return linked need IDs as strings, including external targets."""
    if relation not in need.iter_links_keys():
        return []
    return [str(target) for target in need.get_links(relation, as_str=True)]


def _check_required_metadata(need: NeedItem, log: CheckLogger) -> None:
    for attribute in ("test_type", "derivation_technique"):
        value = need.get(attribute)
        if not isinstance(value, str) or not value.strip():
            log.warning_for_need(
                need,
                f"Add a value for `{attribute}` to this test case. "
                "This field is required.",
                is_new_check=True,
                category="testcase-metadata",
            )


def _check_verification_link_levels(
    need: NeedItem, log: CheckLogger, requirements_by_id: dict[str, NeedItem]
) -> None:
    test_type = need.get("test_type")
    expected_prefix = TEST_TYPE_LINK_LEVELS.get(test_type)
    if expected_prefix is None:
        return

    for relation in ("fully_verifies", "partially_verifies"):
        for target_id in _link_ids(need, relation):
            target = requirements_by_id.get(target_id.split("[", 1)[0])
            if target is None:
                continue
            if target.get("type") not in {
                "feat_req",
                "comp_req",
            } or not target_id.startswith(expected_prefix):
                log.warning_for_need(
                    need,
                    f"The test case links `{relation}` to `{target_id}`, but "
                    f"{test_type} should link to {expected_prefix.rstrip('_')} "
                    "requirements instead. Update the link.",
                    is_new_check=True,
                    category="testcase-metadata",
                )


# req-Id: tool_req__docs_test_metadata_mandatory_1
# req-Id: tool_req__docs_test_metadata_mandatory_2
# req-Id: tool_req__docs_test_metadata_link_levels
@graph_check
def check_testcase_metadata(_: Sphinx, all_needs: NeedsView, log: CheckLogger) -> None:
    """Validate testcase metadata and verification link levels.

    Iterate over the complete needs view deliberately: XML-derived testcases
    and imported needs.json testcases must receive the same checks.
    """
    testcases = list(all_needs.filter_types(["testcase"]).values())
    for need in testcases:
        _check_required_metadata(need, log)

    requirements_by_id = {need["id"]: need for need in all_needs.values()}
    for need in testcases:
        _check_verification_link_levels(need, log, requirements_by_id)
