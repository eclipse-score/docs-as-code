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
"""Unit tests for :mod:`score_module_verification_report.rendering`."""
from __future__ import annotations

from src.extensions.score_module_verification_report.rendering import (
    normalize_slug,
    render_component,
    render_feature,
    render_overview,
    render_report,
    slugify,
    workproduct_rows,
)


_WP = [
    {"key": "req", "label": "Requirements Inspection", "wp_id": "wp__req"},
    {"key": "arc", "label": "Architecture Inspection", "wp_id": "wp__arc"},
]


# ---------------------------------------------------------------------------
# slug utilities
# ---------------------------------------------------------------------------


def test_normalize_slug_strips_underscores_and_lowercases() -> None:
    assert normalize_slug("Bit_Manipulation") == "bitmanipulation"


def test_slugify_converts_non_alnum_to_dashes() -> None:
    assert slugify("Foo Bar / Baz!") == "foo-bar-baz"


def test_slugify_strips_leading_trailing_dashes() -> None:
    assert slugify("---weird---") == "weird"


# ---------------------------------------------------------------------------
# workproduct_rows
# ---------------------------------------------------------------------------


def test_workproduct_rows_uses_needtable_by_default() -> None:
    out = workproduct_rows("kvs", overrides={}, workproducts=_WP)
    assert ":need:`wp__req`" in out
    assert "Requirements Inspection" in out
    # Both id and status cells rendered as needtables with matching filter.
    assert out.count(".. needtable::") == 4
    # Slug substring match (id.replace("_", "")) is emitted verbatim.
    assert '"kvs" in id.replace("_", "")' in out
    assert '"wp__req" in realizes' in out


def test_workproduct_rows_override_uses_direct_need_and_ndf_copy() -> None:
    overrides = {"workproducts": {"req": "doc__custom_req"}}
    out = workproduct_rows("kvs", overrides, _WP)
    # Overridden row: no needtable, direct :need: + :ndf: copy on status.
    assert ":need:`doc__custom_req`" in out
    assert "copy('status', need_id='doc__custom_req')" in out
    # Non-overridden row (arc) still uses needtable.
    assert '"wp__arc" in realizes' in out


def test_workproduct_rows_no_rows_when_workproducts_empty() -> None:
    assert workproduct_rows("kvs", {}, []) == ""


# ---------------------------------------------------------------------------
# render_overview
# ---------------------------------------------------------------------------


def test_render_overview_builds_id_list_literal() -> None:
    components = [{"id": "comp__a"}, {"id": "comp__b"}]
    out = render_overview(components)
    assert 'id in ["comp__a", "comp__b"]' in out
    assert ".. needtable::" in out


def test_render_overview_empty_components() -> None:
    assert 'id in []' in render_overview([])


# ---------------------------------------------------------------------------
# render_component / render_feature
# ---------------------------------------------------------------------------


def test_render_component_contains_component_specific_filters() -> None:
    comp = {"id": "comp__demo_kvs", "slug": "kvs", "title": "Key-Value Store"}
    out = render_component(comp, overrides={}, workproducts=_WP, coverage_data={})
    # Title underline (~ * len(title)).
    assert "~" * len("Key-Value Store") in out
    # comp_id substituted into all filter expressions.
    assert '"comp__demo_kvs" in satisfied_by' in out
    assert '"comp__demo_kvs" in belongs_to' in out
    # Anchor uses slugified title (spaces / punctuation collapsed).
    assert ".. _comp-key-value-store:" in out
    # Workproduct table headers present.
    assert "Verification & Safety Analysis Documents" in out


def test_render_feature_substitutes_feature_id_and_slug() -> None:
    out = render_feature(
        feature_id="feat__demo",
        feature_slug="demo",
        feature_overrides={},
        feature_workproducts=_WP,
    )
    assert 'id == "feat__demo"' in out
    assert '"feat__demo" in satisfied_by' in out
    assert '"feat__demo" in belongs_to' in out
    assert "Feature Inspection Statistics" in out


# ---------------------------------------------------------------------------
# render_report
# ---------------------------------------------------------------------------


def test_render_report_assembles_all_sections() -> None:
    components = [
        {"id": "comp__demo_a", "slug": "a", "title": "A"},
        {"id": "comp__demo_b", "slug": "b", "title": "B"},
    ]
    out = render_report(
        components=components,
        feature_id="feat__demo",
        feature_slug="demo",
        overrides_by_id={},
        workproducts=_WP,
        feature_workproducts=_WP,
        coverage_data={},
    )
    # CSS block for wp-doc-table styling.
    assert ".wp-doc-table" in out
    # Feature, Components header, overview needtable, per-component sections.
    assert 'id == "feat__demo"' in out
    assert "Components\n----------" in out
    assert 'id in ["comp__demo_a", "comp__demo_b"]' in out
    assert '"comp__demo_a" in satisfied_by' in out
    assert '"comp__demo_b" in satisfied_by' in out


def test_render_report_applies_feature_overrides() -> None:
    out = render_report(
        components=[{"id": "comp__demo_a", "slug": "a", "title": "A"}],
        feature_id="feat__demo",
        feature_slug="demo",
        overrides_by_id={
            "feat__demo": {"workproducts": {"req": "doc__feat_req"}},
        },
        workproducts=_WP,
        feature_workproducts=_WP,
        coverage_data={},
    )
    assert ":need:`doc__feat_req`" in out


def test_render_report_applies_component_overrides() -> None:
    out = render_report(
        components=[{"id": "comp__demo_a", "slug": "a", "title": "A"}],
        feature_id="feat__demo",
        feature_slug="demo",
        overrides_by_id={
            "comp__demo_a": {"workproducts": {"req": "doc__comp_a_req"}},
        },
        workproducts=_WP,
        feature_workproducts=_WP,
        coverage_data={},
    )
    assert ":need:`doc__comp_a_req`" in out
