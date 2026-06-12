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

from typing import cast

import pytest

# noqa
import score_metrics.sphinx_filters as sphinx_filters
from score_metrics.sphinx_filters import (
    generic_pie_items_by_tag,
    generic_pie_linked_items,
)
from sphinx_needs.need_item import NeedItem


def test_generic_pie_linked_items_matches_source_by_id_prefix() -> None:
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


def test_generic_pie_items_by_tag_matches_source_by_id_prefix() -> None:
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


def test_get_key_values_raises_key_error_when_global_is_empty() -> None:
    """It raises KeyError if CALCULATED_METRICS is still empty."""
    results: list[int] = []
    with pytest.raises(KeyError):
        sphinx_filters._get_key_values(results, ["overall_metrics:total"])  # pyright: ignore[reportPrivateUsage]


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


def test_get_metrics_with_custom_type_total_considered_empty_kwargs_raises_index_error() -> (
    None
):
    """Current behavior: empty kwargs raises IndexError."""
    sphinx_filters.CALCULATED_METRICS = EXAMPLE_METRICS
    results: list[int] = []

    with pytest.raises(IndexError):
        sphinx_filters.get_metrics_with_first_value_total(needs=[], results=results)
