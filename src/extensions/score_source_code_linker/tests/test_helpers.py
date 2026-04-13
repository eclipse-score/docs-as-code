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
import subprocess
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from src.extensions.score_source_code_linker.helpers import (
    get_github_link,
    get_github_link_from_json,
    parse_info_from_known_good,
    parse_repo_name_from_path,
)
from src.extensions.score_source_code_linker.needlinks import DefaultNeedLink
from src.extensions.score_source_code_linker.repo_source_links import RepoInfo
from src.helper_lib import get_current_git_hash

#              ╭──────────────────────────────────────────────────────────╮
#              │          Tests for parse_repo_name_from_path             │
#              ╰──────────────────────────────────────────────────────────╯


def test_parse_repo_name_from_external_path():
    """Test parsing repo name from external/combo build path."""
    path = Path("external/score_docs_as_code+/src/helper_lib/test_helper_lib.py")

    result = parse_repo_name_from_path(path)

    assert result == "score_docs_as_code"


def test_parse_repo_name_from_external_path_2():
    """Test that an extra 'external' in the path does not change the output"""
    path = Path(
        "external/score_docs_as_code+/src/external/helper_lib/test_helper_lib.py"
    )

    result = parse_repo_name_from_path(path)

    assert result == "score_docs_as_code"


def test_parse_repo_name_from_local_path():
    """Test parsing repo name from local build path."""
    path = Path("src/helper_lib/test_helper_lib.py")

    result = parse_repo_name_from_path(path)

    assert result == "local_repo"


def test_parse_repo_name_from_empty_path():
    """Test parsing repo name from an empty path."""
    path = Path("")

    result = parse_repo_name_from_path(path)

    assert result == "local_repo"


def test_parse_repo_name_without_plus_suffix():
    """
    Test parsing external repo without plus suffix.
    This should never happen (due to bazel adding the '+')
    But testing this edge case anyway
    """
    path = Path("external/repo_without_plus/file.py")

    result = parse_repo_name_from_path(path)

    assert result == "repo_without_plus"


#              ╭──────────────────────────────────────────────────────────╮
#              │                PARSE INFO FROM KNOWN GOOD                │
#              ╰──────────────────────────────────────────────────────────╯


# Example of a minimal valid known_good.json structure
VALID_KNOWN_GOOD = {
    "modules": {
        "target_sw": {
            "score_baselibs": {
                "repo": "https://github.com/eclipse-score/baselibs.git",
                "hash": "158fe6a7b791c58f6eac5f7e4662b8db0cf9ac6e",
            },
            "score_communication": {
                "repo": "https://github.com/eclipse-score/communication.git",
                "hash": "56448a5589a5f7d3921b873e8127b824a8c1ca95",
            },
        },
        "tooling": {
            "score_docs_as_code": {
                "repo": "https://github.com/eclipse-score/docs-as-code.git",
                "hash": "c1207676afe6cafd25c35d420e73279a799515d8",
            }
        },
    }
}

#             ────────────────────────────────────────────────────────────
#            ──────────────────────[ Test Functions ]──────────────────────


@pytest.fixture
def known_good_json(tmp_path: Path):
    """Fixture providing a valid known_good.json file."""
    json_file = tmp_path / "known_good.json"
    _ = json_file.write_text(json.dumps(VALID_KNOWN_GOOD))
    return json_file


# Tests for parse_info_from_known_good
def test_parse_info_from_known_good_happy_path(known_good_json: Path):
    """Test parsing repo info from valid known_good.json."""
    hash_result, repo_result = parse_info_from_known_good(
        known_good_json, "score_baselibs"
    )

    assert hash_result == "158fe6a7b791c58f6eac5f7e4662b8db0cf9ac6e"
    assert repo_result == "https://github.com/eclipse-score/baselibs"


def test_parse_info_from_known_good_different_category(known_good_json: Path):
    """Test finding repo in different category."""
    hash_result, repo_result = parse_info_from_known_good(
        known_good_json, "score_docs_as_code"
    )

    assert hash_result == "c1207676afe6cafd25c35d420e73279a799515d8"
    assert repo_result == "https://github.com/eclipse-score/docs-as-code"


def test_parse_info_from_known_good_repo_not_found(known_good_json: Path):
    """Test that KeyError is raised when repo doesn't exist."""
    with pytest.raises(KeyError, match="Module nonexistent not found"):
        parse_info_from_known_good(known_good_json, "nonexistent")


def test_parse_info_from_known_good_empty_json(tmp_path: Path):
    """Test that it errors when given an empty JSON file."""
    json_file = tmp_path / "example.json"
    _ = json_file.write_text("{}")

    with pytest.raises(
        AssertionError,
        match=f"Known good json at: {json_file} is empty. This is not allowed",
    ):
        parse_info_from_known_good(json_file, "any_repo")


def test_parse_info_from_known_good_no_repo_in_json(tmp_path: Path):
    """Test that assertion works when repo not in top level keys"""
    json_file = tmp_path / "example.json"
    _ = json_file.write_text(
        '{"another_key": {"a": "b"}, "second_key": ["a" , "b", "c"]}'
    )

    with pytest.raises(
        AssertionError,
        match=f"Known good json at: {json_file} is missing the 'modules' key",
    ):
        parse_info_from_known_good(json_file, "any_repo")


def test_parse_info_from_known_good_empty_repo_dict_in_json(tmp_path: Path):
    """Test that assertion works if repo dictionary is empty"""
    json_file = tmp_path / "emample.json"
    _ = json_file.write_text('{"another_key": {"a": "b"}, "modules": {}}')

    with pytest.raises(
        AssertionError,
        match=f"Known good json at: {json_file} has an empty 'modules' dictionary",
    ):
        parse_info_from_known_good(json_file, "any_repo")


VALID_KNOWN_GOOD_WITH_VERSION = {
    "modules": {
        "target_sw": {
            "score_baselibs": {
                "repo": "https://github.com/eclipse-score/baselibs.git",
                "version": "v1.2.3",
            },
        },
        "tooling": {
            "score_docs_as_code": {
                "repo": "https://github.com/eclipse-score/docs-as-code.git",
                "version": "4.3-alpha",
            }
        },
    }
}


@pytest.fixture
def known_good_json_with_version(tmp_path: Path):
    """Providing a known_good.json file that uses 'version' instead of 'hash'."""
    json_file = tmp_path / "known_good_version.json"
    _ = json_file.write_text(json.dumps(VALID_KNOWN_GOOD_WITH_VERSION))
    return json_file


def test_parse_info_from_known_good_with_version(known_good_json_with_version: Path):
    """Test that 'version' is accepted as a fallback when 'hash' is absent."""
    hash_result, repo_result = parse_info_from_known_good(
        known_good_json_with_version, "score_baselibs"
    )

    assert hash_result == "v1.2.3"
    assert repo_result == "https://github.com/eclipse-score/baselibs"


def test_parse_info_from_known_good_with_version_different_category(
    known_good_json_with_version: Path,
):
    """Test that 'version' works for a module in a different category."""
    hash_result, repo_result = parse_info_from_known_good(
        known_good_json_with_version, "score_docs_as_code"
    )

    assert hash_result == "4.3-alpha"
    assert repo_result == "https://github.com/eclipse-score/docs-as-code"


def test_parse_info_from_known_good_neither_hash_nor_version(tmp_path: Path):
    """Test that KeyError is raised when neither 'hash' nor 'version' is present."""
    json_file = tmp_path / "broken.json"
    _ = json_file.write_text(
        json.dumps(
            {
                "modules": {
                    "target_sw": {
                        "score_baselibs": {
                            "repo": "https://github.com/eclipse-score/baselibs.git",
                        }
                    }
                }
            }
        )
    )

    msg = "score_baselibs has neither 'hash' nor 'version'"
    with pytest.raises(KeyError, match=msg):
        parse_info_from_known_good(json_file, "score_baselibs")


# Tests for get_github_link_from_json
def test_get_github_link_from_json_happy_path():
    """
    Test generating GitHub link with fully filled metadata
    =>this happens in combo builds
    """
    metadata = RepoInfo(
        name="project_name",
        url="https://github.com/eclipse/project",
        hash="commit123abc",
    )

    link = DefaultNeedLink()
    link.file = Path("docs/index.rst")
    link.line = 100

    result = get_github_link_from_json(metadata, link)

    assert (
        result
        == "https://github.com/eclipse/project/blob/commit123abc/docs/index.rst#L100"
    )


def test_get_github_link_from_json_with_none_link():
    """Test that None link creates DefaultNeedLink."""
    metadata = RepoInfo(
        name="test_repo", url="https://github.com/test/repo", hash="def456"
    )

    result = get_github_link_from_json(metadata, None)

    assert result.startswith("https://github.com/test/repo/blob/def456/")
    assert "#L" in result


def test_get_github_link_from_json_with_line_zero():
    """Test generating link with line number 0."""
    metadata = RepoInfo(
        name="test_repo", url="https://github.com/test/repo", hash="hash123"
    )

    link = DefaultNeedLink()
    link.file = Path("file.py")
    link.line = 0

    result = get_github_link_from_json(metadata, link)

    assert result == "https://github.com/test/repo/blob/hash123/file.py#L0"


# Tests for get_github_link
def test_get_github_link_with_hash():
    """Test get_github_link uses json method when hash is present."""
    metadata = RepoInfo(
        name="some_repo", url="https://github.com/org/repo", hash="commit_hash_123"
    )

    link = DefaultNeedLink()
    link.file = Path("src/example.py")
    link.line = 42

    result = get_github_link(metadata, link)

    assert (
        result == "https://github.com/org/repo/blob/commit_hash_123/src/example.py#L42"
    )


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def git_repo(temp_dir: Path) -> Path:
    """Create a real git repository for testing."""
    git_dir: Path = temp_dir / "test_repo"
    git_dir.mkdir()

    # Initialize git repo
    _ = subprocess.run(["git", "init"], cwd=git_dir, check=True, capture_output=True)
    _ = subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=git_dir, check=True
    )
    _ = subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=git_dir, check=True
    )

    # Create a test file and commit
    test_file: Path = git_dir / "test_file.py"
    _ = test_file.write_text("# Test file\nprint('hello')\n")
    _ = subprocess.run(["git", "add", "."], cwd=git_dir, check=True)
    _ = subprocess.run(
        ["git", "commit", "-m", "Initial commit"], cwd=git_dir, check=True
    )

    # Add a remote
    _ = subprocess.run(
        ["git", "remote", "add", "origin", "git@github.com:test-user/test-repo.git"],
        cwd=git_dir,
        check=True,
    )
    return git_dir


def test_get_github_link_with_real_repo(git_repo: Path) -> None:
    """
    Test generating GitHub link without url/hash.
    This expects to be in a git repo
    """
    metadata = RepoInfo(name="some_repo", url="", hash="")

    link = DefaultNeedLink()
    link.file = Path("src/example.py")
    link.line = 42

    # Have to change directories in order to ensure that we get the right/any .git file
    os.chdir(Path(git_repo).absolute())
    # ADAPTED: Using get_github_link_from_git for direct local repo testing
    result = get_github_link(metadata, link)

    # Should contain the base URL, hash, file path, and line number
    assert "https://github.com/test-user/test-repo/blob/" in result
    assert "src/example.py#L42" in result

    # Verify the hash is actually from the repo
    hash_from_link = result.split("/blob/")[1].split("/")[0]
    actual_hash = get_current_git_hash(git_repo)
    assert hash_from_link == actual_hash


def test_complete_workflow(known_good_json: Path):
    """Test complete workflow from path to GitHub link."""

    # Parse path
    path = Path("external/score_docs_as_code+/src/helper_lib/test_helper_lib.py")
    repo_name = parse_repo_name_from_path(path)
    assert repo_name == "score_docs_as_code"

    # Get metadata
    hash_val, repo_url = parse_info_from_known_good(known_good_json, repo_name)
    assert hash_val == "c1207676afe6cafd25c35d420e73279a799515d8"
    assert repo_url == "https://github.com/eclipse-score/docs-as-code"

    # Generate link
    metadata = RepoInfo(name=repo_name, url=repo_url, hash=hash_val)
    link = DefaultNeedLink()
    link.file = Path("src/helper_lib/test_helper_lib.py")
    link.line = 75

    result = get_github_link(metadata, link)

    assert (
        result
        == "https://github.com/eclipse-score/docs-as-code/blob/c1207676afe6cafd25c35d420e73279a799515d8/src/helper_lib/test_helper_lib.py#L75"
    )
