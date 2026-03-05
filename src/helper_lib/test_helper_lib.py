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
from pytest import MonkeyPatch

from src.helper_lib import (
    config_setdefault,
    get_current_git_hash,
    get_github_repo_info,
    get_runfiles_dir,
    parse_filename,
    parse_remote_git_output,
)


class _FakeConfig:
    """Minimal stand-in for sphinx.config.Config."""

    def __init__(self, raw: dict):
        self._raw_config = raw


def test_config_setdefault_sets_when_not_in_raw_config():
    cfg = _FakeConfig(raw={})
    config_setdefault(cfg, "html_copy_source", False)  # pyright: ignore [reportArgumentType]
    assert cfg.html_copy_source is False  # pyright: ignore [reportAttributeAccessIssue]


def test_config_setdefault_does_not_overwrite_user_value():
    cfg = _FakeConfig(raw={"html_copy_source": True})
    cfg.html_copy_source = True  # pyright: ignore[reportAttributeAccessIssue]
    config_setdefault(cfg, "html_copy_source", False)  # pyright: ignore [reportArgumentType]
    assert cfg.html_copy_source is True  # pyright: ignore[reportAttributeAccessIssue]


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


#       ╭──────────────────────────────────────────────────────────────────────────────╮
#       │    GENERATED TESTS. Manually reviewed though may need further tweaking to    │
#       │                       catch more branches / edge cases                       │
#       ╰──────────────────────────────────────────────────────────────────────────────╯


# COMBO BUILD TESTS (External Modules)

def test_external_module_basic(tmp_path: Path) -> None:
    """Test parsing a file from an external module (combo build)."""
    # Simulate bazel cache structure
    bazel_cache = tmp_path / ".cache" / "bazel" / "_bazel_user" / "58de169282104bb8c73a59023f615bcd"
    sandbox_base = bazel_cache / "sandbox" / "linux-sandbox" / "42" / "execroot" / "_main"
    external_dir = sandbox_base / "external"
    external_dir.mkdir(parents=True, exist_ok=True)

    runfiles_dir = sandbox_base / "bazel-out" / "k8-fastbuild" / "bin" / "ide_support.runfiles"
    runfiles_dir.mkdir(parents=True, exist_ok=True)

    filepath = Path("external/score_docs_as_code+/src/tests/testfile.py")

    prefix, module_name, file_path, file_name = parse_filename(filepath, runfiles_dir)

    # Verify all components
    assert module_name == "score_docs_as_code"
    assert file_path == "src/tests"
    assert file_name == "testfile.py"

    # Verify prefix points to the bazel cache external directory (NOT sandbox/execroot)
    # The function extracts the path up to but not including /sandbox
    expected_prefix = bazel_cache / "external"
    assert prefix == expected_prefix


def test_external_module_root_file(tmp_path: Path) -> None:
    """Test parsing a file at the root of an external module."""
    bazel_cache = tmp_path / ".cache" / "bazel" / "_bazel_user" / "abc123"
    sandbox_base = bazel_cache / "sandbox" / "linux" / "1" / "execroot" / "_main"
    external_dir = sandbox_base / "external"
    external_dir.mkdir(parents=True, exist_ok=True)

    runfiles_dir = sandbox_base / "bazel-bin" / "test.runfiles"
    runfiles_dir.mkdir(parents=True, exist_ok=True)

    filepath = Path("external/some_lib+/BUILD.bazel")

    prefix, module_name, file_path, file_name = parse_filename(filepath, runfiles_dir)

    assert module_name == "some_lib"
    assert file_path == ""
    assert file_name == "BUILD.bazel"

    # Verify prefix points to bazel cache external directory
    expected_prefix = bazel_cache / "external"
    assert prefix == expected_prefix


def test_external_module_special_chars(tmp_path: Path) -> None:
    """Test parsing module names with hyphens, underscores, and multiple plus signs."""
    bazel_cache = tmp_path / ".cache" / "bazel" / "_bazel_test" / "hash123"
    sandbox_base = bazel_cache / "sandbox" / "worker" / "99" / "execroot" / "_main"
    external_dir = sandbox_base / "external"
    external_dir.mkdir(parents=True, exist_ok=True)

    runfiles_dir = sandbox_base / "bin" / "test.runfiles"
    runfiles_dir.mkdir(parents=True, exist_ok=True)

    filepath = Path("external/my-special_module+v2+/src/file.py")

    prefix, module_name, file_path, file_name = parse_filename(filepath, runfiles_dir)

    # removesuffix only removes the trailing '+'
    assert module_name == "my-special_module+v2"
    assert file_path == "src"
    assert file_name == "file.py"

    # Verify prefix
    expected_prefix = bazel_cache / "external"
    assert prefix == expected_prefix


# LOCAL BUILD TESTS (With Workspace)

def test_local_with_workspace(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Test parsing a local file when workspace root is available."""
    workspace = tmp_path / "my_project"
    workspace.mkdir()
    git_dir = workspace / ".git"
    git_dir.mkdir()

    runfiles_dir = tmp_path / "bazel-bin" / "ide_support.runfiles"
    runfiles_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("BUILD_WORKSPACE_DIRECTORY", str(workspace))

    filepath = Path("src/tests/test_example.py")

    prefix, module_name, file_path, file_name = parse_filename(filepath, runfiles_dir)

    assert module_name == ""
    assert file_path == "src/tests"
    assert file_name == "test_example.py"

    # Verify prefix is the git root (workspace)
    assert prefix == workspace
    assert prefix.exists()
    assert (prefix / ".git").exists()


def test_local_root_file_with_workspace(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Test parsing a file at the repository root."""
    workspace = tmp_path / "repo"
    workspace.mkdir()
    git_dir = workspace / ".git"
    git_dir.mkdir()

    runfiles_dir = tmp_path / "bazel-bin" / "build.runfiles"
    runfiles_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("BUILD_WORKSPACE_DIRECTORY", str(workspace))

    filepath = Path("BUILD.bazel")

    prefix, module_name, file_path, file_name = parse_filename(filepath, runfiles_dir)

    assert module_name == ""
    assert file_path == ""
    assert file_name == "BUILD.bazel"

    # Verify prefix is the workspace root
    assert prefix == workspace
    assert (prefix / ".git").exists()


# LOCAL BUILD TESTS (Without Workspace)

def test_local_without_workspace_uses_execroot(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Test parsing a local file when workspace root is None (uses execroot fallback).

    This simulates the actual behavior where:
    - BUILD_WORKSPACE_DIRECTORY is not set
    - prefix = /home/user/.cache/bazel/_bazel_user/hash/execroot/_main
    """
    monkeypatch.delenv("BUILD_WORKSPACE_DIRECTORY", raising=False)

    # Simulate real bazel cache structure
    bazel_cache = tmp_path / ".cache" / "bazel" / "_bazel_maximilianp" / "4ac366a7bf0ecac1b3be0bef35848a2a"
    execroot = bazel_cache / "execroot" / "_main"
    execroot.mkdir(parents=True, exist_ok=True)

    # Runfiles dir is inside sandbox, but we're checking the execroot path
    sandbox_base = bazel_cache / "sandbox" / "linux-sandbox" / "123" / "execroot" / "_main"
    runfiles_dir = sandbox_base / "bazel-out" / "k8-fastbuild" / "bin" / "test.runfiles"
    runfiles_dir.mkdir(parents=True, exist_ok=True)

    filepath = Path("src/helper_lib/test_helper_lib.py")

    prefix, module_name, file_path, file_name = parse_filename(filepath, runfiles_dir)

    assert module_name == ""
    assert file_path == "src/helper_lib"
    assert file_name == "test_helper_lib.py"

    # Verify prefix points to execroot/_main (the path before /sandbox)
    expected_prefix = bazel_cache / "execroot" / "_main"
    assert prefix == expected_prefix


def test_local_root_file_without_workspace(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Test parsing a root file when workspace is None."""
    monkeypatch.delenv("BUILD_WORKSPACE_DIRECTORY", raising=False)

    bazel_cache = tmp_path / ".cache" / "bazel" / "_bazel_test" / "xyz789"
    execroot = bazel_cache / "execroot" / "_main"
    execroot.mkdir(parents=True, exist_ok=True)

    sandbox_base = bazel_cache / "sandbox" / "worker" / "42" / "execroot" / "_main"
    runfiles_dir = sandbox_base / "bazel-bin" / "app.runfiles"
    runfiles_dir.mkdir(parents=True, exist_ok=True)

    filepath = Path("README.md")

    prefix, module_name, file_path, file_name = parse_filename(filepath, runfiles_dir)

    assert module_name == ""
    assert file_path == ""
    assert file_name == "README.md"

    # Verify prefix is execroot/_main (before sandbox)
    expected_prefix = bazel_cache / "execroot" / "_main"
    assert prefix == expected_prefix


# EDGE CASES

def test_path_reconstruction_external(tmp_path: Path) -> None:
    """Test that we can reconstruct paths from parsed components (external)."""
    bazel_cache = tmp_path / ".cache" / "bazel" / "_bazel_user" / "58de169282104bb8c73a59023f615bcd"
    sandbox_base = bazel_cache / "sandbox" / "execroot" / "_main"
    external_dir = sandbox_base / "external"
    external_dir.mkdir(parents=True, exist_ok=True)

    runfiles_dir = sandbox_base / "bazel-bin" / "test.runfiles"
    runfiles_dir.mkdir(parents=True, exist_ok=True)

    original_path = "src/tests/test_file.py"
    filepath = Path(f"external/awesome_module+/{original_path}")

    prefix, module_name, file_path, file_name = parse_filename(filepath, runfiles_dir)

    assert module_name == "awesome_module"
    reconstructed = f"{file_path}/{file_name}" if file_path else file_name
    assert reconstructed == original_path

    # Verify we can construct the full path using prefix and module_name
    full_path = prefix / module_name / file_path / file_name
    expected_full_path = bazel_cache / "external" / "awesome_module" / "src" / "tests" / "test_file.py"
    assert full_path == expected_full_path


def test_path_reconstruction_local(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Test that we can reconstruct paths from parsed components (local)."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    git_dir = workspace / ".git"
    git_dir.mkdir()

    runfiles_dir = tmp_path / "bazel-bin" / "test.runfiles"
    runfiles_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("BUILD_WORKSPACE_DIRECTORY", str(workspace))

    original_path = "src/core/utils/helper.py"
    filepath = Path(original_path)

    prefix, module_name, file_path, file_name = parse_filename(filepath, runfiles_dir)

    reconstructed = f"{file_path}/{file_name}" if file_path else file_name
    assert reconstructed == original_path
    assert module_name == ""

    # Verify we can construct the full path using prefix
    full_path = prefix / file_path / file_name
    assert full_path == workspace / "src" / "core" / "utils" / "helper.py"
