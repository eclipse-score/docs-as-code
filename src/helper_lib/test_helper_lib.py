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
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from src.helper_lib import (
    get_current_git_hash,
    get_github_repo_info,
    get_runfiles_dir,
    parse_remote_git_output,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def git_repo(temp_dir: Path) -> Path:
    """Create a real git repository for testing."""
    git_dir: Path = temp_dir / "test_repo"
    git_dir.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=git_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=git_dir, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=git_dir, check=True)

    # Create a test file and commit
    test_file: Path = git_dir / "test_file.py"
    test_file.write_text("# Test file\nprint('hello')\n")
    subprocess.run(["git", "add", "."], cwd=git_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=git_dir, check=True)

    # Add a remote
    subprocess.run(
        ["git", "remote", "add", "origin", "git@github.com:test-user/test-repo.git"],
        cwd=git_dir,
        check=True,
    )
    return git_dir


@pytest.fixture
def git_repo_multiple_remotes(temp_dir: Path) -> Path:
    """Create a git repository with multiple remotes for testing."""
    git_dir: Path = temp_dir / "test_repo_multiple"
    git_dir.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=git_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=git_dir, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=git_dir, check=True)

    # Create a test file and commit
    test_file: Path = git_dir / "test_file.py"
    test_file.write_text("# Test file\nprint('hello')\n")
    subprocess.run(["git", "add", "."], cwd=git_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=git_dir, check=True)

    # Add multiple remotes
    subprocess.run(
        ["git", "remote", "add", "upstream", "git@github.com:upstream/test-repo.git"],
        cwd=git_dir,
        check=True,
    )
    subprocess.run(
        ["git", "remote", "add", "origin", "git@github.com:test-user/test-repo.git"],
        cwd=git_dir,
        check=True,
    )

    return git_dir


@pytest.fixture
def git_repo_with_https_remote(temp_dir: Path) -> Path:
    """Create a git repository with HTTPS remote for testing."""
    git_dir: Path = temp_dir / "test_repo_https"
    git_dir.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=git_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=git_dir, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=git_dir, check=True)

    # Create a test file and commit
    test_file: Path = git_dir / "test_file.py"
    test_file.write_text("# Test file\nprint('hello')\n")
    subprocess.run(["git", "add", "."], cwd=git_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=git_dir, check=True)

    # Add HTTPS remote
    subprocess.run(
        [
            "git",
            "remote",
            "add",
            "origin",
            "https://github.com/test-user/test-repo.git",
        ],
        cwd=git_dir,
        check=True,
    )

    return git_dir


# Test error handling
def test_git_operations_with_no_commits(temp_dir: Path):
    """Test git operations on repo with no commits."""
    git_dir: Path = temp_dir / "empty_repo"
    git_dir.mkdir()

    # Initialize git repo but don't commit anything
    subprocess.run(["git", "init"], cwd=git_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=git_dir, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=git_dir, check=True)

    os.chdir(Path(git_dir).absolute())
    # Should raise an exception when trying to get hash
    with pytest.raises(subprocess.CalledProcessError):
        get_current_git_hash(git_dir)


def test_git_repo_with_no_remotes(temp_dir: Path):
    """Test git repository with no remotes."""
    git_dir: Path = temp_dir / "no_remote_repo"
    git_dir.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=git_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=git_dir, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=git_dir, check=True)

    # Create a test file and commit
    test_file: Path = git_dir / "test_file.py"
    test_file.write_text("# Test file\nprint('hello')\n")
    subprocess.run(["git", "add", "."], cwd=git_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=git_dir, check=True)
    os.chdir(git_dir)

    # Should raise an exception when trying to get repo info
    with pytest.raises(AssertionError):
        get_github_repo_info(git_dir)


# Test git-related functions
def test_parse_git_output_ssh_format():
    """Test parsing git remote output in SSH format."""
    git_line = "origin	git@github.com:test-user/test-repo.git (fetch)"
    result = parse_remote_git_output(git_line)
    assert result == "test-user/test-repo"


def test_parse_git_output_https_format():
    """Test parsing git remote output in HTTPS format."""
    git_line = "origin	https://github.com/test-user/test-repo.git (fetch)"
    result = parse_remote_git_output(git_line)
    assert result == "test-user/test-repo"


def test_parse_git_output_ssh_format_without_git_suffix():
    """Test parsing git remote output in SSH format without .git suffix."""
    git_line = "origin	git@github.com:test-user/test-repo (fetch)"
    result = parse_remote_git_output(git_line)
    assert result == "test-user/test-repo"


def test_parse_git_output_invalid_format():
    """Test parsing invalid git remote output."""
    git_line = "invalid"
    result = parse_remote_git_output(git_line)
    assert result == ""


def test_parse_git_output_empty_string():
    """Test parsing empty git remote output."""
    git_line = ""
    result = parse_remote_git_output(git_line)
    assert result == ""


def test_get_github_repo_info_ssh_remote(git_repo: Path):
    """Test getting GitHub repository information with SSH remote."""
    result = get_github_repo_info(git_repo)
    assert result == "test-user/test-repo"


def test_get_github_repo_info_https_remote(git_repo_with_https_remote: Path):
    """Test getting GitHub repository information with HTTPS remote."""
    result = get_github_repo_info(git_repo_with_https_remote)
    assert result == "test-user/test-repo"


def test_get_github_repo_info_multiple_remotes(git_repo_multiple_remotes: Path):
    """Test GitHub repo info retrieval with multiple remotes (origin preferred)."""
    result = get_github_repo_info(git_repo_multiple_remotes)
    assert result == "test-user/test-repo"


def test_get_current_git_hash(git_repo: Path):
    """Test getting current git hash."""
    result = get_current_git_hash(git_repo)

    # Verify it's a valid git hash (40 hex characters)
    assert len(result) == 40
    assert all(c in "0123456789abcdef" for c in result)


def test_get_current_git_hash_invalid_repo(temp_dir: Path):
    """Test getting git hash from invalid repository."""
    with pytest.raises(subprocess.CalledProcessError):
        get_current_git_hash(temp_dir)


def test_runfiles_dir_found(temp_dir: Path):
    """Test Runfiles dir found when provided and it's actually there"""
    runfiles_dir = temp_dir / "runfiles_here"
    runfiles_dir.mkdir(parents=True)
    os.environ["RUNFILES_DIR"] = str(runfiles_dir)
    os.chdir(runfiles_dir)
    result = get_runfiles_dir()
    assert Path(result) == runfiles_dir
    os.environ.pop("RUNFILES_DIR", None)


def test_runfiles_dir_missing_triggers_exit(temp_dir: Path):
    """Testing if the runfiles exit via sys.exit if runfiles are set but don't exist"""
    runfiles_dir = temp_dir / "does_not_exist"
    os.environ["RUNFILES_DIR"] = str(runfiles_dir)
    with pytest.raises(SystemExit) as e:
        get_runfiles_dir()
    assert "Could not find runfiles_dir" in str(e.value)
    os.environ.pop("RUNFILES_DIR", None)


def test_git_root_search_success(git_repo: Path, monkeypatch: pytest.MonkeyPatch):
    """Testing if Git Root can be found successfully with unset RUNFILES"""
    docs_dir = git_repo / "docs"
    runfiles_dir = git_repo / "bazel-bin" / "ide_support.runfiles"
    docs_dir.mkdir()
    runfiles_dir.mkdir(parents=True)
    os.environ.pop("RUNFILES_DIR", None)

    # Have to monkeypatch in order to allow us to test
    # the 'else' path inside 'get_runfiles_dir'
    monkeypatch.setattr(Path, "cwd", lambda: docs_dir)
    result = get_runfiles_dir()
    assert Path(result) == runfiles_dir
    os.environ.pop("RUNFILES_DIR", None)


def test_git_root_search_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """
    Test fallback when no .git is found (should sys.exit).
    """
    nowhere = tmp_path / "nowhere"
    nowhere.mkdir(parents=True)
    os.environ.pop("RUNFILES_DIR", None)
    # Have to monkeypatch in order to allow us to
    # test the 'else' path inside 'get_runfiles_dir'
    monkeypatch.setattr(Path, "cwd", lambda: nowhere)
    with pytest.raises(SystemExit) as excinfo:
        get_runfiles_dir()
    assert "Could not find git root" in str(excinfo.value)
    os.environ.pop("RUNFILES_DIR", None)
