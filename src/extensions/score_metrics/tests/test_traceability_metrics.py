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
import score_metrics.traceability_metrics as metrics
from score_metamodel import ScoreNeedType
from score_metamodel.tests import need as test_need
from sphinx_needs.data import NeedsView
from sphinx_needs.need_item import NeedItem

from score_pytest.attribute_plugin import add_test_properties


@add_test_properties(
    partially_verifies=["tool_req__docs_test_linkage_metrics"],
    test_type="requirements-based",
    derivation_technique="equivalence-classes",
)
def test_get_need_types_by_tags_returns_matching_directives_only() -> None:
    """Return directives for need types sharing at least one selected tag."""
    needs: list[ScoreNeedType] = [
        {
            "title": "Test Type 1",
            "prefix": "TR",
            "tags": ["requirement"],
            "parts": 1,
            "directive": "tool_req",
            "mandatory_options": {
                "id": "^tool_req__.*$",
                "some_required_option": "^some_value__.*$",
            },
            "optional_options": {},
            "mandatory_links": {},
            "optional_links": {},
        },
        {
            "title": "Test Type Verification",
            "prefix": "TRV",
            "tags": ["verification"],
            "parts": 1,
            "directive": "tool_req_ver",
            "mandatory_options": {
                "id": "^tool_req__.*$",
                "some_required_option": "^some_value__.*$",
            },
            "optional_options": {},
            "mandatory_links": {},
            "optional_links": {},
        },
        {
            "title": "Test Type Extra",
            "prefix": "TRE",
            "tags": ["extra"],
            "parts": 1,
            "directive": "tool_req_ext",
            "mandatory_options": {
                "id": "^tool_req__.*$",
                "some_required_option": "^some_value__.*$",
            },
            "optional_options": {},
            "mandatory_links": {},
            "optional_links": {},
        },
    ]
    result = metrics.get_need_types_by_tags(needs, {"verification", "requirement"})
    assert result == ["tool_req", "tool_req_ver"]


@add_test_properties(
    partially_verifies=["tool_req__docs_test_linkage_metrics"],
    test_type="requirements-based",
    derivation_technique="equivalence-classes",
)
def test_get_need_types_by_tags_returns_empty_on_non_match() -> None:
    """Test if function correctly returns empty list if none of the things match"""
    needs: list[ScoreNeedType] = [
        {
            "title": "Test Type 1",
            "prefix": "TR",
            "tags": ["requirement"],
            "parts": 1,
            "directive": "tool_req",
            "mandatory_options": {
                "id": "^tool_req__.*$",
                "some_required_option": "^some_value__.*$",
            },
            "optional_options": {},
            "mandatory_links": {},
            "optional_links": {},
        },
    ]
    result = metrics.get_need_types_by_tags(needs, {"requirements_without_proccess"})
    assert result == []


@add_test_properties(
    partially_verifies=["tool_req__docs_test_linkage_metrics"],
    test_type="interface-test",
    derivation_technique="boundary-values",
)
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("  ", False),
        ("text", True),
        ([], False),
        ([1], True),
        (0, False),
        (1, True),
        (None, False),
    ],
)
def test_is_non_empty_string_and_non_string_behavior(
    value: Any, expected: bool
) -> None:
    """Treat blank strings as empty and all other values by truthiness."""
    # Unsure if we should test this as this is python behaviour, but might as well
    assert metrics.is_non_empty(value) is expected


@add_test_properties(
    partially_verifies=["tool_req__docs_test_linkage_metrics"],
    test_type="requirements-based",
    derivation_technique="boundary-values",
)
@pytest.mark.parametrize(
    ("value1", "value2", "expected"),
    [(3, 0, 100.0), (1, 4, 25.0)],
)
def test_safe_percent_zero(value1: int, value2: int, expected: float) -> None:
    """Check if 100 is returned for empty denominator & normal behaviour"""
    assert metrics.safe_percent(value1, value2) == expected


@add_test_properties(
    partially_verifies=["tool_req__docs_test_linkage_metrics"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_calculate_requirement_metrics_counts_links_and_missing_ids() -> None:
    """Count code/test links and derive missing identifier lists."""
    current_requirement_needs: list[NeedItem] = [
        test_need(id="REQ_1", source_code_link="src/main.c", testlink="TC_1"),
        test_need(id="REQ_2", source_code_link=" ", testlink="TC_2"),
        test_need(id="REQ_3", source_code_link="src/lib.rs", testlink=""),
        test_need(id="REQ_4", source_code_link="", testlink=""),
    ]

    result = metrics.calculate_requirement_metrics(current_requirement_needs)

    assert result["total"] == 4
    assert result["with_code_link"] == 2
    assert result["with_test_link"] == 2
    assert result["fully_linked"] == 1

    assert result["with_code_link_pct"] == 50.0
    assert result["with_test_link_pct"] == 50.0
    assert result["fully_linked_pct"] == 25.0


@add_test_properties(
    partially_verifies=["tool_req__docs_test_linkage_metrics"],
    test_type="requirements-based",
    derivation_technique="equivalence-classes",
)
def test_calculate_requirement_metrics_non_fully_linked() -> None:
    """Count code/test links and derive missing identifier lists."""
    current_requirement_needs: list[NeedItem] = [
        test_need(id="REQ_1", source_code_link="src/main.c", testlink=""),
        test_need(id="REQ_2", source_code_link=" ", testlink="TC_2"),
        test_need(id="REQ_3", source_code_link="src/lib.rs", testlink=""),
        test_need(id="REQ_4", source_code_link="", testlink=""),
    ]

    result = metrics.calculate_requirement_metrics(current_requirement_needs)

    assert result["total"] == 4
    assert result["with_code_link"] == 2
    assert result["with_test_link"] == 1
    assert result["fully_linked"] == 0

    assert result["with_code_link_pct"] == 50.0
    assert result["with_test_link_pct"] == 25.0
    assert result["fully_linked_pct"] == 0.0


@add_test_properties(
    partially_verifies=["tool_req__docs_test_linkage_metrics"],
    test_type="requirements-based",
    derivation_technique="equivalence-classes",
)
def test_calculate_requirement_metrics_non_fully_linked_2() -> None:
    """Count code/test links and derive missing identifier lists."""
    current_requirement_needs: list[NeedItem] = [
        test_need(id="REQ_1", source_code_link="", testlink=""),
        test_need(id="REQ_2", source_code_link="", testlink="TC_2"),
        test_need(id="REQ_3", source_code_link="src/main.c", testlink=""),
        test_need(id="REQ_4", source_code_link=" ", testlink="TC_4"),
    ]

    result = metrics.calculate_requirement_metrics(current_requirement_needs)

    assert result["total"] == 4
    assert result["with_code_link"] == 1
    assert result["with_test_link"] == 2
    assert result["fully_linked"] == 0

    assert result["with_code_link_pct"] == 25.0
    assert result["with_test_link_pct"] == 50.0
    assert result["fully_linked_pct"] == 0.0


@add_test_properties(
    partially_verifies=["tool_req__docs_test_linkage_metrics"],
    test_type="interface-test",
    derivation_technique="design-analysis",
)
def test_calculate_test_metrics_counts_linked_tests_and_broken_refs() -> None:
    """Count linked testcases and list references to missing needs."""
    test_needs: list[NeedItem] = [
        test_need(id="TC_1", partially_verifies=["REQ_1"], fully_verifies=[]),
        test_need(
            id="TC_2", partially_verifies=[], fully_verifies=["REQ_2", "REQ_404"]
        ),
        test_need(id="TC_3", partially_verifies=[], fully_verifies=[]),
    ]

    all_needs = cast(
        NeedsView,
        {
            "REQ_1": test_need(id="REQ_1"),
            "REQ_2": test_need(id="REQ_2"),
        },
    )

    result = metrics.calculate_test_metrics(test_needs, all_needs)

    assert result["total"] == 3
    assert result["linked_to_requirements"] == 2
    assert result["linked_to_requirements_pct"] == pytest.approx(66.6666666667)
    assert result["broken_references"] == [
        {"testcase": "TC_2", "missing_need": "REQ_404"}
    ]
