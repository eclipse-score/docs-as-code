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
"""Unit tests for testcase result annotations."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from docutils import nodes

from score_pytest.attribute_plugin import add_test_properties
from src.extensions.score_source_code_linker import testcase_annotations as ta
from src.extensions.score_source_code_linker.testcase_annotations import (
    RESULT_CLASSES,
    annotate_testcase_results,
)


class _FakeNeedsView(dict):
    pass


class _FakeSphinxNeedsData:
    def __init__(self, env):
        self._env = env

    def get_needs_view(self):
        return self._env.needs_view


def _patch_needs_data():
    return patch.object(ta, "SphinxNeedsData", _FakeSphinxNeedsData)


def _doctree_with_reference(*, refid=None, refuri=None, text="testcase"):
    doc = nodes.document(None, None)  # type: ignore[arg-type]
    attrs = {}
    if refid is not None:
        attrs["refid"] = refid
    if refuri is not None:
        attrs["refuri"] = refuri
    ref = nodes.reference("", "", nodes.Text(text), **attrs)
    doc.append(ref)
    return doc, ref


def _app(needs):
    return SimpleNamespace(env=SimpleNamespace(needs_view=_FakeNeedsView(needs)))


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_annotates_external_github_testlink():
    """Annotate an unambiguous external testcase link with its result."""
    url = "https://github.com/example/repo/blob/abc/tests/test.py#L42"
    doc, ref = _doctree_with_reference(refuri=url, text="test_requirement")
    needs = {
        "testcase__test_requirement": {
            "type": "testcase",
            "external_url": url,
            "result": "passed",
        }
    }

    with _patch_needs_data():
        annotate_testcase_results(_app(needs), doc, "requirements")

    html = ref.children[-1].astext()
    assert RESULT_CLASSES["passed"] in html
    assert "(passed)" in html
    assert ".score-testcase-result--passed" in doc.astext()
    assert 'html[data-theme="dark"]' in doc.astext()


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_annotates_resolved_testcase_reference_by_refid():
    """Annotate a testcase reference resolved by its need ID."""
    doc, ref = _doctree_with_reference(
        refid="testcase__foo", text="Some testcase title"
    )
    needs = {"testcase__foo": {"type": "testcase", "result": "failed"}}

    with _patch_needs_data():
        annotate_testcase_results(_app(needs), doc, "requirements")

    assert "(failed)" in ref.children[-1].astext()


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_escapes_unexpected_result_value():
    """Escape unexpected testcase result text before rendering HTML."""
    url = "https://github.com/example/repo/blob/abc/tests/test.py#L42"
    doc, ref = _doctree_with_reference(refuri=url)
    needs = {
        "testcase__unsafe": {
            "type": "testcase",
            "external_url": url,
            "result": "<failed&>",
        }
    }

    with _patch_needs_data():
        annotate_testcase_results(_app(needs), doc, "requirements")

    html = ref.children[-1].astext()
    assert "&lt;failed&amp;&gt;" in html
    assert "<failed&>" not in html


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_does_not_annotate_ambiguous_external_github_testlink():
    """Leave URL-only links unchanged when multiple testcases share a URL."""
    url = "https://github.com/example/repo/blob/abc/tests/test.py#L42"
    doc, ref = _doctree_with_reference(refuri=url)
    needs = {
        "testcase__passed": {
            "type": "testcase",
            "external_url": url,
            "result": "passed",
        },
        "testcase__failed": {
            "type": "testcase",
            "external_url": url,
            "result": "failed",
        },
    }

    with _patch_needs_data():
        annotate_testcase_results(_app(needs), doc, "requirements")

    assert len(ref.children) == 1


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_does_not_annotate_empty_result():
    """Leave testcase links unchanged when the result is empty."""
    url = "https://github.com/example/repo/blob/abc/tests/test.py#L42"
    doc, ref = _doctree_with_reference(refuri=url)
    needs = {
        "testcase__empty": {
            "type": "testcase",
            "external_url": url,
            "result": "",
        }
    }

    with _patch_needs_data():
        annotate_testcase_results(_app(needs), doc, "requirements")

    assert len(ref.children) == 1


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_does_not_annotate_unknown_external_link():
    """Leave links unchanged when no testcase matches their URL."""
    doc, ref = _doctree_with_reference(
        refuri="https://github.com/example/repo/blob/abc/src/other.py#L1"
    )
    needs = {
        "testcase__known": {
            "type": "testcase",
            "external_url": "https://github.com/example/repo/blob/abc/tests/test.py#L42",
            "result": "passed",
        }
    }

    with _patch_needs_data():
        annotate_testcase_results(_app(needs), doc, "requirements")

    assert len(ref.children) == 1


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_does_not_annotate_same_reference_twice():
    """Keep repeated handler invocations from duplicating an annotation."""
    url = "https://github.com/example/repo/blob/abc/tests/test.py#L42"
    doc, ref = _doctree_with_reference(refuri=url)
    needs = {
        "testcase__once": {
            "type": "testcase",
            "external_url": url,
            "result": "passed",
        }
    }

    with _patch_needs_data():
        annotate_testcase_results(_app(needs), doc, "requirements")
        annotate_testcase_results(_app(needs), doc, "requirements")

    assert len(ref.children) == 2
