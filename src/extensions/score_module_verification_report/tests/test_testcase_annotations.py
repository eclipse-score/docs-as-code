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
"""Unit tests for
:mod:`score_module_verification_report.testcase_annotations`."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from docutils import nodes

from src.extensions.score_module_verification_report import (
    testcase_annotations as ta,
)
from src.extensions.score_module_verification_report.testcase_annotations import (  # noqa: E501
    _FALLBACK_COLOR,
    RESULT_COLORS,
    annotate_testcase_results,
)


class _FakeNeedsView:
    def __init__(self, needs):
        self._needs = needs

    def get(self, need_id):
        return self._needs.get(need_id)


def _patch_needs(needs):
    """Return a context-manager patching the module-level ``_needs_view``
    helper so tests do not depend on sphinx-needs being importable."""
    view = _FakeNeedsView(needs) if needs is not None else None
    return patch.object(ta, "_needs_view", lambda env: view)


def _doctree_with_testcase_link(text, refid="testcase__foo"):
    """Build a tiny docutils tree containing a single reference whose
    visible text is ``text`` (mimicking a sphinx-needs back-link)."""
    doc = nodes.document(None, None)  # type: ignore[arg-type]
    ref = nodes.reference("", "", nodes.Text(text), refid=refid)
    doc.append(ref)
    return doc, ref


def _app(env):
    return SimpleNamespace(env=env)


# ---------------------------------------------------------------------------
# annotate_testcase_results — happy paths
# ---------------------------------------------------------------------------


def test_annotates_passed_result_in_green():
    doc, ref = _doctree_with_testcase_link("testcase__foo")
    env = SimpleNamespace(
        module_verification_report_registry={"mod__foo": {"docname": "my_report"}},
    )
    with _patch_needs({"testcase__foo": {"result": "passed"}}):
        annotate_testcase_results(_app(env), doc, "my_report")

    # Original text preserved as first child.
    assert isinstance(ref.children[0], nodes.Text)
    assert ref.children[0].astext() == "testcase__foo"
    # Coloured raw HTML span appended.
    assert isinstance(ref.children[-1], nodes.raw)
    html = ref.children[-1].astext()
    assert RESULT_COLORS["passed"] in html
    assert "(passed)" in html


def test_annotates_failed_result_in_red():
    doc, ref = _doctree_with_testcase_link("testcase__bar")
    env = SimpleNamespace(
        module_verification_report_registry={"mod__r": {"docname": "r"}}
    )
    with _patch_needs({"testcase__bar": {"result": "failed"}}):
        annotate_testcase_results(_app(env), doc, "r")
    html = ref.children[-1].astext()
    assert RESULT_COLORS["failed"] in html
    assert "(failed)" in html


def test_unknown_result_uses_fallback_color():
    doc, ref = _doctree_with_testcase_link("testcase__x")
    env = SimpleNamespace(
        module_verification_report_registry={"mod__r": {"docname": "r"}}
    )
    with _patch_needs({"testcase__x": {"result": "weird"}}):
        annotate_testcase_results(_app(env), doc, "r")
    html = ref.children[-1].astext()
    assert _FALLBACK_COLOR in html
    assert "(weird)" in html


# ---------------------------------------------------------------------------
# annotate_testcase_results — no-op paths
# ---------------------------------------------------------------------------


def test_noop_when_docname_not_registered():
    doc, ref = _doctree_with_testcase_link("testcase__foo")
    env = SimpleNamespace(
        module_verification_report_registry={"mod__other": {"docname": "other"}}
    )
    with _patch_needs({"testcase__foo": {"result": "passed"}}):
        annotate_testcase_results(_app(env), doc, "my_report")
    # Untouched.
    assert len(ref.children) == 1
    assert ref.children[0].astext() == "testcase__foo"


def test_noop_when_attr_absent():
    doc, ref = _doctree_with_testcase_link("testcase__foo")
    env = SimpleNamespace()
    with _patch_needs({"testcase__foo": {"result": "passed"}}):
        annotate_testcase_results(_app(env), doc, "my_report")
    assert len(ref.children) == 1


def test_noop_when_text_not_testcase():
    doc, ref = _doctree_with_testcase_link("comp_req__foo")
    env = SimpleNamespace(
        module_verification_report_registry={"mod__r": {"docname": "r"}}
    )
    with _patch_needs({"comp_req__foo": {"result": "passed"}}):
        annotate_testcase_results(_app(env), doc, "r")
    assert len(ref.children) == 1


def test_noop_when_need_missing():
    doc, ref = _doctree_with_testcase_link("testcase__missing")
    env = SimpleNamespace(
        module_verification_report_registry={"mod__r": {"docname": "r"}}
    )
    with _patch_needs({}):  # empty
        annotate_testcase_results(_app(env), doc, "r")
    assert len(ref.children) == 1


def test_noop_when_result_empty():
    doc, ref = _doctree_with_testcase_link("testcase__x")
    env = SimpleNamespace(
        module_verification_report_registry={"mod__r": {"docname": "r"}}
    )
    with _patch_needs({"testcase__x": {"result": ""}}):
        annotate_testcase_results(_app(env), doc, "r")
    assert len(ref.children) == 1


def test_noop_when_needs_view_unavailable():
    doc, ref = _doctree_with_testcase_link("testcase__x")
    env = SimpleNamespace(
        module_verification_report_registry={"mod__r": {"docname": "r"}}
    )
    with _patch_needs(None):  # sphinx_needs not importable / not ready
        annotate_testcase_results(_app(env), doc, "r")
    assert len(ref.children) == 1
