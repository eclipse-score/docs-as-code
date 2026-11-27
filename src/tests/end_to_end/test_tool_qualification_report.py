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
"""tool_qualification_report: a Tool Verification Report next to a mounted module.

The fixture is ``scenarios/tool_qualification_report``. Its report has one
malfunction that needs qualification and one that cannot affect safety. The
verifying testcases cover every result once, and further tool requirements and
testcases of the module are not reached by the report. A mounted second module
and an imported inventory contribute Needs the report must not count.
"""

import html
import re

import pytest
from score_pytest.attribute_plugin import add_test_properties

from src.tests.end_to_end.helpers import run_scenario


@pytest.fixture(scope="module")
def report() -> str:
    build_dir = run_scenario("run", "tool_qualification_report", ":docs").build_dir
    return (build_dir / "tool" / "index.html").read_text(encoding="utf-8")


def _section_text(page: str, section_id: str) -> str:
    """Return the visible text of a rendered section, whitespace collapsed.

    The text ends where the section closes or the next section starts, so
    nested sections are not included.
    """
    body = page.split(f'<section id="{section_id}">', maxsplit=1)[1]
    body = re.split(r"<section id=|</section>", body, maxsplit=1)[0]
    text = html.unescape(re.sub(r"<[^>]+>", " ", body))
    return re.sub(r"\s+", " ", text).strip()


@pytest.mark.bazel_slow
@add_test_properties(
    partially_verifies=["tool_req__docs_tvr_confidence_level"],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_conclusion_states_the_verdict_and_its_evidence(report: str):
    """The conclusion derives the confidence level and summarizes its evidence."""
    conclusion = _section_text(report, "conclusion")
    assert (
        "The tool must be qualified ( tcl: LOW ): 1 of its 2 potential "
        "malfunctions can affect safety without being detected reliably." in conclusion
    )
    assert "Qualification scope: 1 tool requirement to be verified" in conclusion
    assert (
        "Verification: 1 is linked to a fully verifying testcase, "
        "0 only to partially verifying ones, 0 to none." in conclusion
    )
    # Every verifying testcase appears in exactly one result category; an
    # unexpected result is named rather than counted as missing.
    assert (
        "Of 7 verifying testcases, 2 passed, 1 failed, 1 was skipped, "
        "1 is disabled, 1 has result error , 1 has no result." in conclusion
    )
    assert "Coverage: 1 of 1 malfunction is fully covered" in conclusion


@pytest.mark.bazel_slow
@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_requirement_without_qualification_need_is_explained(report: str):
    """A requirement violated only by a malfunction that cannot affect safety.

    It belongs to the report, so it is no gap, but it is not verified for the
    qualification either.
    """
    derivation = _section_text(report, "how-the-conclusion-is-derived")
    assert "The malfunctions of this report violate 1 further tool requirement." in (
        derivation
    )
    assert "tool_req__example_informative" not in _section_text(
        report, "not-covered-by-this-report"
    )


@pytest.mark.bazel_slow
@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_only_the_reports_own_module_is_checked_for_gaps(report: str):
    """Only Needs of the report's own module are counted.

    Neither the mounted module's requirement and testcase nor a requirement
    imported from another module's inventory are counted.
    """
    conclusion = _section_text(report, "conclusion")
    assert (
        "Outside this report: the score_scenarios module also contains "
        "1 tool requirement and 2 testcases that this report does not reach."
        in conclusion
    )
    derivation = _section_text(report, "how-the-conclusion-is-derived")
    assert (
        "The 2 testcases outside this report verify none of its tool "
        "requirements; 1 of them verifies no requirement at all." in derivation
    )
    gaps = _section_text(report, "not-covered-by-this-report")
    assert "tool_req__example_unreached" in gaps
    assert "tool_req__mounted_capability" not in gaps
    assert "tool_req__imported_capability" not in gaps
    assert "tool_req__example_checked" not in gaps


@pytest.mark.bazel_slow
@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_verifying_testcases_are_summarized_by_design(report: str):
    """Testcases without design metadata are counted as "not set", not dropped."""
    testcases = _section_text(report, "verifying-testcases")
    assert "The 7 testcases that verify" in testcases
    assert "Test types: interface-test (1), not set (6)." in testcases
    assert "Derivation techniques: boundary-values (1), not set (6)." in testcases
