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

"""Tests for testcase_needs.py: turning parsed testcases into Sphinx needs."""

from typing import Any

import pytest
from attribute_plugin import add_test_properties  # type: ignore[import-untyped]

import src.extensions.score_source_code_linker.testcase_needs as testcase_needs
from src.extensions.score_source_code_linker.testlink import DataOfTestCase


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_short_hash_consistency_and_format():
    """Ensure shorthash has the intended format"""
    h1 = testcase_needs.short_hash("foo")
    h2 = testcase_needs.short_hash("foo")
    assert h1 == h2
    assert h1.isalpha()
    assert len(h1) == 5


def test_construct_and_add_need_uses_fallback_url_for_missing_repo_metadata(
    monkeypatch: pytest.MonkeyPatch,
):
    calls: list[dict[str, object]] = []

    def _fake_add_external_need(**kwargs: object) -> object:
        calls.append(kwargs)
        return object()

    monkeypatch.setattr(testcase_needs, "add_external_need", _fake_add_external_need)

    testcase = DataOfTestCase(
        name="tc_missing_meta",
        file="tests/foo_test.py",
        line="10",
        result="passed",
        result_text="",
        FullyVerifies="REQ_1",
        PartiallyVerifies="",
        TestType="requirements-based",
        DerivationTechnique="analysis",
        repo=None,
    )

    app_stub: Any = object()
    testcase_needs.construct_and_add_need(
        app=app_stub,
        tn=testcase,
    )

    # Must not crash and should create an external need using fallback metadata.
    assert len(calls) == 1
    assert calls[0]["external_url"] == (
        "https://github.com/placeholder/placeholder/blob/unknown/tests/foo_test.py#L10"
    )
