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
"""Tests for testcase metadata validation."""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import MagicMock

import pytest
from sphinx_needs.data import NeedsView
from sphinx_needs.need_item import NeedItem

from src.extensions.score_metamodel.checks.testcase import check_testcase_metadata
from src.extensions.score_metamodel.tests import fake_check_logger, need


class DummyNeedsView:
    """Minimal view supporting the operations used by testcase validation."""

    def __init__(self, needs: list[NeedItem]) -> None:
        self._needs = needs

    def filter_types(self, types: list[str]) -> DummyNeedsView:
        return DummyNeedsView([item for item in self._needs if item["type"] in types])

    def values(self) -> list[NeedItem]:
        return self._needs


def _run(*needs: NeedItem) -> Any:
    log = fake_check_logger()
    check_testcase_metadata(MagicMock(), cast(NeedsView, DummyNeedsView(list(needs))), log)
    log.flush_new_checks()
    return log


def _testcase(**fields: Any) -> NeedItem:
    metadata: dict[str, Any] = {
        "id": "testcase__sample",
        "type": "testcase",
        "test_type": "requirements-based",
        "derivation_technique": "requirements-analysis",
        "content": "Checks the expected behavior.",
    }
    metadata.update(fields)
    return need(**metadata)


@pytest.mark.parametrize(
    ("attribute", "value"),
    [
        (attribute, value)
        for attribute in ("test_type", "derivation_technique")
        for value in (None, "", "   ")
    ],
)
def test_required_metadata_must_be_nonempty(attribute: str, value: str | None) -> None:
    """Report missing and blank metadata values."""
    log = _run(_testcase(**{attribute: value}))
    log.assert_info(
        f"Add a value for `{attribute}` to this test case. "
        "This field is required.",
        expect_location=False
    )


def test_external_testcase_with_wrong_link_level_is_checked() -> None:
    """Apply level checks to imported needs as well as parsed XML needs."""
    testcase = _testcase(
        id="testcase__external",
        is_external=True,
        is_import=True,
        test_type="Unit Test",
        partially_verifies=["feat_req__external_target"],
    )
    target = need(id="feat_req__external_target", type="feat_req")

    log = _run(testcase, target)

    log.assert_info(
        "should link to comp_req requirements instead. Update the link.",
        expect_location=False
    )


def test_valid_external_testcase_metadata_passes() -> None:
    """External testcase needs are checked by the same function as local needs."""
    testcase = _testcase(is_external=True, is_import=True)
    log = _run(testcase)
    log.assert_no_warnings()


def test_non_testcase_needs_are_ignored() -> None:
    """Validation is limited to testcase needs."""
    log = _run(need(id="feat_req__sample", type="feat_req"))
    log.assert_no_warnings()


@pytest.mark.parametrize(
    ("test_type", "target_id", "expected_prefix"),
    [
        ("Feature Integration Test", "comp_req__sample", "feat_req__"),
        ("Component Integration Test", "feat_req__sample", "comp_req__"),
        ("Unit Test", "feat_req__sample", "comp_req__"),
    ],
)
def test_verification_links_must_match_test_level(
    test_type: str, target_id: str, expected_prefix: str
) -> None:
    """Report verification links to the wrong requirement level."""
    target_type = "feat_req" if target_id.startswith("feat_req__") else "comp_req"
    target = need(id=target_id, type=target_type)
    testcase = _testcase(
        test_type=test_type,
        partially_verifies=[target_id],
    )
    log = _run(testcase, target)
    log.assert_info(
        f"should link to {expected_prefix.rstrip('_')} requirements instead. "
        "Update the link.",
        expect_location=False,
    )


@pytest.mark.parametrize("relation", ["fully_verifies", "partially_verifies"])
def test_valid_verification_link_level_passes(relation: str) -> None:
    """Allow both verification relations to the required level."""
    testcase = _testcase(
        test_type="Feature Integration Test",
        **{relation: ["feat_req__sample"]},
    )
    target = need(id="feat_req__sample", type="feat_req")
    log = _run(testcase, target)
    log.assert_no_warnings()


def test_unmapped_test_type_has_no_link_level_constraint() -> None:
    """Do not infer link policy for test types without a defined mapping."""
    testcase = _testcase(
        test_type="interface-test",
        partially_verifies=["feat_req__sample"],
    )
    target = need(id="feat_req__sample", type="feat_req")
    log = _run(testcase, target)
    log.assert_no_warnings()
