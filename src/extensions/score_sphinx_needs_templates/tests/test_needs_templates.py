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
"""Tests for graph traversal helpers used by Sphinx-Needs templates."""

from collections.abc import Iterable
from pathlib import Path

import pytest
import score_sphinx_needs_templates as templates
from sphinx.testing.util import SphinxTestApp


class FakeLink:
    """Small test double for the Sphinx-Needs link objects."""

    def __init__(self, target: str):
        self.target = target

    def to_link_string(self) -> str:
        return self.target


class FakeNeed(dict[str, str]):
    """Need-shaped test double with independently controlled link indexes."""

    def __init__(
        self,
        need_id: str,
        *,
        backlinks: Iterable[FakeLink] = (),
        links: Iterable[FakeLink] = (),
    ):
        super().__init__(id=need_id, type="test")
        self._backlinks = list(backlinks)
        self._links = list(links)

    def get_backlinks(self, link_name: str, *, as_str: bool) -> list[FakeLink]:
        del link_name, as_str
        return self._backlinks

    def get_links(self, link_name: str, *, as_str: bool) -> list[FakeLink]:
        del link_name, as_str
        return self._links


def test_backlinks_merge_indexed_and_new_outgoing_links(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A stale non-empty backlink index must not hide links added later."""
    requirement = FakeNeed(
        "REQ",
        backlinks=[FakeLink("TC-old")],
    )
    old_testcase = FakeNeed("TC-old", links=[FakeLink("REQ")])
    new_testcase = FakeNeed("TC-new", links=[FakeLink("REQ")])
    needs = {need["id"]: need for need in (requirement, old_testcase, new_testcase)}
    monkeypatch.setattr(templates, "_get_available_needs", lambda: needs)

    linked_needs_class = vars(templates)["_LinkedNeeds"]
    linked = linked_needs_class()("REQ", "fully_verifies_back")

    assert [need["id"] for need in linked] == ["TC-old", "TC-new"]


def test_parse_version_pads_missing_patch() -> None:
    """A two-component milestone implies patch ``0`` for comparison purposes."""
    parse_version = vars(templates)["_parse_version"]

    assert parse_version("v0.8") == (0, 8, 0)
    assert parse_version("v1.0.1") == (1, 0, 1)
    assert parse_version("V2.3") == (2, 3, 0)


def test_req_in_report_version_unscoped_report_version_always_true() -> None:
    """No ``report_version`` means the report is unscoped ("latest")."""
    req_in_report_version = vars(templates)["_RequirementInReportVersion"]()
    need = FakeNeed("feat_req__x")

    assert req_in_report_version(need, None) is True
    assert req_in_report_version(need, "") is True


def test_req_in_report_version_direct_valid_from_boundary() -> None:
    """``valid_from`` is inclusive: equal or later report_version is in scope."""
    req_in_report_version = vars(templates)["_RequirementInReportVersion"]()
    need = FakeNeed("feat_req__x")
    need["valid_from"] = "v0.8"

    assert req_in_report_version(need, "v0.7") is False
    assert req_in_report_version(need, "v0.8") is True
    assert req_in_report_version(need, "v0.9") is True


def test_req_in_report_version_malformed_valid_from_is_excluded() -> None:
    """An unparsable ``valid_from`` must not raise; it just excludes the need."""
    req_in_report_version = vars(templates)["_RequirementInReportVersion"]()
    need = FakeNeed("feat_req__x")
    need["valid_from"] = "not-a-version"

    assert req_in_report_version(need, "v1.0") is False


def test_req_in_report_version_missing_valid_from_without_derived_from_is_excluded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A requirement with no ``valid_from`` and nothing to inherit from is out."""
    req_in_report_version = vars(templates)["_RequirementInReportVersion"]()
    comp_req = FakeNeed("comp_req__x")
    monkeypatch.setattr(
        templates, "_get_available_needs", lambda: {"comp_req__x": comp_req}
    )

    assert req_in_report_version(comp_req, "v1.0") is False


def test_req_in_report_version_comp_req_inherits_via_derived_from(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``comp_req`` has no ``valid_from`` of its own; it inherits its scope from
    the ``feat_req`` it is ``derived_from``."""
    req_in_report_version = vars(templates)["_RequirementInReportVersion"]()
    feat_req = FakeNeed("feat_req__x")
    feat_req["valid_from"] = "v0.8"
    comp_req = FakeNeed("comp_req__x", links=[FakeLink("feat_req__x")])
    needs = {"feat_req__x": feat_req, "comp_req__x": comp_req}
    monkeypatch.setattr(templates, "_get_available_needs", lambda: needs)

    assert req_in_report_version(comp_req, "v0.7") is False
    assert req_in_report_version(comp_req, "v0.8") is True


def test_any_req_in_report_version_unscoped_true_even_for_empty_list() -> None:
    """Unscoped ("latest") reports keep Features/Components with no requirement."""
    any_req_in_report_version = vars(templates)["_AnyRequirementInReportVersion"]()

    assert any_req_in_report_version([], None) is True


def test_any_req_in_report_version_scoped_empty_list_is_excluded() -> None:
    """A scoped report has nothing to show for a Feature/Component with no reqs."""
    any_req_in_report_version = vars(templates)["_AnyRequirementInReportVersion"]()

    assert any_req_in_report_version([], "v1.0") is False


def test_any_req_in_report_version_true_if_at_least_one_requirement_matches() -> None:
    any_req_in_report_version = vars(templates)["_AnyRequirementInReportVersion"]()
    out_of_scope = FakeNeed("feat_req__a")
    out_of_scope["valid_from"] = "v2.0"
    in_scope = FakeNeed("feat_req__b")
    in_scope["valid_from"] = "v0.8"

    assert any_req_in_report_version([out_of_scope, in_scope], "v1.0") is True


def test_any_req_in_report_version_false_if_no_requirement_matches() -> None:
    any_req_in_report_version = vars(templates)["_AnyRequirementInReportVersion"]()
    a = FakeNeed("feat_req__a")
    a["valid_from"] = "v2.0"
    b = FakeNeed("feat_req__b")
    b["valid_from"] = "v3.0"

    assert any_req_in_report_version([a, b], "v1.0") is False


def test_tool_qualification_matrix_groups_shared_requirements(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Render shared tool requirements in the qualification matrix.

    A tool requirement is reusable across project use cases. This fixture models
    two use cases, each with a different LOW-confidence malfunction, while both
    malfunctions violate the same tool requirement. The matrix must expose the
    three verification categories and place the unlinked requirement in the
    corresponding column for each malfunction.

    This is an integration test because the category assignment and table
    structure are produced by the Jinja post-template.
    """
    monkeypatch.setenv("BUILD_WORKSPACE_DIRECTORY", str(tmp_path))
    (tmp_path / "conf.py").write_text(
        """
extensions = ["sphinx_needs", "score_sphinx_needs_templates", "score_metamodel"]
master_doc = "index"
needs_id_regex = r"^[a-zA-Z0-9_]+$"
""",
        encoding="utf-8",
    )
    (tmp_path / "index.rst").write_text(
        """
.. doc_tool:: Shared requirement report
   :id: doc_tool__shared_requirement_report
   :status: evaluated
   :security_affected: NO
   :tool_version: v1
   :post_template: tool_qualification_report

.. gd_req:: Shared process requirement
   :id: gd_req__shared_requirement

   The process shall preserve shared qualification evidence.

.. tool_req:: Shared tool requirement
   :id: tool_req__shared_requirement
   :satisfies: gd_req__shared_requirement

   The tool shall satisfy the shared capability.

.. tool_usecase:: First use case
   :id: tool_usecase__shared_requirement_first
   :belongs_to: doc_tool__shared_requirement_report

   The tool is used to prepare the first project artifact.

   .. potential_tool_malfunction:: First malfunction
      :id: potential_tool_malfunction__shared_requirement_first
      :violates: tool_req__shared_requirement
      :safety_affected: YES
      :detection_sufficient: NO
      :safety_measures: Independent review

.. tool_usecase:: Second use case
   :id: tool_usecase__shared_requirement_second
   :belongs_to: doc_tool__shared_requirement_report

   The tool is used to prepare the second project artifact.

   .. potential_tool_malfunction:: Second malfunction
      :id: potential_tool_malfunction__shared_requirement_second
      :violates: tool_req__shared_requirement
      :safety_affected: YES
      :detection_sufficient: NO
      :safety_measures: Independent review
""",
        encoding="utf-8",
    )

    app = SphinxTestApp(
        srcdir=tmp_path,
        outdir=tmp_path / "_build",
        buildername="html",
        freshenv=True,
    )
    try:
        app.build(force_all=True)
        html = (app.outdir / "index.html").read_text(encoding="utf-8")
    finally:
        app.cleanup()

    purpose_section = html.split('<section id="purpose-and-intended-use">', maxsplit=1)[
        1
    ].split('<section id="conclusion">', maxsplit=1)[0]
    assert "<table" not in purpose_section
    assert "First use case" in purpose_section
    assert "The tool is used to prepare the first project artifact." in purpose_section
    assert 'href="#tool_usecase__shared_requirement_first"' in purpose_section
    assert "First malfunction" not in purpose_section
    assert "safety_affected" not in purpose_section

    evaluation_section = html.split('<section id="evaluation-overview">', maxsplit=1)[
        1
    ].split('<section id="tool-qualification-matrix">', maxsplit=1)[0]
    assert "Violates" not in evaluation_section
    assert "Safety affected" in evaluation_section
    assert "SCORE TCL" in evaluation_section
    assert "<em>Capability being evaluated.</em>" in evaluation_section
    assert "table.tool-qualification-report tbody a" in evaluation_section
    assert "LOW" in evaluation_section
    assert "First use case (" not in evaluation_section
    assert "First malfunction (" not in evaluation_section
    assert '<div class="line">First use case</div>' in evaluation_section
    assert (
        '<div class="line"><a class="reference external" '
        'href="#tool_usecase__shared_requirement_first">'
        "tool_usecase__shared_requirement_first</a></div>" in evaluation_section
    )
    assert 'href="#tool_usecase__shared_requirement_first"' in evaluation_section
    assert (
        'href="#potential_tool_malfunction__shared_requirement_first"'
        in evaluation_section
    )

    matrix_section = html.split('<section id="tool-qualification-matrix">', maxsplit=1)[
        1
    ]
    assert "Fully verified tool requirements" in matrix_section
    assert "Partially verified tool requirements" in matrix_section
    assert "Unverified tool requirements" in matrix_section
    assert "Tool requirements (with testlinks)" not in matrix_section
    assert "Tool requirements (without testlinks)" not in matrix_section
    assert matrix_section.index("First use case") < matrix_section.index(
        "First malfunction"
    )
    assert (
        matrix_section.count(
            '<a class="reference external" '
            'href="#tool_req__shared_requirement">tool_req__shared_requirement</a>'
        )
        == 2
    )
    assert '<section id="qualification-evidence">' not in html
    assert '<section id="traceability-evidence">' not in html
