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

from typing import Any, cast

import pytest

# noqa
import score_metrics.sphinx_filters as sphinx_filters
from score_metrics.sphinx_filters import (
    generic_pie_items_by_tag,
    generic_pie_linked_items,
)
from score_metrics.traceability_metrics import calculate_verification_metrics
from score_pytest.attribute_plugin import add_test_properties
from sphinx_needs.exceptions import NeedsInvalidFilter
from sphinx_needs.need_item import NeedItem
from sphinx_needs.utils import check_and_get_external_filter_func


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_generic_pie_linked_items_matches_source_by_id_prefix() -> None:
    """Test generic pie linked items matches source by id prefix."""
    needs = cast(
        list[NeedItem],
        [
            {"id": "std_req__iso26262__001", "type": "std_req"},
            # Type intentionally does not match selector prefix, id does.
            {
                "id": "gd_guidl__xyz",
                "type": "guideline",
                "complies": ["std_req__iso26262__001"],
            },
        ],
    )

    results: list[int] = []
    generic_pie_linked_items(
        needs, results, arg1="std_req__iso26262__", arg2="gd_", arg3="complies"
    )

    assert results == [1, 0]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_generic_pie_items_by_tag_matches_source_by_id_prefix() -> None:
    """Test generic pie items by tag matches source by id prefix."""
    needs = cast(
        list[NeedItem],
        [
            {"id": "REQ_A", "type": "tool_req", "tags": ["aspice40_man5"]},
            {"id": "REQ_B", "type": "tool_req", "tags": ["aspice40_man5"]},
            # Type intentionally does not match selector prefix, id does.
            {
                "id": "gd_req__abc",
                "type": "process_requirement",
                "complies": ["REQ_A"],
            },
        ],
    )

    results: list[int] = []
    generic_pie_items_by_tag(
        needs, results, arg1="aspice40_man5", arg2="gd_", arg3="complies"
    )

    assert results == [1, 1]


EXAMPLE_METRICS: dict[str, object] = {
    "schema_version": "1",
    "generated_by": "sphinx_build",
    "overall_metrics": {
        "total": 61,
        "with_code_link": 46,
        "with_test_link": 3,
        "fully_linked": 2,
        "with_code_link_pct": 75.40983606557377,
        "with_test_link_pct": 4.918032786885246,
        "fully_linked_pct": 3.278688524590164,
    },
    "metrics_by_type": {
        "tool_req": {
            "total": 61,
            "with_code_link": 46,
            "with_test_link": 3,
            "fully_linked": 2,
        }
    },
    "tests": {
        "total": 208,
        "linked_to_requirements": 16,
        "linked_to_requirements_pct": 7.6923076923076925,
        "broken_references": [],
    },
}


@pytest.fixture(autouse=True)
def reset_global_metrics():
    """Reset global CALCULATED_METRICS before and after each test."""
    sphinx_filters.CALCULATED_METRICS = {}
    yield
    sphinx_filters.CALCULATED_METRICS = {}


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_get_key_values_raises_key_error_when_global_is_empty() -> None:
    """It raises KeyError if CALCULATED_METRICS is still empty."""
    results: list[int] = []
    with pytest.raises(KeyError):
        sphinx_filters._get_key_values(results, ["overall_metrics:total"])  # pyright: ignore[reportPrivateUsage]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_get_key_values_appends_values_when_metrics_loaded() -> None:
    """It appends resolved integer values once metrics data is loaded."""
    sphinx_filters.CALCULATED_METRICS = EXAMPLE_METRICS
    results: list[int] = []

    sphinx_filters._get_key_values(  # pyright: ignore[reportPrivateUsage]
        results,
        [
            "overall_metrics:total",
            "overall_metrics:with_code_link",
            "tests:linked_to_requirements",
        ],
    )

    assert results == [61, 46, 16]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_get_metrics_with_overall_total_considered_when_metrics_loaded() -> None:
    """It computes remainder from overall total and selected metrics."""
    sphinx_filters.CALCULATED_METRICS = EXAMPLE_METRICS
    results: list[int] = []

    sphinx_filters.get_metrics_with_first_value_total(
        needs=[],
        results=results,
        total="overall_metrics:total",
        code="overall_metrics:with_code_link",
        test="overall_metrics:with_test_link",
        fully="overall_metrics:fully_linked",
    )

    assert results == [10, 46, 3, 2]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_get_metrics_with_custom_type_total_considered_with_total_suffix() -> None:
    """It uses trailing ':total' as baseline and computes remainder."""
    sphinx_filters.CALCULATED_METRICS = EXAMPLE_METRICS
    results: list[int] = []

    sphinx_filters.get_metrics_with_first_value_total(
        needs=[],
        results=results,
        total="metrics_by_type:tool_req:total",
        code="metrics_by_type:tool_req:with_code_link",
        test="metrics_by_type:tool_req:with_test_link",
    )
    print(results)

    assert results == [12, 46, 3]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_get_metrics_with_custom_type_total_considered_without_total_suffix() -> None:
    """It appends values directly when trailing ':total' is not provided."""
    sphinx_filters.CALCULATED_METRICS = EXAMPLE_METRICS
    results: list[int] = []

    sphinx_filters.get_metrics_with_first_value_total(
        needs=[],
        results=results,
        code="metrics_by_type:tool_req:with_code_link",
        test="metrics_by_type:tool_req:with_test_link",
    )
    print(results)

    assert results == [43, 3]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_get_just_metrics_appends_values_when_metrics_loaded() -> None:
    """It appends selected values without remainder logic."""
    sphinx_filters.CALCULATED_METRICS = EXAMPLE_METRICS
    results: list[int] = []

    sphinx_filters.get_just_metrics(
        needs=[],
        results=results,
        total="overall_metrics:total",
        linked_tests="tests:linked_to_requirements",
    )

    assert results == [61, 16]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_get_metrics_with_custom_type_total_considered_empty_kwargs_raises_index_error() -> (
    None
):
    """Current behavior: empty kwargs raises IndexError."""
    sphinx_filters.CALCULATED_METRICS = EXAMPLE_METRICS
    results: list[int] = []

    with pytest.raises(IndexError):
        sphinx_filters.get_metrics_with_first_value_total(needs=[], results=results)


_COMPONENT_NEEDS = cast(
    list[NeedItem],
    [
        {
            "id": "comp_req__x__in",
            "type": "comp_req",
            "satisfied_by": ["comp__x"],
            "status": "valid",
            "valid_from": "v1",
            "fully_verifies_back": ["tc__a"],
            "partially_verifies_back": [],
        },
        {
            "id": "comp_req__x__later",
            "type": "comp_req",
            "satisfied_by": ["comp__x"],
            "status": "invalid",
            "valid_from": "v2",
            "fully_verifies_back": [],
            "partially_verifies_back": [],
        },
        {
            "id": "comp_arc_sta__x__a",
            "type": "comp_arc_sta",
            "belongs_to": ["comp__x"],
            "status": "valid",
            "fully_verifies_back": [],
            "partially_verifies_back": ["tc__b"],
        },
    ],
)


def _call_like_needpie(signature: str, needs: list[NeedItem]) -> list[int]:
    """Parse and call a filter-func exactly the way ``needpie`` does."""
    ff = check_and_get_external_filter_func(f"score_metrics.sphinx_filters.{signature}")
    assert ff is not None
    args = ff.args.split(",") if ff.args else []
    results: list[int] = []
    ff.func(
        needs=needs,
        results=results,
        **{f"arg{index + 1}": arg for index, arg in enumerate(args)},
    )
    return results


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_component_metrics_accept_quoted_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Quoted, space-separated arguments as written in a template are decoded."""
    all_needs = {n["id"]: n for n in _COMPONENT_NEEDS}
    all_needs["comp__x"] = cast(NeedItem, {"id": "comp__x", "type": "comp"})
    monkeypatch.setattr(
        sphinx_filters,
        "CALCULATED_METRICS",
        {"verification_metrics": calculate_verification_metrics(cast(Any, all_needs))},
    )

    status = 'get_component_status_metrics("comp__x", "requirements", "")'
    coverage = 'get_component_coverage_metrics("comp__x", "architecture", "")'

    assert _call_like_needpie(status, _COMPONENT_NEEDS) == [1, 0, 1]
    assert _call_like_needpie(coverage, _COMPONENT_NEEDS) == [0, 1, 0]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_component_metrics_version_scopes_requirements_only() -> None:
    """A version excludes later requirements but never architecture elements."""
    reqs = 'get_component_status_metrics("comp__x", "requirements", "v1")'
    arcs = 'get_component_status_metrics("comp__x", "architecture", "v1")'

    assert _call_like_needpie(reqs, _COMPONENT_NEEDS) == [1, 0, 0]
    assert _call_like_needpie(arcs, _COMPONENT_NEEDS) == [1, 0, 0]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_filter_func_arguments_must_not_contain_a_dot() -> None:
    """sphinx-needs splits the call on its last dot, so ``v1.0`` cannot be passed."""
    with pytest.raises(NeedsInvalidFilter):
        _call_like_needpie(
            'get_component_status_metrics("comp__x", "requirements", "v1.0")',
            _COMPONENT_NEEDS,
        )
