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

from typing import cast

from docutils import nodes
from sphinx.application import Sphinx

from score_pytest.attribute_plugin import add_test_properties
from src.extensions.score_source_code_linker.testcase_annotations import (
    annotate_testcase_results,
)

# The handler only inspects the doctree; Sphinx's callback signature still
# requires an application argument.
_UNUSED_APP = cast(Sphinx, None)


def _doctree_with_reference(
    *,
    refid: str | None = None,
    refuri: str | None = None,
    text: str = "testcase",
) -> tuple[nodes.document, nodes.reference]:
    doc = nodes.document(None, None)  # type: ignore[arg-type]
    attrs: dict[str, str] = {}
    if refid is not None:
        attrs["refid"] = refid
    if refuri is not None:
        attrs["refuri"] = refuri
    ref = nodes.reference("", "", nodes.Text(text), **attrs)
    doc.append(ref)
    return doc, ref


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_annotates_external_github_testlink():
    """Color the result already present in an external testcase link."""
    url = "https://github.com/example/repo/blob/abc/tests/test.py#L42"
    doc, ref = _doctree_with_reference(refuri=url, text="test_requirement (passed)")
    annotate_testcase_results(_UNUSED_APP, doc, "requirements")

    html = ref.children[-1].astext()
    assert "score-testcase-result--passed" in html
    assert "(passed)" in html
    assert len(ref.children) == 2
    assert ref.children[0].astext() == "test_requirement"
    assert ".score-testcase-result--passed" in doc.astext()
    assert 'html[data-theme="dark"]' in doc.astext()


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_does_not_annotate_reference_without_result_suffix():
    """Leave references without a rendered result suffix unchanged."""
    doc, ref = _doctree_with_reference(
        refid="testcase__foo", text="Some testcase title"
    )
    annotate_testcase_results(_UNUSED_APP, doc, "requirements")
    assert len(ref.children) == 1


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_does_not_annotate_link_without_result_suffix():
    """Leave links unchanged when they have no result suffix."""
    doc, ref = _doctree_with_reference(
        refuri="https://github.com/example/repo/blob/abc/src/other.py#L1"
    )
    annotate_testcase_results(_UNUSED_APP, doc, "requirements")
    assert len(ref.children) == 1


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_does_not_annotate_same_reference_twice():
    """Keep repeated handler invocations from duplicating an annotation."""
    url = "https://github.com/example/repo/blob/abc/tests/test.py#L42"
    doc, ref = _doctree_with_reference(refuri=url, text="testcase (passed)")
    annotate_testcase_results(_UNUSED_APP, doc, "requirements")
    annotate_testcase_results(_UNUSED_APP, doc, "requirements")

    assert len(ref.children) == 2
