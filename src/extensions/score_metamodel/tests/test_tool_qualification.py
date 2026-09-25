# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Tests for the structured SCORE tool-management workflow checks."""

from typing import Any
from unittest.mock import MagicMock

import pytest
from sphinx_needs.need_item import NeedItem

from src.extensions.score_metamodel.checks.tool_qualification import (
    check_tool_malfunction_evaluation,
    check_tool_qualification_workflow,
    derive_tvr_values,
)
from src.extensions.score_metamodel.tests import fake_check_logger, need


def _run_local(malfunction: NeedItem, logger: Any = None) -> Any:
    logger = logger or fake_check_logger()
    check_tool_malfunction_evaluation(MagicMock(), malfunction, logger)
    return logger


def _graph_needs(*needs: NeedItem) -> MagicMock:
    all_needs = MagicMock()
    all_needs.values.return_value = list(needs)
    all_needs.filter_types.return_value = all_needs
    return all_needs


def _low_report(
    *,
    status: str = "evaluated",
    testcase: NeedItem | None = None,
    violated: list[str] | None = None,
) -> MagicMock:
    report = need(
        id="doc_tool__test_report",
        type="doc_tool",
        status=status,
        safety_affected="",
        tcl="",
    )
    usecase = need(
        id="tool_usecase__test_report__context",
        type="tool_usecase",
        belongs_to=["doc_tool__test_report"],
    )
    requirement = need(
        id="tool_req__test_report__requirement",
        type="tool_req",
    )
    malfunction = need(
        id="potential_tool_malfunction__test_report__failure",
        type="potential_tool_malfunction",
        safety_affected="YES",
        detection_sufficient="NO",
        parent_needs=["tool_usecase__test_report__context"],
        violates=violated or ["tool_req__test_report__requirement"],
    )
    needs = [report, usecase, requirement, malfunction]
    if testcase is not None:
        needs.append(testcase)
    return _graph_needs(*needs)


@pytest.mark.parametrize(
    ("safety_affected", "detection_sufficient", "safety_measures", "message"),
    [
        ("YES", None, None, "safety-relevant malfunctions"),
        ("YES", "YES", "", "non-empty `safety_measures`"),
    ],
)
def test_safety_malfunction_requires_conditional_evaluation_data(
    safety_affected: str,
    detection_sufficient: str | None,
    safety_measures: str | None,
    message: str,
):
    """Safety-relevant malfunctions require detection and a positive measure."""
    logger = _run_local(
        need(
            id="potential_tool_malfunction__local_invalid",
            type="potential_tool_malfunction",
            safety_affected=safety_affected,
            detection_sufficient=detection_sufficient,
            safety_measures=safety_measures,
        )
    )

    logger.assert_warning(message)


def test_positive_detection_with_measure_is_valid():
    """A safety-relevant malfunction may be HIGH when its measure is documented."""
    logger = _run_local(
        need(
            id="potential_tool_malfunction__local_valid",
            type="potential_tool_malfunction",
            safety_affected="YES",
            detection_sufficient="YES",
            safety_measures="Independent review of the generated result.",
        )
    )

    logger.assert_no_warnings()


def test_safety_malfunction_with_insufficient_detection_needs_no_measure():
    """LOW evaluation is valid without a measure because it requires qualification."""
    logger = _run_local(
        need(
            id="potential_tool_malfunction__local_low",
            type="potential_tool_malfunction",
            safety_affected="YES",
            detection_sufficient="NO",
        )
    )

    logger.assert_no_warnings()


def test_non_safety_malfunction_does_not_need_detection():
    """Non-safety malfunctions omit detection because it is not meaningful there."""
    logger = _run_local(
        need(
            id="potential_tool_malfunction__local_non_safety",
            type="potential_tool_malfunction",
            safety_affected="NO",
        )
    )

    logger.assert_no_warnings()


def test_non_safety_malfunction_rejects_meaningless_detection():
    """The local check rejects detection data that has no safety meaning."""
    logger = _run_local(
        need(
            id="potential_tool_malfunction__local_meaningless_detection",
            type="potential_tool_malfunction",
            safety_affected="NO",
            detection_sufficient="YES",
        )
    )

    logger.assert_warning("must not define `detection_sufficient`")


def test_low_malfunction_with_tool_requirement_is_valid():
    """A LOW malfunction is qualification-ready when it violates a tool requirement."""
    logger = fake_check_logger()
    check_tool_qualification_workflow(MagicMock(), _low_report(), logger)

    logger.assert_no_warnings()


def test_report_summary_is_derived_when_summary_fields_are_omitted():
    """A TVR stores summary values derived from its malfunction graph."""
    all_needs = _low_report()
    logger = fake_check_logger()

    check_tool_qualification_workflow(MagicMock(), all_needs, logger)

    logger.assert_no_warnings()
    report = all_needs.values.return_value[0]
    assert report["safety_affected"] == "YES"
    assert report["tcl"] == "LOW"


def test_report_without_usecase_is_left_unchanged():
    """Legacy reports without use cases remain compatible with the workflow check."""
    report = need(
        id="doc_tool__report_without_usecase",
        type="doc_tool",
        status="evaluated",
        safety_affected="",
        tcl="",
    )
    logger = fake_check_logger()

    check_tool_qualification_workflow(MagicMock(), _graph_needs(report), logger)

    logger.assert_no_warnings()
    assert report["safety_affected"] == ""
    assert report["tcl"] == ""


def test_low_malfunction_with_only_upstream_requirement_is_invalid():
    """An upstream requirement alone cannot receive tool qualification evidence."""
    upstream = need(id="stkh_req__test_report__requirement", type="stkh_req")
    all_needs = _low_report(violated=["stkh_req__test_report__requirement"])
    all_needs.values.return_value.append(upstream)
    logger = fake_check_logger()

    check_tool_qualification_workflow(MagicMock(), all_needs, logger)

    logger.assert_warning("must violate at least one `tool_req`")


def test_mixed_use_cases_derive_low_from_one_low_malfunction():
    """One LOW malfunction keeps a report LOW even when another use case is HIGH."""
    all_needs = _low_report()
    high_usecase = need(
        id="tool_usecase__test_report__high_context",
        type="tool_usecase",
        belongs_to=["doc_tool__test_report"],
    )
    high_malfunction = need(
        id="potential_tool_malfunction__test_report__high_failure",
        type="potential_tool_malfunction",
        safety_affected="YES",
        detection_sufficient="YES",
        safety_measures="Independent review.",
        parent_needs=[high_usecase["id"]],
    )
    all_needs.values.return_value.extend([high_usecase, high_malfunction])
    logger = fake_check_logger()

    check_tool_qualification_workflow(MagicMock(), all_needs, logger)

    logger.assert_no_warnings()


def test_qualified_low_report_requires_successful_full_evidence():
    """A qualified LOW report needs passed full-verification evidence."""
    all_needs = _low_report(status="qualified")
    logger = fake_check_logger()

    check_tool_qualification_workflow(MagicMock(), all_needs, logger)

    logger.assert_warning("qualification evidence is incomplete")


def test_qualified_low_report_with_passed_full_evidence_is_valid():
    """A passed testcase with full verification completes LOW qualification."""
    testcase = need(
        id="testcase__test_report__qualification",
        type="testcase",
        result="passed",
        fully_verifies=["tool_req__test_report__requirement"],
    )
    all_needs = _low_report(status="qualified", testcase=testcase)
    logger = fake_check_logger()

    check_tool_qualification_workflow(MagicMock(), all_needs, logger)

    logger.assert_no_warnings()


def test_qualified_low_report_requires_evidence_for_each_requirement():
    """Qualification evidence is required for every LOW tool requirement."""
    testcase = need(
        id="testcase__test_report__first_requirement",
        type="testcase",
        result="passed",
        fully_verifies=["tool_req__test_report__requirement"],
    )
    second_requirement = need(
        id="tool_req__test_report__second_requirement",
        type="tool_req",
    )
    second_malfunction = need(
        id="potential_tool_malfunction__test_report__second_failure",
        type="potential_tool_malfunction",
        safety_affected="YES",
        detection_sufficient="NO",
        parent_needs=["tool_usecase__test_report__context"],
        violates=[second_requirement["id"]],
    )
    all_needs = _low_report(status="qualified", testcase=testcase)
    all_needs.values.return_value.extend([second_requirement, second_malfunction])
    logger = fake_check_logger()

    check_tool_qualification_workflow(MagicMock(), all_needs, logger)

    logger.assert_warning("tool_req__test_report__second_requirement")


def test_partial_evidence_alone_does_not_complete_low_qualification():
    """Partial verification is traceability evidence, not complete qualification."""
    testcase = need(
        id="testcase__test_report__partial_qualification",
        type="testcase",
        result="passed",
        partially_verifies=["tool_req__test_report__requirement"],
    )
    all_needs = _low_report(status="qualified", testcase=testcase)
    logger = fake_check_logger()

    check_tool_qualification_workflow(MagicMock(), all_needs, logger)

    logger.assert_warning("qualification evidence is incomplete")


def test_released_low_report_also_requires_successful_full_evidence():
    """Release cannot bypass qualification for a LOW report."""
    all_needs = _low_report(status="released")
    logger = fake_check_logger()

    check_tool_qualification_workflow(MagicMock(), all_needs, logger)

    logger.assert_warning("qualification evidence is incomplete")


def test_high_report_does_not_require_qualification():
    """HIGH reports may be evaluated or released without qualification tests."""
    report = need(
        id="doc_tool__high_report",
        type="doc_tool",
        status="released",
        safety_affected="",
        tcl="",
    )
    usecase = need(
        id="tool_usecase__high_report__context",
        type="tool_usecase",
        belongs_to=[report["id"]],
    )
    malfunction = need(
        id="potential_tool_malfunction__high_report__failure",
        type="potential_tool_malfunction",
        safety_affected="NO",
        parent_needs=[usecase["id"]],
    )
    logger = fake_check_logger()

    check_tool_qualification_workflow(
        MagicMock(), _graph_needs(report, usecase, malfunction), logger
    )

    logger.assert_no_warnings()


def test_qualification_does_not_reclassify_detection_or_tcl():
    """Successful qualification leaves the malfunction and derived TCL unchanged."""
    malfunction = need(
        id="potential_tool_malfunction__qualification_is_not_classification",
        type="potential_tool_malfunction",
        safety_affected="YES",
        detection_sufficient="NO",
    )

    assert derive_tvr_values([malfunction]) == ("YES", "LOW")
    assert malfunction["detection_sufficient"] == "NO"
