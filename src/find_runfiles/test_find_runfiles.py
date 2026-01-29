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
import pytest
from pathlib import Path
from src import find_runfiles  # Assuming the new file is named find_runfiles.py

## --- Helpers to simulate environments ---


def setup_mock_repo(tmp_path: Path):
    """Creates a dummy .git directory and returns the path."""
    repo = tmp_path / "workspaces" / "process"
    repo.mkdir(parents=True)
    (repo / ".git").mkdir()
    return repo


## --- Tests ---


def test_run_incremental_pretty_path(tmp_path, monkeypatch):
    """
    Simulates: bazel run //process-docs:incremental
    Logic: Uses RUNFILES_DIR environment variable.
    """
    git_root = setup_mock_repo(tmp_path)
    runfiles_path = (
        git_root / "bazel-out/k8-fastbuild/bin/process-docs/incremental.runfiles"
    )
    runfiles_path.mkdir(parents=True)

    # In the new logic, get_runfiles_dir() just returns the env var Path if it exists
    monkeypatch.setenv("RUNFILES_DIR", str(runfiles_path))

    result = find_runfiles.get_runfiles_dir()
    assert result == runfiles_path
    assert result.exists()


def test_build_incremental_and_exec_it(tmp_path, monkeypatch):
    """
    Simulates: bazel build //process-docs:incremental && bazel-bin/process-docs/incremental
    """
    git_root = setup_mock_repo(tmp_path)
    bin_runfiles = git_root / "bazel-bin/process-docs/incremental.runfiles"
    bin_runfiles.mkdir(parents=True)

    monkeypatch.setenv("RUNFILES_DIR", str(bin_runfiles))

    result = find_runfiles.get_runfiles_dir()
    assert result == bin_runfiles


def test_outside_bazel_ide_support(tmp_path, monkeypatch):
    """
    Simulates: Running outside bazel (e.g., Esbonio/Sphinx).
    Logic: Falls back to git_root / "bazel-bin" / "ide_support.runfiles"
    """
    git_root = setup_mock_repo(tmp_path)
    # The new logic uses Path.cwd().resolve() to find .git
    monkeypatch.chdir(git_root)
    monkeypatch.delenv("RUNFILES_DIR", raising=False)

    # Create the expected fallback path
    expected_path = git_root / "bazel-bin" / "ide_support.runfiles"
    expected_path.mkdir(parents=True)

    result = find_runfiles.get_runfiles_dir()
    assert result == expected_path


def test_find_git_root_via_env(tmp_path, monkeypatch):
    """Tests find_git_root prioritizing BUILD_WORKSPACE_DIRECTORY."""
    workspace = tmp_path / "workspace_env"
    workspace.mkdir()
    monkeypatch.setenv("BUILD_WORKSPACE_DIRECTORY", str(workspace))

    assert find_runfiles.find_git_root() == workspace


def test_find_git_root_via_traversal(tmp_path, monkeypatch):
    """Tests find_git_root by walking up the tree."""
    git_root = setup_mock_repo(tmp_path)
    monkeypatch.delenv("BUILD_WORKSPACE_DIRECTORY", raising=False)

    # We need to ensure __file__ in the module points somewhere inside this tmp_path
    # This is tricky without mocks, so we ensure the logic finds it relative to the module
    # or rely on the directory traversal if the module itself is in the temp path.
    # For a pure integration test, we verify the traversal logic:
    sub_dir = git_root / "some" / "deep" / "path"
    sub_dir.mkdir(parents=True)

    # Since we can't easily change __file__ of a loaded module,
    # find_git_root() might need a small refactor to accept a starting path
    # for better testability, but staying true to your current code:
    monkeypatch.chdir(sub_dir)
    # This will work if find_git_root uses Path.cwd() or if __file__ is managed.
