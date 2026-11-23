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
import subprocess
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from score_pytest.attribute_plugin import add_test_properties

from src.helper_lib import get_current_git_hash
from src.helper_lib.repo_info import (
    PLACEHOLDER_URL,
    DefaultRepoInfo,
    RepoInfo,
    clear_git_cache,
    get_github_link,
    load_known_good,
    parse_info_from_known_good,
    resolve_repo,
    split_external_path,
)


@pytest.mark.parametrize(
    "input_path, expected_repo, expected_path",
    [
        # Path starts with "external/" and has a project name
        (
            Path("external/score_docs_as_code+/docs/external/index.md"),
            "score_docs_as_code",
            Path("docs/external/index.md"),
        ),
        # Path does NOT start with "external/"
        (Path("src/main.py"), "host_module", Path("src/main.py")),
        (Path(), "host_module", Path()),
        # Path has "external" elsewhere in the string (should not be removed)
        (
            Path("my_external_data/file.txt"),
            "host_module",
            Path("my_external_data/file.txt"),
        ),
        # Deeply nested path inside an external prefix, repo without '+'
        (Path("external/repo/subfolder/file.py"), "repo", Path("subfolder/file.py")),
        # Path is exactly "external/": Path() drops the trailing '/', so it is
        # no external prefix any more
        (Path("external/"), "host_module", Path("external")),
        # External repo directory without anything inside
        (Path("external/score_x+"), "score_x", Path(".")),
    ],
)
@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_split_external_path(input_path: Path, expected_repo: str, expected_path: Path):
    """Test splitting an exec path into repo name and path inside the repo."""
    assert split_external_path(input_path, local_module="host_module") == (
        expected_repo,
        expected_path,
    )


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
        load_known_good(known_good_json), "score_baselibs"
    )

    assert hash_result == "158fe6a7b791c58f6eac5f7e4662b8db0cf9ac6e"
    assert repo_result == "https://github.com/eclipse-score/baselibs"


def test_parse_info_from_known_good_different_category(known_good_json: Path):
    """Test finding repo in different category."""
    hash_result, repo_result = parse_info_from_known_good(
        load_known_good(known_good_json), "score_docs_as_code"
    )

    assert hash_result == "c1207676afe6cafd25c35d420e73279a799515d8"
    assert repo_result == "https://github.com/eclipse-score/docs-as-code"


def test_parse_info_from_known_good_repo_not_found(known_good_json: Path):
    """Test that KeyError is raised when repo doesn't exist."""
    with pytest.raises(KeyError, match="Module nonexistent not found"):
        parse_info_from_known_good(load_known_good(known_good_json), "nonexistent")


def test_load_known_good_empty_json(tmp_path: Path):
    """Test that it errors when given an empty JSON file."""
    json_file = tmp_path / "example.json"
    _ = json_file.write_text("{}")

    with pytest.raises(
        AssertionError,
        match=f"Known good json at: {json_file} is empty. This is not allowed",
    ):
        _ = load_known_good(json_file)


def test_load_known_good_no_modules_key(tmp_path: Path):
    """Test that assertion works when repo not in top level keys"""
    json_file = tmp_path / "example.json"
    _ = json_file.write_text(
        '{"another_key": {"a": "b"}, "second_key": ["a" , "b", "c"]}'
    )

    with pytest.raises(
        AssertionError,
        match=f"Known good json at: {json_file} is missing the 'modules' key",
    ):
        _ = load_known_good(json_file)


def test_load_known_good_empty_modules(tmp_path: Path):
    """Test that assertion works if repo dictionary is empty"""
    json_file = tmp_path / "emample.json"
    _ = json_file.write_text('{"another_key": {"a": "b"}, "modules": {}}')

    with pytest.raises(
        AssertionError,
        match=f"Known good json at: {json_file} has an empty 'modules' dictionary",
    ):
        _ = load_known_good(json_file)


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
        load_known_good(known_good_json_with_version), "score_baselibs"
    )

    assert hash_result == "v1.2.3"
    assert repo_result == "https://github.com/eclipse-score/baselibs"


def test_parse_info_from_known_good_with_version_different_category(
    known_good_json_with_version: Path,
):
    """Test that 'version' works for a module in a different category."""
    hash_result, repo_result = parse_info_from_known_good(
        load_known_good(known_good_json_with_version), "score_docs_as_code"
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
        parse_info_from_known_good(load_known_good(json_file), "score_baselibs")


# Tests for resolve_repo
def test_resolve_repo_fills_hash_and_url():
    repo = resolve_repo(
        "score_docs_as_code", VALID_KNOWN_GOOD, local_module="host_module"
    )
    assert repo == RepoInfo(
        name="score_docs_as_code",
        hash="c1207676afe6cafd25c35d420e73279a799515d8",
        url="https://github.com/eclipse-score/docs-as-code",
    )


@pytest.mark.parametrize(
    ("repo_name", "known_good"),
    [
        ("score_docs_as_code", VALID_KNOWN_GOOD),
        ("", VALID_KNOWN_GOOD),
        ("dependency", None),
    ],
)
def test_resolve_repo_nothing_to_look_up(
    repo_name: str, known_good: dict[str, object] | None
):
    """Keep existing metadata when there is no external pin to look up."""
    assert not resolve_repo(repo_name, known_good, local_module="score_docs_as_code")


def test_resolve_repo_unknown_repo_raises():
    with pytest.raises(KeyError, match="Module nonexistent not found"):
        _ = resolve_repo("nonexistent", VALID_KNOWN_GOOD, local_module="host_module")


# Tests for get_github_link
def test_get_github_link_with_hash():
    """Combo build: hash and url come from the repo info (known_good)."""
    metadata = RepoInfo(
        name="project_name",
        url="https://github.com/eclipse/project",
        hash="commit123abc",
    )

    result = get_github_link(metadata, Path("docs/index.rst"), 100)

    assert (
        result
        == "https://github.com/eclipse/project/blob/commit123abc/docs/index.rst#L100"
    )


def test_get_github_link_with_line_zero():
    metadata = RepoInfo(
        name="test_repo", url="https://github.com/test/repo", hash="hash123"
    )

    result = get_github_link(metadata, Path("file.py"), 0)

    assert result == "https://github.com/test/repo/blob/hash123/file.py#L0"


def test_get_github_link_plain_links_gives_placeholder():
    """Bazel sandbox builds: placeholder, even with full repo info."""
    metadata = RepoInfo(name="some_repo", url="https://github.com/org/repo", hash="h")

    result = get_github_link(metadata, Path("src/example.py"), 42, plain_links=True)

    assert result == f"{PLACEHOLDER_URL}/src/example.py#L42"


def test_get_github_link_no_repo_gives_placeholder_with_defaults():
    """Testcase without repo info and without file/line."""
    result = get_github_link(None, None, None)

    assert result == f"{PLACEHOLDER_URL}/<placeholder_file>#L1"


def test_get_github_link_git_without_remote_gives_none(tmp_path: Path):
    """Local build where git has no remote: no URL, the caller falls back."""
    _ = subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)

    assert get_github_link(DefaultRepoInfo(), "a.py", 1, git_root=tmp_path) is None


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


def test_git_lookup_is_cached_until_cleared(git_repo: Path) -> None:
    """Git is asked once per build. clear_git_cache picks up a new commit."""
    clear_git_cache()
    first = get_github_link(DefaultRepoInfo(), "a.py", 1, git_root=git_repo)
    old_hash = get_current_git_hash(git_repo)

    _ = subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "next"], cwd=git_repo, check=True
    )
    new_hash = get_current_git_hash(git_repo)

    # Same build: still the cached hash
    assert get_github_link(DefaultRepoInfo(), "a.py", 1, git_root=git_repo) == first
    assert first is not None and old_hash in first

    # Next build
    clear_git_cache()
    second = get_github_link(DefaultRepoInfo(), "a.py", 1, git_root=git_repo)
    assert second is not None and new_hash in second


def test_get_github_link_with_real_repo(git_repo: Path) -> None:
    """
    Test generating GitHub link without url/hash.
    """
    metadata = RepoInfo(name="some_repo", url="", hash="")

    result = get_github_link(
        metadata,
        Path("src/example.py"),
        42,
        git_root=git_repo,
        local_module="some_repo",
    )
    assert result is not None

    # Should contain the base URL, hash, file path, and line number
    assert "https://github.com/test-user/test-repo/blob/" in result
    assert "src/example.py#L42" in result

    # Verify the hash is actually from the repo
    hash_from_link = result.split("/blob/")[1].split("/")[0]
    actual_hash = get_current_git_hash(git_repo)
    assert hash_from_link == actual_hash

    # An unpinned dependency cannot use the same checkout.
    assert (
        get_github_link(
            metadata, Path("src/example.py"), 42, git_root=git_repo, local_module="host"
        )
        is None
    )


def test_complete_workflow(known_good_json: Path):
    """Test complete workflow from path to GitHub link."""

    # Parse path
    path = Path("external/score_docs_as_code+/src/helper_lib/test_helper_lib.py")
    repo_name, _ = split_external_path(path, local_module="host_module")
    assert repo_name == "score_docs_as_code"

    # Get metadata
    hash_val, repo_url = parse_info_from_known_good(
        load_known_good(known_good_json), repo_name
    )
    assert hash_val == "c1207676afe6cafd25c35d420e73279a799515d8"
    assert repo_url == "https://github.com/eclipse-score/docs-as-code"

    # Generate link
    metadata = RepoInfo(name=repo_name, url=repo_url, hash=hash_val)

    result = get_github_link(metadata, Path("src/helper_lib/test_helper_lib.py"), 75)

    assert (
        result
        == "https://github.com/eclipse-score/docs-as-code/blob/c1207676afe6cafd25c35d420e73279a799515d8/src/helper_lib/test_helper_lib.py#L75"
    )
