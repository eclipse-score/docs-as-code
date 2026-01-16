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
import contextlib
import json
import os
import shutil
import subprocess
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from pytest import TempPathFactory
from sphinx.testing.util import SphinxTestApp
from sphinx_needs.data import SphinxNeedsData

from src.extensions.score_source_code_linker.needlinks import NeedLink
from src.extensions.score_source_code_linker.testlink import (
    DataForTestLink,
    DataForTestLink_JSON_Decoder,
)
from src.extensions.score_source_code_linker.tests.test_codelink import (
    needlink_test_decoder,
)
from src.extensions.score_source_code_linker.tests.test_need_source_links import (
    SourceCodeLinks_TEST_JSON_Decoder,
)
from src.helper_lib import find_ws_root, get_github_base_url
from src.helper_lib.additional_functions import get_github_link


@pytest.fixture()
def sphinx_base_dir(tmp_path_factory: TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("test_git_repo")


@pytest.fixture()
def git_repo_setup(sphinx_base_dir: Path) -> Path:
    """Creating git repo, to make testing possible"""

    repo_path = sphinx_base_dir
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=repo_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True
    )

    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/testorg/testrepo.git"],
        cwd=repo_path,
        check=True,
    )
    os.environ["BUILD_WORKSPACE_DIRECTORY"] = str(repo_path)
    return repo_path


@pytest.fixture()
def create_demo_files(sphinx_base_dir: Path, git_repo_setup: Path):
    repo_path = sphinx_base_dir

    # Create some source files with requirement IDs
    source_dir = repo_path / "src"
    source_dir.mkdir()

    # Create source files that contain requirement references
    (source_dir / "implementation1.py").write_text(make_codelink_source_1())

    (source_dir / "implementation2.py").write_text(make_codelink_source_2())
    (source_dir / "bad_implementation.py").write_text(make_codelink_bad_source())
    # Create a docs directory for Sphinx
    docs_dir = repo_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.rst").write_text(basic_needs())
    (docs_dir / "conf.py").write_text(basic_conf())

    # Create test.xml files
    bazel_testdir1 = repo_path / "bazel-testlogs"
    bazel_testdir1.mkdir()
    bazel_testdir2 = bazel_testdir1 / "src"
    bazel_testdir2.mkdir()

    (bazel_testdir2 / "test.xml").write_text(make_test_xml_1())
    testsdir = bazel_testdir2 / "tests"
    testsdir.mkdir()
    (testsdir / "test.xml").write_text(make_test_xml_2())

    curr_dir = Path(__file__).absolute().parent
    # print("CURR_dir", curr_dir)
    shutil.copyfile(
        curr_dir / "expected_codelink.json", repo_path / ".expected_codelink.json"
    )
    shutil.copyfile(
        curr_dir / "expected_testlink.json", repo_path / ".expected_testlink.json"
    )
    shutil.copyfile(
        curr_dir / "expected_grouped.json", repo_path / ".expected_grouped.json"
    )

    # Add files to git and commit
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit with test files"],
        cwd=repo_path,
        check=True,
    )


def make_codelink_source_1():
    return (
        """
# This is a test implementation file
#"""
        + """ req-Id: TREQ_ID_1
def some_function():
    pass

# Some other code here
# More code...
#"""
        """ req-Id: TREQ_ID_2
def another_function():
    pass
"""
    )


def make_codelink_source_2():
    return (
        """
# Another implementation file
# Though we should make sure this
# is at a different line than the other ID
#"""
        + """ req-Id: TREQ_ID_1
class SomeClass:
    def method(self):
        pass

"""
    )


def make_codelink_bad_source():
    return (
        """
#"""
        + """ req-Id: TREQ_ID_200
def This_Should_Error(self):
    pass

"""
    )


def make_test_xml_1():
    return """
<testsuites>
  <testsuite name="TestInterfaceValidation" tests="2" failures="0" errors="0" time="0.123" timestamp="2025-08-12T10:30:00">
    <testcase name="test_api_response_format" classname="" file="src/testfile_1.py" line="10" time="0.056">
      <properties>
        <property name="PartiallyVerifies" value="TREQ_ID_2, TREQ_ID_3"/>
        <property name="TestType" value="interface-test"/>
        <property name="DerivationTechnique" value="design-analysis"/>
      </properties>
    </testcase>
    <testcase name="test_error_handling" classname="" file="src/testfile_1.py" line="38" ttime="0.067">
      <properties>
        <property name="PartiallyVerifies" value="TREQ_ID_2, TREQ_ID_3"/>
        <property name="TestType" value="interface-test"/>
        <property name="DerivationTechnique" value="design-analysis"/>
      </properties>
    </testcase>
  </testsuite>
</testsuites>
"""


def make_test_xml_2():
    # ruff: This is a long xml string, so ignore the line length check for the block
    # flake8: noqa: E501 (start)
    return """
<testsuites>
  <testsuite name="TestRequirementsCoverage" tests="2" failures="0" errors="0" time="0.234" timestamp="2025-08-12T10:31:00">
    <testcase name="test_system_startup_time" classname="test_requirements_coverage.TestRequirementsCoverage" file="src/tests/testfile_2.py" line="25" time="0.089">
      <properties>
        <property name="FullyVerifies" value="TREQ_ID_1"/>
        <property name="TestType" value="requirements-based"/>
        <property name="DerivationTechnique" value="requirements-analysis"/>
      </properties>
    </testcase>
    <testcase name="test_error_handling_skipped" classname="" file="src/tests/testfile_2.py" line="102" time="0.067">
      <skipped message="Test skipped test" type="pytest.skip">This is a message that shouldn't show up</skipped>
    </testcase>
  </testsuite>
</testsuites>
"""


# flake8: noqa: E501 (end)


def construct_gh_url() -> str:
    gh = get_github_base_url()
    return f"{gh}/blob/"


@pytest.fixture()
def sphinx_app_setup(
    sphinx_base_dir: Path, create_demo_files: None, git_repo_setup: Path
) -> Callable[[], SphinxTestApp]:
    def _create_app():
        base_dir = sphinx_base_dir
        docs_dir = base_dir / "docs"

        # CRITICAL: Change to a directory that exists and is accessible
        # This fixes the "no such file or directory" error in Bazel
        original_cwd = None
        # Current working directory doesn't exist, which is the problem
        with contextlib.suppress(FileNotFoundError):
            original_cwd = os.getcwd()

        # Change to the base_dir before creating SphinxTestApp
        os.chdir(base_dir)
        try:
            return SphinxTestApp(
                freshenv=True,
                srcdir=docs_dir,
                confdir=docs_dir,
                outdir=sphinx_base_dir / "out",
                buildername="html",
                warningiserror=True,
            )
        finally:
            # Try to restore original directory, but don't fail if it doesn't exist
            if original_cwd is not None:
                # Original directory might not exist anymore in Bazel sandbox
                with contextlib.suppress(FileNotFoundError, OSError):
                    os.chdir(original_cwd)

    return _create_app


def basic_conf():
    return """
extensions = [
    "sphinx_needs",
    "score_source_code_linker",
]
needs_types = [
    dict(
        directive="test_req",
        title="Testing Requirement",
        prefix="TREQ_",
        color="#BFD8D2",
        style="node",
    ),
]
needs_extra_options = ["source_code_link", "testlink"]
needs_extra_links =  [{
      "option": "partially_verifies",
      "incoming": "paritally_verified_by",
      "outgoing": "paritally_verifies",
   },
   {
      "option": "fully_verifies",
      "incoming": "fully_verified_by",
      "outgoing": "fully_verifies",
   }]

"""


def basic_needs():
    return """
TESTING SOURCE LINK
===================

.. test_req:: TestReq1
   :id: TREQ_ID_1
   :status: valid

.. test_req:: TestReq2
   :id: TREQ_ID_2
   :status: open

.. test_req:: TestReq3
   :id: TREQ_ID_3
   :status: open
"""


@pytest.fixture()
def example_source_link_text_all_ok(sphinx_base_dir: Path):
    return {
        "TREQ_ID_1": [
            NeedLink(
                file=Path("src/implementation2.py"),
                line=5,
                tag="#" + " req-Id:",
                need="TREQ_ID_1",
                full_line="#" + " req-Id: TREQ_ID_1",
            ),
            NeedLink(
                file=Path("src/implementation1.py"),
                line=3,
                tag="#" + " req-Id:",
                need="TREQ_ID_1",
                full_line="#" + " req-Id: TREQ_ID_1",
            ),
        ],
        "TREQ_ID_2": [
            NeedLink(
                file=Path("src/implementation1.py"),
                line=9,
                tag="#" + " req-Id:",
                need="TREQ_ID_2",
                full_line="#" + " req-Id: TREQ_ID_2",
            )
        ],
        "TREQ_ID_3": [],
    }


@pytest.fixture()
def example_test_link_text_all_ok(sphinx_base_dir: Path):
    return {
        "TREQ_ID_1": [
            DataForTestLink(
                name="TestRequirementsCoverage__test_system_startup_time",
                file=Path("src/tests/testfile_2.py"),
                need="TREQ_ID_1",
                line=25,
                verify_type="fully",
                result="passed",
                result_text="",
            ),
        ],
        "TREQ_ID_2": [
            DataForTestLink(
                name="test_api_response_format",
                file=Path("src/testfile_1.py"),
                need="TREQ_ID_2",
                line=10,
                verify_type="partially",
                result="passed",
                result_text="",
            ),
            DataForTestLink(
                name="test_error_handling",
                file=Path("src/testfile_1.py"),
                need="TREQ_ID_2",
                line=38,
                verify_type="partially",
                result="passed",
                result_text="",
            ),
        ],
        "TREQ_ID_3": [
            DataForTestLink(
                name="test_api_response_format",
                file=Path("src/testfile_1.py"),
                need="TREQ_ID_3",
                line=10,
                verify_type="partially",
                result="passed",
                result_text="",
            ),
            DataForTestLink(
                name="test_error_handling",
                file=Path("src/testfile_1.py"),
                need="TREQ_ID_3",
                line=38,
                verify_type="partially",
                result="passed",
                result_text="",
            ),
        ],
    }


@pytest.fixture()
def example_source_link_text_non_existent(sphinx_base_dir: Path):
    return [
        {
            "TREQ_ID_200": [
                NeedLink(
                    file=Path("src/bad_implementation.py"),
                    line=2,
                    tag="#" + " req-Id:",
                    need="TREQ_ID_200",
                    full_line="#" + " req-Id: TREQ_ID_200",
                )
            ]
        }
    ]


def make_source_link(needlinks: list[NeedLink]):
    return ", ".join(f"{get_github_link(n)}<>{n.file}:{n.line}" for n in needlinks)


def make_test_link(testlinks: list[DataForTestLink]):
    return ", ".join(f"{get_github_link(n)}<>{n.name}" for n in testlinks)


def compare_json_files(
    file1: Path, expected_file: Path, object_hook: Callable[[dict[str, Any]], Any]
):
    """Golden File tests with a known good file and the one created"""
    with open(file1) as f1:
        json1 = json.load(f1, object_hook=object_hook)
    with open(expected_file) as f2:
        json2 = json.load(f2, object_hook=object_hook)
    assert len(json1) == len(json2), (
        f"{file1}'s lenth are not the same as in the golden file lenght. "
        f"Len of{file1}: {len(json1)}. Len of Golden File: {len(json2)}"
    )
    c1 = Counter(n for n in json1)
    c2 = Counter(n for n in json2)
    assert c1 == c2, (
        f"Testfile does not have same needs as golden file. "
        f"Testfile: {c1}\nGoldenFile: {c2}"
    )


def compare_grouped_json_files(file1: Path, golden_file: Path):
    """Golden File tests with a known good file and the one created"""
    with open(file1) as f1:
        json1 = json.load(f1, object_hook=SourceCodeLinks_TEST_JSON_Decoder)
    with open(golden_file) as f2:
        json2 = json.load(f2, object_hook=SourceCodeLinks_TEST_JSON_Decoder)

    assert len(json1) == len(json2), (
        "Input & Expected have different Lenghts. "
        f"Input: {file1}: {len(json1)}, Expected: {golden_file}: {len(json2)}"
    )

    json1_sorted = sorted(json1, key=lambda x: x.need)
    json2_sorted = sorted(json2, key=lambda x: x.need)

    for item1, item2 in zip(json1_sorted, json2_sorted, strict=False):
        assert item1.need == item2.need, (
            f"Needs don't match: {item1.need} vs {item2.need}"
        )

        # Need to sort it to make sure we compare content not order
        codelinks1_sorted = sorted(item1.links.CodeLinks)
        codelinks2_sorted = sorted(item2.links.CodeLinks)
        assert codelinks1_sorted == codelinks2_sorted, (
            f"CodeLinks don't match for {item1.need}. "
            f"{file1}: {item1.links.CodeLinks}, {golden_file}: {item2.links.CodeLinks}"
        )

        testlinks1_sorted = sorted(item1.links.TestLinks)
        testlinks2_sorted = sorted(item2.links.TestLinks)
        assert testlinks1_sorted == testlinks2_sorted, (
            f"TestLinks don't match for {item1.need}. "
            f"{file1}: {item1.links.TestLinks}, {golden_file}: {item2.links.TestLinks}"
        )


def test_source_link_integration_ok(
    sphinx_app_setup: Callable[[], SphinxTestApp],
    example_source_link_text_all_ok: dict[str, list[NeedLink]],
    example_test_link_text_all_ok: dict[str, list[DataForTestLink]],
    sphinx_base_dir: Path,
    git_repo_setup: Path,
    create_demo_files: None,
):
    """This is a test description"""
    app = sphinx_app_setup()
    try:
        os.environ["BUILD_WORKSPACE_DIRECTORY"] = str(sphinx_base_dir)
        app.build()
        ws_root = find_ws_root()
        assert ws_root is not None
        Needs_Data = SphinxNeedsData(app.env)
        needs_data = {x["id"]: x for x in Needs_Data.get_needs_view().values()}
        compare_json_files(
            app.outdir / "score_source_code_linker_cache.json",
            sphinx_base_dir / ".expected_codelink.json",
            needlink_test_decoder,
        )
        compare_json_files(
            app.outdir / "score_xml_parser_cache.json",
            sphinx_base_dir / ".expected_testlink.json",
            DataForTestLink_JSON_Decoder,
        )
        compare_grouped_json_files(
            app.outdir / "score_scl_grouped_cache.json",
            sphinx_base_dir / ".expected_grouped.json",
        )

        # TODO: Is this actually a good test, or just a weird mock?
        for i in (1, 2, 3):
            treq_id = f"TREQ_ID_{i}"
            assert treq_id in needs_data
            treq_info = needs_data[treq_id]
            print("Needs Data for", treq_id, ":", treq_info)

            # verify codelinks
            expected_code_link = make_source_link(
                example_source_link_text_all_ok[treq_id]
            )
            actual_source_code_link = treq_info.get(
                "source_code_link", "no source link"
            )
            assert expected_code_link == actual_source_code_link, treq_id

            # verify testlinks
            expected_test_link = make_test_link(example_test_link_text_all_ok[treq_id])
            actual_test_code_link = treq_info.get("testlink", "no test link")
            assert expected_test_link == actual_test_code_link, treq_id
    finally:
        app.cleanup()


def test_source_link_integration_non_existent_id(
    sphinx_app_setup: Callable[[], SphinxTestApp],
    example_source_link_text_non_existent: dict[str, list[str]],
    sphinx_base_dir: Path,
    git_repo_setup: Path,
    create_demo_files: None,
):
    """Asserting warning if need not found"""
    app = sphinx_app_setup()
    try:
        app.build()
        warnings = app.warning.getvalue()
        assert (
            "src/bad_implementation.py:2: Could not find TREQ_ID_200 in documentation"
            in warnings
        )
    finally:
        app.cleanup()
