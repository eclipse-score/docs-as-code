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
import score_sphinx_needs_templates as sphinx_needs_templates
from score_metrics.sphinx_filters import (
    generic_pie_items_by_tag,
    generic_pie_linked_items,
)
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


_PROPS: dict[str, Any] = {
    "partially_verifies": [],
    "test_type": "interface-test",
    "derivation_technique": "explorative-testing",
}


def _need(need_id: str, need_type: str, link: str, **fields: Any) -> NeedItem:
    need: dict[str, Any] = {
        "id": need_id,
        "type": need_type,
        link: ["comp__x"],
        "fully_verifies_back": [],
        "partially_verifies_back": [],
        **fields,
    }
    return cast(NeedItem, need)


_COMPONENT_NEEDS = [
    _need(
        "r1",
        "comp_req",
        "satisfied_by",
        safety="ASIL_B",
        status="valid_inspected",
        valid_from="v1.0",
        fully_verifies_back=["tc__a"],
    ),
    _need(
        "r2",
        "comp_req",
        "satisfied_by",
        safety="ASIL_B",
        status="valid",
        valid_from="v1.0",
        partially_verifies_back=["tc__b"],
    ),
    _need(
        "r3",
        "comp_req",
        "satisfied_by",
        safety="QM",
        status="valid_inspected",
        valid_from="v1.0",
    ),
    _need(
        "r4",
        "comp_req",
        "satisfied_by",
        safety="QM",
        status="invalid",
        valid_from="v2.0",
    ),
    _need(
        "a1",
        "comp_arc_sta",
        "belongs_to",
        safety="ASIL_B",
        status="valid",
        partially_verifies_back=["tc__c"],
    ),
    _need("a2", "comp_arc_dyn", "belongs_to", safety="QM", status="valid"),
]


def _call_like_needpie(signature: str, needs: list[NeedItem]) -> list[int]:
    """Parse and call a filter-func exactly the way ``needpie`` does."""
    if not signature.startswith("score_metrics."):
        signature = f"score_metrics.sphinx_filters.{signature}"
    ff = check_and_get_external_filter_func(signature)
    assert ff is not None
    args = ff.args.split(",") if ff.args else []
    results: list[int] = []
    ff.func(
        needs=cast(Any, needs),
        results=results,
        **{f"arg{index + 1}": arg for index, arg in enumerate(args)},
    )
    return results


@add_test_properties(**_PROPS)
def test_component_metrics_accept_quoted_arguments() -> None:
    """Quoted, space-separated arguments as written in a template are decoded."""
    status = 'get_component_status_metrics("comp__x", "requirements", "", "")'
    coverage = 'get_component_coverage_metrics("comp__x", "architecture")'

    assert _call_like_needpie(status, _COMPONENT_NEEDS) == [1, 2, 1]
    assert _call_like_needpie(coverage, _COMPONENT_NEEDS) == [0, 1, 1]


@add_test_properties(**_PROPS)
def test_component_metrics_split_by_safety_class() -> None:
    """ASIL lists valid_inspected first; QM counts valid_inspected as valid."""
    asil = "get_component_status_metrics(comp__x, requirements, , ASIL_B)"
    qm = "get_component_status_metrics(comp__x, requirements, , QM)"
    qm_coverage = "get_component_coverage_metrics(comp__x, requirements, , QM)"

    assert _call_like_needpie(asil, _COMPONENT_NEEDS) == [1, 1, 0]
    assert _call_like_needpie(qm, _COMPONENT_NEEDS) == [1, 1]
    assert _call_like_needpie(qm_coverage, _COMPONENT_NEEDS) == [0, 0, 2]


@add_test_properties(**_PROPS)
def test_component_metrics_version_scopes_requirements_only() -> None:
    """``v1_0`` means v1.0; it excludes later requirements, never architecture."""
    reqs = "get_component_status_metrics(comp__x, requirements, v1_0, QM)"
    arcs = "get_component_status_metrics(comp__x, architecture, v1_0, QM)"

    assert _call_like_needpie(reqs, _COMPONENT_NEEDS) == [1, 0]
    assert _call_like_needpie(arcs, _COMPONENT_NEEDS) == [1, 0]


@add_test_properties(**_PROPS)
def test_filter_func_arguments_must_not_contain_a_dot() -> None:
    """sphinx-needs splits the call on its last dot, so ``v1.0`` cannot be passed."""
    with pytest.raises(NeedsInvalidFilter):
        _call_like_needpie(
            "get_component_status_metrics(comp__x, requirements, v1.0, QM)",
            _COMPONENT_NEEDS,
        )


_DEFAULTS: dict[str, list[str]] = {"satisfied_by": [], "belongs_to": []}


def _pie_counts(rst: str, needs: list[NeedItem]) -> list[list[int]]:
    """Evaluate every needpie in a ``safety_pie_row`` block like sphinx-needs."""
    pies: list[list[int]] = []
    for block in rst.split(".. needpie::")[1:]:
        body = [line.strip() for line in block.splitlines()[1:]]
        func = next((line for line in body if line.startswith(":filter-func:")), None)
        if func:
            pies.append(_call_like_needpie(func.split(" ", 1)[1], needs))
            continue
        filters = [line for line in body if line and not line.startswith(":")]
        filters = (
            filters[: filters.index(".. grid-item::")]
            if ".. grid-item::" in filters
            else filters
        )
        pies.append(
            [sum(bool(eval(f, {}, {**_DEFAULTS, **n})) for n in needs) for f in filters]  # noqa: S307
        )
    return pies


@add_test_properties(**_PROPS)
def test_safety_pie_row_filter_funcs_match_inline_filters() -> None:
    """The central filter functions count exactly what the inline filters count."""
    row = vars(sphinx_needs_templates)["_safety_pie_row_callable"]
    in_scope = ["r1", "r2", "r3"]
    req_base = f'type == "comp_req" and "comp__x" in satisfied_by and id in {in_scope}'
    arc_base = 'type in ["comp_arc_sta", "comp_arc_dyn"] and "comp__x" in belongs_to'

    for safety in ("ASIL_B", "QM"):
        for base, category, version in (
            (req_base, "requirements", "v1.0"),
            (arc_base, "architecture", None),
        ):
            inline = row("C", "S", base, safety, safety, 1)
            central = row(
                "C",
                "S",
                "",
                safety,
                safety,
                1,
                component="comp__x",
                category=category,
                version=version,
            )
            assert ":filter-func:" in central
            assert _pie_counts(central, _COMPONENT_NEEDS) == _pie_counts(
                inline, _COMPONENT_NEEDS
            )
