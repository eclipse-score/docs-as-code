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
"""Tests for the ``mod_ver_report`` Sphinx-Needs content template.

The template is rendered by Sphinx-Needs from the need's own fields, using
MiniJinja. These tests render it directly with the same engine and the same
context shape, so a broken template fails here instead of in a docs build.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sphinx_needs._jinja import render_template_string

TEMPLATE = (
    Path(__file__).resolve().parents[3] / "needs_templates" / "mod_ver_report.need"
)


def _render(**overrides: object) -> str:
    context: dict[str, object] = {
        "id": "mod_vrep__baselibs__report",
        "title": "Baselibs Verification Report",
        "belongs_to": ["mod__baselibs"],
        "components": ["comp__baselibs_json", "comp__baselibs_bit_manipulation"],
        "features": ["feat__baselibs"],
    }
    context.update(overrides)
    return render_template_string(TEMPLATE.read_text(), context, autoescape=False)


def test_template_file_is_shipped() -> None:
    assert TEMPLATE.is_file(), TEMPLATE


# ---------------------------------------------------------------------------
# Feature sections
# ---------------------------------------------------------------------------


def test_feature_section_uses_the_features_link() -> None:
    """The feature is read off the need, never guessed from the module id."""
    out = _render(features=["feat__something_else"])
    assert 'id == "feat__something_else"' in out
    assert "feat__baselibs" not in out


def test_single_feature_keeps_the_plain_heading() -> None:
    out = _render()
    assert "Feature\n-------\n" in out
    assert "Feature: " not in out


def test_one_section_per_feature_with_qualified_headings() -> None:
    out = _render(features=["feat__demo_one", "feat__demo_two"])
    assert 'id == "feat__demo_one"' in out
    assert 'id == "feat__demo_two"' in out
    assert "Feature: Demo One\n" + "-" * len("Feature: Demo One") in out
    assert "Feature: Demo Two\n" + "-" * len("Feature: Demo Two") in out


def test_feature_workproducts_match_on_the_feature_slug() -> None:
    out = _render(features=["feat__baselibs"])
    assert '"baselibs" in id.replace("_", "").lower()' in out
    # The feature table carries only the two feature-level work products.
    feature_block = out[: out.index("Components\n----------")]
    assert "wp__requirements_inspect" in feature_block
    assert "wp__sw_arch_verification" in feature_block
    assert "wp__sw_component_fmea" not in feature_block


# ---------------------------------------------------------------------------
# Component sections
# ---------------------------------------------------------------------------


def test_component_overview_lists_exactly_the_linked_components() -> None:
    out = _render()
    assert (
        ':filter: id in ["comp__baselibs_json", "comp__baselibs_bit_manipulation"]'
        in out
    )


def test_component_title_and_anchor_derive_from_the_id() -> None:
    out = _render()
    assert ".. _comp-bit-manipulation:" in out
    assert "Bit Manipulation\n" + "~" * len("Bit Manipulation") in out
    assert ".. _comp-json:" in out
    assert "Json\n~~~~" in out


def test_every_component_gets_the_full_set_of_workproducts() -> None:
    out = _render(components=["comp__baselibs_json"])
    for wp in (
        "wp__requirements_inspect",
        "wp__sw_arch_verification",
        "wp__sw_implementation_inspection",
        "wp__sw_component_dfa",
        "wp__sw_component_fmea",
    ):
        assert f":need:`{wp}`" in out


def test_needpie_filters_guard_against_missing_verify_fields() -> None:
    """Needs without ``*_verifies_back`` must not break the pie filters."""
    out = _render()
    assert '"fully_verifies_back" in locals()' in out
    assert '"partially_verifies_back" in locals()' in out


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rubric",
    [
        "Feature Requirements Statistics",
        "Feature Architecture Statistics",
        "Feature Inspection Statistics",
        "Components",
        "Component Overview",
        "Component Requirements Statistics",
        "Component Architecture Statistics",
        "Requirements Traceability",
        "Architectural Elements",
        "Verification & Safety Analysis Documents",
    ],
)
def test_all_report_sections_are_present(rubric: str) -> None:
    """Every section must be a real heading — rubrics produce no TOC entries."""
    assert f"{rubric}\n" in _render()


def test_list_tables_have_a_consistent_number_of_fields_per_row() -> None:
    """A short row silently corrupts a ``list-table``; catch it here."""
    lines = _render().splitlines()
    checked = 0
    i = 0
    while i < len(lines):
        if not lines[i].strip().startswith(".. list-table::"):
            i += 1
            continue
        indent = len(lines[i]) - len(lines[i].lstrip())
        j, per_row = i + 1, []
        while j < len(lines):
            line = lines[j]
            if line.strip() and (len(line) - len(line.lstrip())) <= indent:
                break
            stripped = line.strip()
            # A cell may be empty ("- " with nothing after it), e.g. the
            # branch-% column for a file with no branch data.
            if stripped == "*" or stripped.startswith("* - ") or stripped == "* -":
                per_row.append(1)
            elif (stripped == "-" or stripped.startswith("- ")) and per_row:
                per_row[-1] += 1
            j += 1
        assert len(set(per_row)) == 1, f"ragged list-table at line {i + 1}: {per_row}"
        checked += 1
        i = j
    # one feature work-product table + one per component
    assert checked >= 3


def test_no_unrendered_jinja_remains() -> None:
    out = _render()
    for marker in ("{{", "}}", "{%", "%}"):
        assert marker not in out, marker


def test_no_rubrics_are_used() -> None:
    """A rubric is not a section: it yields no TOC entry and no anchor."""
    assert ".. rubric::" not in _render()


def test_every_heading_underline_is_long_enough() -> None:
    """A short underline makes docutils drop the section (and its TOC entry)."""
    lines = _render().splitlines()
    headings = 0
    for title, underline in zip(lines, lines[1:], strict=False):
        if not underline or set(underline) - set("-~^") or not title.strip():
            continue
        if len(set(underline)) != 1 or len(underline) < 3:
            continue
        assert len(underline) >= len(title.rstrip()), (
            f"underline too short for {title!r}"
        )
        headings += 1
    # 3 feature + Components + Component Overview + 2x(title + 5 subsections)
    assert headings >= 15, headings
