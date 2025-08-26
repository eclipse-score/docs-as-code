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
This file deals with finding and parsing of test.xml files that get created during `bazel test`.
It also generates external needs out of the parsed testcases to enable linking to requirements &gathering statistics
"""

# req-Id: tool_req__docs_test_link_testcase

import base64
import contextlib
import hashlib
import itertools
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element

from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx_needs import logging
from sphinx_needs.api import add_external_need

from src.extensions.score_source_code_linker.testlink import (
    DataOfTestCase,
    store_data_of_test_case_json,
    store_test_xml_parsed_json,
)
from src.helper_lib import find_ws_root
from src.helper_lib.additional_functions import get_github_link

logger = logging.get_logger(__name__)
logger.setLevel("DEBUG")


def parse_testcase_result(testcase: ET.Element) -> tuple[str, str]:
    """
    Returns 'result' and 'result_text' found in the 'message'
    attribute of the result.
    Example:
        => <skipped message="Test skip message"></skipped>

        Returns:
            ("skipped", "Test skip message")
    """
    skipped = testcase.find("skipped")
    failed = testcase.find("failure")
    status = testcase.get("status")
    # NOTE: Special CPP case of 'disabled'
    if status is not None and status == "notrun":
        return "disabled", ""
    if skipped is None and failed is None:
        return "passed", ""
    if failed is not None:
        return "failed", failed.get("message", "")
    if skipped is not None:
        return "skipped", skipped.get("message", "")
    # TODO: Test all possible permuations of this to find if this is unreachable
    raise ValueError(
        f"Testcase: {testcase.get('name')}. Did not find 'failed', 'skipped' or 'passed' in test"
    )


def parse_properties(case_properties: dict[str, Any], properties: Element):
    for prop in properties:
        prop_name = prop.get("name", "")
        prop_value = prop.get("value", "")
        # We ignore the Description of the test as a 'property'.
        # Every language just needs to ensure each test does have a description. No matter where this resides.
        if prop_name == "Description":
            continue
        case_properties[prop_name] = prop_value
    return case_properties


def read_test_xml_file(file: Path) -> tuple[list[DataOfTestCase], list[str]]:
    """
    Reading & parsing the test.xml files into TestCaseNeeds

    Returns:
        tuple consisting of:
            - list[TestCaseNeed]
            - list[str] => Testcase Names that did not have the required properties.
    """
    test_case_needs: list[DataOfTestCase] = []
    non_prop_tests: list[str] = []
    tree = ET.parse(file)
    root = tree.getroot()

    for testsuite in root.findall("testsuite"):
        for testcase in testsuite.findall("testcase"):
            case_properties = {}
            testname = testcase.get("name")
            assert testname is not None, (
                f"Testcase: {testcase} does not have a 'name' attribute. This is mandatory. This should not happen, something is wrong."
            )
            test_file = testcase.get("file")
            line = testcase.get("line")

            #          ╭──────────────────────────────────────╮
            #          │   Assert worldview that mandatory    │
            #          │      things are actually there       │
            #          │         Disabled temporarily         │
            #          ╰──────────────────────────────────────╯

            # assert test_file is not None, (
            #     f"Testcase: {testname} does not have a 'file' attribute. This is mandatory"
            # )
            # assert lineNr is not None, (
            #     f"Testcase: {testname} located in {test_file} does not have a 'lineNr' attribute. This is mandator"
            # )
            case_properties["name"] = testname
            case_properties["file"] = test_file
            case_properties["line"] = line
            case_properties["result"], case_properties["result_text"] = (
                parse_testcase_result(testcase)
            )

            properties_element = testcase.find("properties")
            # HINT: This list is hard coded here, might not be ideal to have that in the long run.
            if properties_element is None:
                non_prop_tests.append(testname)
                continue

            # ╓                                      ╖
            # ║ Disabled Temporarily                 ║
            # ╙                                      ╜
            # assert properties_element is not None, (
            #     f"Testcase: {testname} located in {test_file}:{lineNr}, does not have any properties. Properties 'TestType', 'DerivationTechnique' and either 'PartiallyVerifies' or 'FullyVerifies' are mandatory."
            # )

            case_properties = parse_properties(case_properties, properties_element)
            test_case_needs.append(DataOfTestCase.from_dict(case_properties))
    return test_case_needs, non_prop_tests


def find_xml_files(dir: Path) -> list[Path]:
    """
    Recursively search all test.xml files inside 'bazel-testlogs'

    Returns:
        - list[Path] => Paths to all found 'test.xml' files.
    """

    test_file_name = "test.xml"

    xml_paths: list[Path] = []
    for root, _, files in os.walk(dir):
        if test_file_name in files:
            xml_paths.append(Path(os.path.join(root, test_file_name)))
    return xml_paths


def run_xml_parser(app: Sphinx, env: BuildEnvironment):
    """
    This is the 'main' function for parsing test.xml's and
    building testcase needs.
    It gets called from the source_code_linker __init__
    """
    ws_root = find_ws_root()
    assert ws_root is not None
    bazel_testlogs = ws_root / "bazel-testlogs"
    xml_file_paths = find_xml_files(bazel_testlogs)
    test_case_needs = build_test_needs_from_files(app, env, xml_file_paths)
    # Saving the test case needs for cache
    store_data_of_test_case_json(
        app.outdir / "score_testcaseneeds_cache.json", test_case_needs
    )
    output = list(
        itertools.chain.from_iterable(tcn.get_test_links() for tcn in test_case_needs)
    )
    # This is not ideal, due to duplication, but I can't think of a better solution right now
    store_test_xml_parsed_json(app.outdir / "score_xml_parser_cache.json", output)


def build_test_needs_from_files(
    app: Sphinx, env: BuildEnvironment, xml_paths: list[Path]
) -> list[DataOfTestCase]:
    """
    Reading in all test.xml files, and building 'testcase' external need objects out of them.

    Returns:
        - list[TestCaseNeed]
    """
    tcns: list[DataOfTestCase] = []
    for f in xml_paths:
        b, z = read_test_xml_file(f)
        non_prop_tests = ", ".join(n for n in z)
        if non_prop_tests:
            logger.info(f"Tests missing properties: {non_prop_tests}")
        tcns.extend(b)
        for c in b:
            construct_and_add_need(app, c)
    return tcns


def short_hash(input_str: str, length: int = 5) -> str:
    # Get a stable hash
    sha256 = hashlib.sha256(input_str.encode()).digest()
    # Encode to base32 (A-Z + 2-7), decode to str, remove padding
    b32 = base64.b32encode(sha256).decode("utf-8").rstrip("=")
    # Keep only alphabetic characters
    letters_only = "".join(filter(str.isalpha, b32))
    # Return the first `length` letters
    return letters_only[:length].lower()


def construct_and_add_need(app: Sphinx, tn: DataOfTestCase):
    # IDK if this is ideal or not
    with contextlib.suppress(BaseException):
        _ = add_external_need(
            app=app,
            need_type="testcase",
            title=tn.name,
            tags="TEST",
            id=f"testcase__{tn.name}_{short_hash(tn.file + tn.name).upper()}",
            name=tn.name,
            external_url=get_github_link(tn),
            fully_verifies=tn.FullyVerifies if tn.FullyVerifies is not None else "",
            partially_verifies=tn.PartiallyVerifies
            if tn.PartiallyVerifies is not None
            else "",
            test_type=tn.TestType,
            derivation_technique=tn.DerivationTechnique,
            file=tn.file,
            line=tn.line,
            result=tn.result,  # We just want the 'failed' or whatever
            result_text=tn.result_text if tn.result_text else "",
        )
