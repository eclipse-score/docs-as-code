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
"""Unit tests for the dependable element traceability tool."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from score_pytest.attribute_plugin import add_test_properties

from scripts_bazel import dependable_element_trace as trace
from src.extensions.score_source_code_linker.xml_parser import (
    read_dependable_element_needs,
    read_test_xml_file,
)

TEST_XML = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="BitTest" tests="3">
    <testcase name="Sets" file="score/bits/bits_test.cpp" line="10" classname="BitTest">
      <properties>
        <property name="PartiallyVerifies" value="comp_req__bits__set"/>
        <property name="TestType" value="requirements-based"/>
        <property name="DerivationTechnique" value="requirements-analysis"/>
      </properties>
    </testcase>
    <testcase name="Clears" file="score/bits/bits_test.cpp" line="20" classname="BitTest">
      <failure message="expected 0"/>
      <properties>
        <property name="FullyVerifies" value="{clear_ref}"/>
        <property name="TestType" value="requirements-based"/>
        <property name="DerivationTechnique" value="boundary-values"/>
      </properties>
    </testcase>
    <testcase name="Untraced" file="score/bits/bits_test.cpp" line="30" classname="BitTest"/>
  </testsuite>
</testsuites>
"""


def _needs_json(needs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {"current_version": "1", "versions": {"1": {"needs": needs}}}


def _manifest(
    tmp_path: Path,
    *,
    clear_ref: str = "comp_req__bits__clear",
    failing: bool = False,
    integrity_level: str = "B",
    release: bool = False,
) -> dict[str, Any]:
    reqs = tmp_path / "needs_local" / "needs.json"
    reqs.parent.mkdir(parents=True)
    reqs.write_text(
        json.dumps(
            _needs_json(
                {
                    "comp_req__bits__set": {"type": "comp_req", "safety": "ASIL_B"},
                    "comp_req__bits__clear": {"type": "comp_req", "safety": "QM"},
                    "comp_req__bits__header": {"type": "comp_req", "safety": "QM"},
                    "comp_req__bits__old": {"type": "comp_req", "status": "invalid"},
                    "aou_req__bits__ints": {"type": "aou_req", "safety": "ASIL_B"},
                }
            )
        )
    )
    xml = tmp_path / "de" / "tests-report" / "score" / "bits" / "bits_test" / "test.xml"
    xml.parent.mkdir(parents=True)
    content = TEST_XML.format(clear_ref=clear_ref)
    if not failing:
        content = content.replace('<failure message="expected 0"/>', "")
    xml.write_text(content)
    return {
        "label": "//:de",
        "integrity_level": integrity_level,
        "release": release,
        "requirements": [],
        "components": [
            {
                "label": "//score/bits:component",
                "requirements": [str(reqs)],
                "test_reports": [str(xml)],
            }
        ],
    }


def _checks(report: dict[str, Any], severity: str) -> list[str]:
    return [f["check"] for f in report["findings"] if f["severity"] == severity]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_reports_coverage_and_writes_testcase_needs(tmp_path: Path) -> None:
    """Covered/uncovered comp_reqs are reported; invalid ones are ignored."""
    needs_json, report = trace.run(_manifest(tmp_path))

    component = report["components"][0]
    assert component["covered"] == ["comp_req__bits__clear", "comp_req__bits__set"]
    assert component["uncovered"] == ["comp_req__bits__header"]
    assert component["testcases"] == 3
    assert report["result"] == "PASSED"
    assert _checks(report, "warning") == [
        "test_traces_to_requirement",
        "requirement_verified",
    ]

    needs = needs_json["versions"]["1.0"]["needs"]
    assert {n["name"] for n in needs.values()} == {
        "BitTest__Sets",
        "BitTest__Clears",
        "BitTest__Untraced",
    }
    sets = next(n for n in needs.values() if n["name"] == "BitTest__Sets")
    assert sets["type"] == "testcase"
    assert sets["partially_verifies"] == ["comp_req__bits__set"]
    assert sets["component"] == "//score/bits:component"


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_release_mode_fails_on_unverified_requirement(tmp_path: Path) -> None:
    """In release mode an unverified requirement is an error."""
    _, report = trace.run(_manifest(tmp_path, release=True))

    assert report["result"] == "FAILED"
    assert _checks(report, "error") == ["requirement_verified"]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_fails_on_failed_test_and_unknown_reference(tmp_path: Path) -> None:
    """Failed tests and references to unknown Needs are errors."""
    _, report = trace.run(
        _manifest(tmp_path, clear_ref="comp_req__bits__typo", failing=True)
    )

    assert report["result"] == "FAILED"
    assert sorted(_checks(report, "error")) == ["test_passed", "test_reference_exists"]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_fails_when_requirement_exceeds_integrity_level(tmp_path: Path) -> None:
    """An ASIL_B requirement does not fit into a QM dependable element."""
    _, report = trace.run(_manifest(tmp_path, integrity_level="QM"))

    assert report["result"] == "FAILED"
    assert _checks(report, "error") == ["integrity_level"]
    assert "comp_req__bits__set" in report["findings"][0]["message"]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_main_writes_outputs_and_summary(tmp_path: Path) -> None:
    """The CLI writes needs.json, report and a summary with the result."""
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(_manifest(tmp_path)))
    out = tmp_path / "out"
    out.mkdir()

    assert (
        trace.main(
            [
                "--manifest",
                str(manifest),
                "--needs-out",
                str(out / "needs.json"),
                "--report-out",
                str(out / "report.json"),
                "--summary-out",
                str(out / "summary.txt"),
            ]
        )
        == 0
    )
    summary = (out / "summary.txt").read_text().splitlines()
    assert summary[-1] == "RESULT: PASSED"
    assert "2/3 requirements verified by 3 test cases" in summary[1]
    assert json.loads((out / "report.json").read_text())["result"] == "PASSED"


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_docs_reader_restores_the_parsed_test_cases(tmp_path: Path) -> None:
    """The documentation build reads back exactly the test cases of test.xml."""
    manifest = _manifest(tmp_path, failing=True)
    needs_json, _ = trace.run(manifest)
    needs_file = tmp_path / "needs.json"
    needs_file.write_text(json.dumps(needs_json))

    xml = Path(manifest["components"][0]["test_reports"][0])
    expected, _, _ = read_test_xml_file(xml, None)
    restored = read_dependable_element_needs(needs_file, None)

    assert sorted(restored, key=lambda tc: str(tc.name)) == sorted(
        expected, key=lambda tc: str(tc.name)
    )
    links = sorted(link for tc in restored for link in tc.get_test_links())
    assert links == sorted(link for tc in expected for link in tc.get_test_links())
