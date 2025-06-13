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
from collections import defaultdict
from collections.abc import Callable
from gettext import find
from pathlib import Path

import pytest
import logging
from pytest import TempPathFactory
from src.extensions.score_source_code_linker.parse_source_files import (
    get_github_base_url,
    find_git_root,
    get_github_repo_info,
    extract_requirements,
    get_git_hash,
    parse_git_output,
    logger as scl_logger,
)


@pytest.fixture(scope="session")
def create_tmp_files(tmp_path_factory: TempPathFactory) -> Path:
    root_dir: Path = tmp_path_factory.mktemp("test_root")
    test_file_contents = """


def implementation_1():
    pass

# req-Id: TEST_REQ__LINKED_ID
def implementation_tagged():
    pass

# req-traceability: TEST_REQ__LINKED_TRACE
def implementation_tagged_2():
    pass
"""
    with open(root_dir / "testfile.txt", "w") as f:
        f.write(test_file_contents)

    test_file_contents2 = """

# req-Id: TEST_REQ__LINKED_DIFFERENT_FILE
def implementation_separate():
    pass
"""
    with open(root_dir / "testfile2.txt", "w") as f:
        f.write(test_file_contents2)
    test_file_contents3 = """

def implementation_14():
    pass

def implementation_4():
    pass

# comments
def implementation_4():
    pass
        """
    with open(root_dir / "testfile3.txt", "w") as f:
        f.write(test_file_contents3)
    return root_dir


def dummy_git_hash_func(input: str) -> Callable[[str], str]:
    return lambda _: input


def test_extract_requirements(create_tmp_files: Path):
    root_dir = create_tmp_files
    github_base_url = get_github_base_url()
    results_dict1 = extract_requirements(
        str(root_dir / "testfile.txt"), github_base_url, dummy_git_hash_func("no-hash")
    )
    expected_dict1: dict[str, list[str]] = defaultdict(list)
    expected_dict1["TEST_REQ__LINKED_ID"].append(
        f"{github_base_url}/blob/no-hash/{root_dir}/testfile.txt#L7"
    )
    expected_dict1["TEST_REQ__LINKED_TRACE"].append(
        f"{github_base_url}/blob/no-hash/{root_dir}/testfile.txt#L11"
    )

    # Assumed random hash here to test if passed correctly
    results_dict2 = extract_requirements(
        str(root_dir / "testfile2.txt"),
        github_base_url,
        dummy_git_hash_func("aacce4887ceea1f884135242a8c182db1447050"),
    )
    expected_dict2: dict[str, list[str]] = defaultdict(list)
    expected_dict2["TEST_REQ__LINKED_DIFFERENT_FILE"].append(
        f"{github_base_url}/blob/aacce4887ceea1f884135242a8c182db1447050/{root_dir}/testfile2.txt#L3"
    )

    results_dict3 = extract_requirements(
        str(root_dir / "testfile3.txt"), github_base_url
    )
    expected_dict3: dict[str, list[str]] = defaultdict(list)

    # if there is no git-hash returned from command.
    # This happens if the file is new and not committed yet.
    results_dict4 = extract_requirements(
        str(root_dir / "testfile2.txt"), github_base_url, dummy_git_hash_func("")
    )
    expected_dict4: dict[str, list[str]] = defaultdict(list)
    expected_dict4["TEST_REQ__LINKED_DIFFERENT_FILE"].append(
        f"{github_base_url}/blob//{root_dir}/testfile2.txt#L3"
    )

    assert results_dict1 == expected_dict1
    assert results_dict2 == expected_dict2
    assert results_dict3 == expected_dict3
    assert results_dict4 == expected_dict4


def test_get_git_hash():
    assert get_git_hash("testfile.x") == "file_not_found"
    assert get_git_hash("") == "file_not_found"


# These tests aren't great / exhaustive, but an okay first step into the right direction.


def test_get_github_repo_info():
    # I'd argue the happy path is tested with the other ones?
    with pytest.raises(AssertionError):
        get_github_repo_info(Path("."))


git_test_data_ok = [
    (
        "origin  https://github.com/eclipse-score/test-repo.git (fetch)",
        "eclipse-score/test-repo",
    ),
    (
        "origin  git@github.com:eclipse-score/test-repo.git (fetch)",
        "eclipse-score/test-repo",
    ),
    ("origin  git@github.com:eclipse-score/test-repo.git", "eclipse-score/test-repo"),
    ("upstream  git@github.com:upstream/repo.git (fetch)", "upstream/repo"),
]


@pytest.mark.parametrize("input,output", git_test_data_ok)
def test_parse_git_output_ok(input, output):
    assert output == parse_git_output(input)


git_test_data_bad = [
    ("origin ", ""),
    (
        "    ",
        "",
    ),
]


@pytest.mark.parametrize("input,output", git_test_data_bad)
def test_parse_git_output_bad(caplog, input, output):
    with caplog.at_level(logging.WARNING, logger=scl_logger.name):
        result = parse_git_output(input)
    assert len(caplog.messages) == 1
    assert caplog.records[0].levelname == "WARNING"
    assert (
        f"Got wrong input line from 'get_github_repo_info'. Input: {input}. Expected example: 'origin git@github.com:user/repo.git'"
        in caplog.records[0].message
    )
    assert output == result


def test_get_github_base_url():
    # Not really a great test imo.
    git_root = find_git_root()
    repo = get_github_repo_info(git_root)
    expected = f"https://github.com/{repo}"
    actual = get_github_base_url()
    assert expected == actual
