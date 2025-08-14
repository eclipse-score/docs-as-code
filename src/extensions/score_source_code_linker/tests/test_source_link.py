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
import json
import os
import shutil
import subprocess
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest
from pytest import TempPathFactory
from sphinx.testing.util import SphinxTestApp
from sphinx_needs.data import SphinxNeedsData
from test_requirement_links import needlink_test_decoder

from src.extensions.score_source_code_linker import get_github_base_url, get_github_link
from src.extensions.score_source_code_linker.needlinks import NeedLink
from src.helper_lib import find_ws_root


@pytest.fixture()
def sphinx_base_dir(tmp_path_factory: TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("test_git_repo")


@pytest.fixture()
def git_repo_setup(sphinx_base_dir) -> Path:
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
def create_demo_files(sphinx_base_dir, git_repo_setup):
    repo_path = sphinx_base_dir

    # Create some source files with requirement IDs
    source_dir = repo_path / "src"
    source_dir.mkdir()

    # Create source files that contain requirement references
    (source_dir / "implementation1.py").write_text(make_source_1())

    (source_dir / "implementation2.py").write_text(make_source_2())
    (source_dir / "bad_implementation.py").write_text(make_bad_source())
    # Create a docs directory for Sphinx
    docs_dir = repo_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.rst").write_text(basic_needs())
    (docs_dir / "conf.py").write_text(basic_conf())
    curr_dir = Path(__file__).absolute().parent
    # print("CURR_dir", curr_dir)
    shutil.copyfile(curr_dir / "scl_golden_file.json", repo_path / ".golden_file.json")

    # Add files to git and commit
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit with test files"],
        cwd=repo_path,
        check=True,
    )

    # Cleanup
    # Don't know if we need this?
    # os.environ.pop("BUILD_WORKSPACE_DIRECTORY", None)


def make_source_1():
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


def make_source_2():
    return (
        """
# Another implementation file
#"""
        + """ req-Id: TREQ_ID_1
class SomeClass:
    def method(self):
        pass

"""
    )


def make_bad_source():
    return (
        """
#"""
        + """ req-Id: TREQ_ID_200
def This_Should_Error(self):
    pass

"""
    )


def construct_gh_url() -> str:
    gh = get_github_base_url()
    return f"{gh}/blob/"


@pytest.fixture()
def sphinx_app_setup(
    sphinx_base_dir, create_demo_files, git_repo_setup
) -> Callable[[], SphinxTestApp]:
    def _create_app():
        base_dir = sphinx_base_dir
        docs_dir = base_dir / "docs"

        # CRITICAL: Change to a directory that exists and is accessible
        # This fixes the "no such file or directory" error in Bazel
        original_cwd = None
        try:
            original_cwd = os.getcwd()
        except FileNotFoundError:
            # Current working directory doesn't exist, which is the problem
            pass

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
                try:
                    os.chdir(original_cwd)
                except (FileNotFoundError, OSError):
                    # Original directory might not exist anymore in Bazel sandbox
                    pass

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
needs_extra_options = ["source_code_link"]
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
"""


@pytest.fixture()
def example_source_link_text_all_ok(sphinx_base_dir):
    return {
        "TREQ_ID_1": [
            NeedLink(
                file=Path("src/implementation1.py"),
                line=3,
                tag="#" + " req-Id:",
                need="TREQ_ID_1",
                full_line="#" + " req-Id: TREQ_ID_1",
            ),
            NeedLink(
                file=Path("src/implementation2.py"),
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
    }


@pytest.fixture()
def example_source_link_text_non_existent(sphinx_base_dir):
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


def make_source_link(needlinks):
    return ", ".join(f"{get_github_link(n)}<>{n.file}:{n.line}" for n in needlinks)


def compare_json_files(file1: Path, golden_file: Path):
    with open(file1) as f1:
        json1 = json.load(f1, object_hook=needlink_test_decoder)
    with open(golden_file) as f2:
        json2 = json.load(f2, object_hook=needlink_test_decoder)
    assert len(json1) == len(json2), (
        f"{file1}'s lenth are not the same as in the golden file lenght. "
        f"Len of{file1}: {len(json1)}. Len of Golden File: {len(json2)}"
    )
    c1 = Counter(n for n in json1)
    c2 = Counter(n for n in json2)
    assert c1 == c2, (
        "Testfile does not have same needs as golden file. "
        f"Testfile: {c1}\nGoldenFile: {c2}"
    )


def test_source_link_integration_ok(
    sphinx_app_setup: Callable[[], SphinxTestApp],
    example_source_link_text_all_ok: dict[str, list[str]],
    sphinx_base_dir,
    git_repo_setup,
    create_demo_files,
):
    app = sphinx_app_setup()
    try:
        os.environ["BUILD_WORKSPACE_DIRECTORY"] = str(sphinx_base_dir)
        app.build()
        ws_root = find_ws_root()
        if ws_root is None:
            # This should never happen
            pytest.fail(f"WS_root is none. WS_root: {ws_root}")
        Needs_Data = SphinxNeedsData(app.env)
        needs_data = {x["id"]: x for x in Needs_Data.get_needs_view().values()}
        compare_json_files(
            app.outdir / "score_source_code_linker_cache.json",
            sphinx_base_dir / ".golden_file.json",
        )
        # Testing TREQ_ID_1  & TREQ_ID_2
        for i in range(1, 3):
            assert f"TREQ_ID_{i}" in needs_data
            need_as_dict = cast(dict[str, object], needs_data[f"TREQ_ID_{i}"])
            expected_link = make_source_link(
                example_source_link_text_all_ok[f"TREQ_ID_{i}"]
            )
            # extra_options are only available at runtime
            # Compare contents, regardless of order.
            actual_source_code_link = cast(list[str], need_as_dict["source_code_link"])
            assert set(expected_link) == set(actual_source_code_link)
    finally:
        app.cleanup()


def test_source_link_integration_non_existent_id(
    sphinx_app_setup: Callable[[], SphinxTestApp],
    example_source_link_text_non_existent: dict[str, list[str]],
    sphinx_base_dir,
    git_repo_setup,
    create_demo_files,
):
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
