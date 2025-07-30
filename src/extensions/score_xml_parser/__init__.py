import os

from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from src.extensions.score_source_code_linker.generate_source_code_links_json import (
    find_git_root,
    find_ws_root
)

from junitparser import JUnitXml
from junitparser 
from sphinx.application import Sphinx

@dataclass
class TestCaseNeed():
    id: str
    filepath: str
    result: str
    partially_verifies: Optional[list[str]]
    fully_verifies: Optional[list[str]]
    test_type: str
    derivation_technique: str





def parse_file(file: Path) -> list[TestCaseNeed]:
    """
    Parsing the test.xml file into a dictionary.
    Infos extracted are:

    Verifies: str # Comma seperated
    Filename: str # Pure filename
    Filepath: str
    Metadata: dict[str,str] # All other properties defined in the test besides `verifies`

    input:
    ======
        file (str): Filepath to the test.xml that should be parsed

    Example:

    input:
    ======
        file: "testfiles/tools_sphinx_extensions_test_requirements_checks_test_checks_test.xml"

    Properties of the file look like this:
    <properties>
        <property name="Verifies"
            value="TOOL_REQ__toolchain_sphinx_needs_build__requirement_linkage_status_check" />
        <property name="Description"
            value="It should check the traceability like linkage of attributes." />
        <property name="ASIL" value="ASIL_D" />
        <property name="Priority" value="1" />
        <property name="TestType" value="Requirements-based test" />
        <property name="DerivationTechnique" value="Analysis of requirements" />
    </properties>

    output dict[str, str]:
    =======
    {
        "verifies": TOOL_REQ__toolchain_sphinx_needs_build__requirement_linkage_status_check,
        "Priority": 1,
        "TestType": Requirements-based test,
        "DerivationTechnique": Analysis of requirements,
        "filename": tools_sphinx_extensions_test_requirements_checks_test_checks_test
        "filepath": testfiles/tools_sphinx_extensions_test_requirements_checks_test_checks_test.xml
    }
    """
    info_dict:dict[str, str] = dict()
    xml = JUnitXml.fromfile(file)
    for suite in xml: 
        for case in suite:
            case
            for prop in case.properties():
                info_dict[prop.name] = prop.value
        info_dict["filename"] = str(file).split("/")[-1].removesuffix(".xml")
        info_dict["filepath"] = str(file)
        return info_dict


def find_xml_files(dir: Path) -> list[Path]:
    """
    Recoursively goes through all directories inside `bazel-testlogs` and finds
    any of the files that is named `test.xml`.
    It then returns the Paths to the files a list

    input:
    ======
        dir (str): Path to 'bazel-testlogs' directory

    output:
    ======
        list: [Path("bazel-testlogs/tools/sphinx_extensions/test/requirements/checks/test_checks/test.xml"), ...]
    """
    test_file_name = "test.xml"

    xml_paths: list[Path] = []
    for root, _, files in os.walk(dir):
        if test_file_name in files:
            xml_paths.append(Path(os.path.join(root, test_file_name)))
    return xml_paths


def setup(app: Sphinx) -> dict[str, str | bool]:
    # Esbonio will execute setup() on every iteration.
    # setup_once will only be called once.
    app.connect("config-inited", generate_test_needs)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

def generate_test_needs():
    git_root =find_git_root(__file__)
    ws_root = find_ws_root()
    assert ws_root
    bazel_testlogs = ws_root / "bazel-testlogs"
    # Check if it exists, create if not
    # Should be possible to build docs without
    assert bazel_testlogs.exists(), "Please run `bazel tests`"
    xml_file_paths = find_xml_files(bazel_testlogs)
    for file in xml_file_paths:
        parse_file(file)





"""
We need a 'testcase' need or whatever, with the following attrs: 

id => build from 'test_file_name_testcasenr' ?
testfile
partially verifies [optional] though this or fully has to exist.
fully verifies [optional]
description => content or just leave this out?
TestType 
Derivation Technique
result => pass, failed, skipped ?
"""
