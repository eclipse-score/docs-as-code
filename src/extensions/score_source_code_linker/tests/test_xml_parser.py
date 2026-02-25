# *******************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
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
"""
Tests for the xml_parser.py file.
Keep in mind that this is with the 'assertions' inside xml_parser disabled so far.
Once we enable those we will need to change the tests
"""

import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

# This depends on the `attribute_plugin` in our tooling repository
from attribute_plugin import add_test_properties  # type: ignore[import-untyped]

import src.extensions.score_source_code_linker.xml_parser as xml_parser
from src.extensions.score_source_code_linker.testlink import DataOfTestCase


# Unsure if I should make these last a session or not
def _write_test_xml(
    path: Path,
    name: str,
    result: str = "",
    props: dict[str, str] | None = None,
    file: str = "",
    line: int = 0,
):
    """Helper to create the XML structure for a test case."""
    ts = ET.Element("testsuites")
    suite = ET.SubElement(ts, "testsuite")

    # Create testcase with attributes
    tc_attrs = {"name": name}
    if file:
        tc_attrs["file"] = file
    if line:
        tc_attrs["line"] = str(line)
    tc = ET.SubElement(suite, "testcase", tc_attrs)

    # Add failure/skipped status
    if result == "failed":
        ET.SubElement(tc, "failure", {"message": "failmsg"})
    elif result == "skipped":
        ET.SubElement(tc, "skipped", {"message": "skipmsg"})

    # Add properties if provided
    if props:
        props_el = ET.SubElement(tc, "properties")
        for k, v in props.items():
            ET.SubElement(props_el, "property", {"name": k, "value": v})

    # Save to file
    ET.ElementTree(ts).write(path, encoding="utf-8", xml_declaration=True)


@pytest.fixture
def tmp_xml_dirs(
    tmp_path: Path,
) -> Callable[..., tuple[Path, Path, Path, Path, Path]]:
    def _tmp_xml_dirs(
        test_folder: str = "bazel-testlogs",
    ) -> tuple[Path, Path, Path, Path, Path]:
        root = tmp_path / test_folder
        dir1, dir2, dir3, dir4 = (
            root / "with_props",
            root / "no_props",
            root / "with_extra_props",
            root / "missing_props",
        )

        for d in (dir1, dir2, dir3, dir4):
            d.mkdir(parents=True, exist_ok=True)

        # File with properties
        _write_test_xml(
            dir1 / "test.xml",
            name="tc_with_props",
            result="failed",
            file="path1",
            line=10,
            props={
                "PartiallyVerifies": "REQ1",
                "FullyVerifies": "",
                "TestType": "type",
                "DerivationTechnique": "tech",
                "Description": "desc",
            },
        )

        # File without properties
        _write_test_xml(dir2 / "test.xml", name="tc_no_props", file="path2", line=20)

        # File with some properties that we don't care about
        _write_test_xml(
            dir3 / "test.xml",
            name="tc_with_extra_props",
            result="failed",
            file="path1",
            line=10,
            props={
                # Properties we do not parse should not throw an error
                "PartiallyVerifies": "REQ1",
                "FullyVerifies": "",
                "TestType": "type",
                "DerivationTechnique": "tech",
                "Description": "desc",
                "ASIL": "B",
                "important": "yes",
            },
        )

        # File with some properties missing
        _write_test_xml(
            dir4 / "test.xml",
            name="tc_with_missing_props",
            result="failed",
            file="path1",
            line=10,
            props={
                # derivation_technique and test_type are missing
                # This should not make a 'valid' testlink
                "PartiallyVerifies": "REQ1",
                "FullyVerifies": "",
                "Description": "desc",
            },
        )

        return root, dir1, dir2, dir3, dir4

    return _tmp_xml_dirs


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_find_xml_files(
    tmp_xml_dirs: Callable[..., tuple[Path, Path, Path, Path, Path]],
):
    """Ensure xml files are found as expected if bazel-testlogs is used"""
    root: Path
    dir1: Path
    dir2: Path
    root, dir1, dir2, dir3, dir4 = tmp_xml_dirs()
    found = xml_parser.find_xml_files(root)
    expected: set[Path] = {
        dir1 / "test.xml",
        dir2 / "test.xml",
        dir3 / "test.xml",
        dir4 / "test.xml",
    }
    assert set(found) == expected


def test_find_xml_folder(
    tmp_xml_dirs: Callable[..., tuple[Path, Path, Path, Path, Path]],
):
    """Ensure xml files are found as expected if bazel-testlogs is used"""
    root: Path
    root, _, _, _, _ = tmp_xml_dirs()
    found = xml_parser.find_test_folder(base_path=root.parent)
    assert found is not None
    assert found == root


def test_find_xml_folder_test_reports(
    tmp_xml_dirs: Callable[..., tuple[Path, Path, Path, Path, Path]],
):
    # root is the 'tests-report' folder inside tmp_path
    root, _, _, _, _ = tmp_xml_dirs(test_folder="tests-report")
    # We pass the PARENT of 'tests-report' as the workspace root
    found = xml_parser.find_test_folder(base_path=root.parent)
    assert found is not None
    assert found == root


def test_find_xml_files_test_reports(
    tmp_xml_dirs: Callable[..., tuple[Path, Path, Path, Path, Path]],
):
    """Ensure xml files are found as expected if tests-report is used"""
    root: Path
    dir1: Path
    dir2: Path
    root, dir1, dir2, dir3, dir4 = tmp_xml_dirs(test_folder="tests-report")
    found = xml_parser.find_xml_files(dir=root)
    assert found is not None
    expected: set[Path] = {
        root / dir1 / "test.xml",
        root / dir2 / "test.xml",
        root / dir3 / "test.xml",
        root / dir4 / "test.xml",
    }
    assert set(found) == expected


def test_early_return(tmp_path: Path):
    """
    Ensure that if tests-report & bazel-testlogs is not found,
    we return None for early return inside extension
    """
    # Move the test execution context to a 100% empty folder

    found = xml_parser.find_test_folder(tmp_path)
    assert found is None


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_parse_testcase_result():
    """Ensure Testcase results are parsed as intended"""
    tc = ET.Element("testcase", {"name": "a"})
    assert xml_parser.parse_testcase_result(tc) == ("passed", "")

    tc2 = ET.Element("testcase", {"name": "b", "status": "notrun"})
    assert xml_parser.parse_testcase_result(tc2) == ("disabled", "")

    tc3 = ET.Element("testcase", {"name": "c"})
    ET.SubElement(tc3, "failure", {"message": "err"})
    assert xml_parser.parse_testcase_result(tc3) == ("failed", "err")

    tc4 = ET.Element("testcase", {"name": "d"})
    ET.SubElement(tc4, "skipped", {"message": "skp"})
    assert xml_parser.parse_testcase_result(tc4) == ("skipped", "skp")


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_parse_properties():
    """Ensure properties of testcases are parsed as intended"""
    cp: dict[str, Any] = {}
    props_el = ET.Element("properties")
    ET.SubElement(props_el, "property", {"name": "A", "value": "1"})
    ET.SubElement(props_el, "property", {"name": "Description", "value": "ignored"})
    res = xml_parser.parse_properties(cp, props_el)
    assert res["A"] == "1"
    assert "Description" not in res


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_read_test_xml_file(
    tmp_xml_dirs: Callable[..., tuple[Path, Path, Path, Path, Path]],
):
    """Ensure a whole pre-defined xml file is parsed correctly"""
    _: Path
    dir1: Path
    dir2: Path
    _, dir1, dir2, dir3, dir4 = tmp_xml_dirs()
    needs1, no_props1, missing_props1 = xml_parser.read_test_xml_file(dir1 / "test.xml")
    # Should parse the properties and create a 'valid' testlink
    assert isinstance(needs1, list) and len(needs1) == 1
    tcneed = needs1[0]
    assert isinstance(tcneed, DataOfTestCase)
    assert tcneed.result == "failed"
    assert no_props1 == []
    assert missing_props1 == []

    # No properties at all => Should not be a 'valid' testlink
    needs2, no_props2, missing_props2 = xml_parser.read_test_xml_file(dir2 / "test.xml")
    assert needs2 == []
    assert no_props2 == ["tc_no_props"]
    assert missing_props2 == []

    # Extra Properties => Should not cause an error
    needs3, no_props3, missing_props3 = xml_parser.read_test_xml_file(dir3 / "test.xml")
    assert isinstance(needs1, list) and len(needs1) == 1
    tcneed3 = needs3[0]
    assert isinstance(tcneed3, DataOfTestCase)
    assert no_props3 == []
    assert missing_props3 == []

    # Missing some properties => Should not be a 'valid' testlink
    needs4, no_props4, missing_props4 = xml_parser.read_test_xml_file(dir4 / "test.xml")
    assert needs4 == []
    assert no_props4 == []
    assert missing_props4 == ["tc_with_missing_props"]


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_short_hash_consistency_and_format():
    """Ensure shorthash has the intended format"""
    h1 = xml_parser.short_hash("foo")
    h2 = xml_parser.short_hash("foo")
    assert h1 == h2
    assert h1.isalpha()
    assert len(h1) == 5
