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

from types import SimpleNamespace
from typing import Any

import pytest
from attribute_plugin import add_test_properties  # type: ignore[import-untyped]

import src.extensions.score_source_code_linker.testcase_needs as testcase_needs
from src.extensions.score_source_code_linker.testlink import DataOfTestCase
from src.helper_lib.repo_info import RepoInfo


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="equivalence-classes",
)
def test_short_hash_consistency_and_format():
    """Ensure shorthash has the intended format"""
    h1 = testcase_needs.short_hash("foo")
    h2 = testcase_needs.short_hash("foo")
    assert h1 == h2
    assert h1.isalpha()
    assert len(h1) == 5


@pytest.mark.parametrize(
    ("repo", "line", "expected_url"),
    [
        pytest.param(
            None,
            "10",
            "https://github.com/placeholder/placeholder/blob/unknown/tests/foo_test.py#L10",
            id="missing-repo",
        ),
        pytest.param(
            RepoInfo(name="dependency", hash="", url=""),
            "10",
            "https://github.com/placeholder/placeholder/blob/unknown/tests/foo_test.py#L10",
            id="unpinned-repo",
        ),
        pytest.param(
            RepoInfo(
                name="dependency",
                hash="abc123",
                url="https://github.com/example/dependency",
            ),
            None,
            "https://github.com/example/dependency/blob/abc123/tests/foo_test.py",
            id="pinned-repo-without-line",
        ),
    ],
)
@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="equivalence-classes",
)
def test_construct_and_add_need_uses_source_url_or_placeholder(
    monkeypatch: pytest.MonkeyPatch,
    repo: RepoInfo | None,
    line: str | None,
    expected_url: str,
):
    """A pinned repo yields its real URL; missing pins use the placeholder."""
    calls: list[dict[str, object]] = []

    def _fake_add_external_need(**kwargs: object) -> object:
        calls.append(kwargs)
        return object()

    monkeypatch.setattr(testcase_needs, "add_external_need", _fake_add_external_need)

    testcase = DataOfTestCase(
        name="tc_example",
        file="tests/foo_test.py",
        line=line,
        result="passed",
        result_text="",
        FullyVerifies="REQ_1",
        PartiallyVerifies="",
        TestType="requirements-based",
        DerivationTechnique="analysis",
        repo=repo,
    )

    app_stub: Any = SimpleNamespace(config=SimpleNamespace(needs_fields={}))
    testcase_needs.construct_and_add_need(
        app=app_stub,
        tn=testcase,
    )

    assert len(calls) == 1
    assert calls[0]["external_url"] == expected_url
    assert "bazel_module" not in calls[0]
