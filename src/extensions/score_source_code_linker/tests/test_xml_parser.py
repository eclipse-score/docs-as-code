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
from pathlib import Path
from typing import Any

import pytest

import src.extensions.score_source_code_linker.xml_parser as xml_parser
from src.extensions.score_source_code_linker.testlink import DataOfTestCase


# Unsure if I should make these last a session or not
@pytest.fixture
def tmp_xml_dirs(tmp_path):
    root = tmp_path / "bazel-testlogs"
    dir1 = root / "with_props"
    dir2 = root / "no_props"
    dir1.mkdir(parents=True)
    dir2.mkdir(parents=True)

    def write(file_path: Path, testcases: list[ET.Element]):
        ts = ET.Element("testsuites")
        suite = ET.SubElement(ts, "testsuite")
        for tc in testcases:
            suite.append(tc)
        tree = ET.ElementTree(ts)
        tree.write(file_path, encoding="utf-8", xml_declaration=True)

    def make_tc(
        name: str,
        result: str = "",
        props: dict[str, str] = dict(),
        file: str = "",
        line: int = 0,
    ):
        tc = ET.Element("testcase", {"name": name})
        if file:
            tc.set("file", file)
        if line:
            tc.set("line", str(line))
        if result == "failed":
            ET.SubElement(tc, "failure", {"message": "failmsg"})
        elif result == "skipped":
            ET.SubElement(tc, "skipped", {"message": "skipmsg"})
        if props:
            props_el = ET.SubElement(tc, "properties")
            for k, v in props.items():
                ET.SubElement(props_el, "property", {"name": k, "value": v})
        return tc

    # File with properties
    tc1 = make_tc(
        "tc_with_props",
        result="failed",
        props={
            "PartiallyVerifies": "REQ1",
            "FullyVerifies": "",
            "TestType": "type",
            "DerivationTechnique": "tech",
            "Description": "desc",
        },
        file="path1",
        line=10,
    )
    write(dir1 / "test.xml", [tc1])

    # File without properties
    # HINT: Once the assertions in xml_parser are back and active, this should allow us to catch that the tests
    #       Need to be changed too.
    tc2 = make_tc("tc_no_props", file="path2", line=20)
    write(dir2 / "test.xml", [tc2])

    return root, dir1, dir2


def test_find_xml_files(tmp_xml_dirs):
    root, dir1, dir2 = tmp_xml_dirs
    found = xml_parser.find_xml_files(root)
    expected = {dir1 / "test.xml", dir2 / "test.xml"}
    assert set(found) == expected


def test_parse_testcase_result():
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


def test_parse_properties():
    cp: dict[str, Any] = {}
    props_el = ET.Element("properties")
    ET.SubElement(props_el, "property", {"name": "A", "value": "1"})
    ET.SubElement(props_el, "property", {"name": "Description", "value": "ignored"})
    res = xml_parser.parse_properties(cp, props_el)
    assert res["A"] == "1"
    assert "Description" not in res


def test_read_test_xml_file(tmp_xml_dirs):
    root, dir1, dir2 = tmp_xml_dirs

    needs1, no_props1 = xml_parser.read_test_xml_file(dir1 / "test.xml")
    assert isinstance(needs1, list) and len(needs1) == 1
    tcneed = needs1[0]
    assert isinstance(tcneed, DataOfTestCase)
    assert tcneed.result == "failed"
    assert no_props1 == []

    needs2, no_props2 = xml_parser.read_test_xml_file(dir2 / "test.xml")
    assert needs2 == []
    assert no_props2 == ["tc_no_props"]


def test_short_hash_consistency_and_format():
    h1 = xml_parser.short_hash("foo")
    h2 = xml_parser.short_hash("foo")
    assert h1 == h2
    assert h1.isalpha()
    assert len(h1) == 5
