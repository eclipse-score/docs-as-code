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

from src.helper_lib import get_current_git_hash, get_github_repo_info


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


# Test error handling
def test_git_operations_with_no_commits(temp_dir):
    """Test git operations on repo with no commits."""
    git_dir = temp_dir / "empty_repo"
    git_dir.mkdir()

    # Initialize git repo but don't commit anything
    subprocess.run(["git", "init"], cwd=git_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=git_dir, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=git_dir, check=True)

    os.chdir(Path(git_dir).absolute())
    # Should raise an exception when trying to get hash
    with pytest.raises(Exception):
        get_current_git_hash(git_dir)


def test_git_repo_with_no_remotes(temp_dir):
    """Test git repository with no remotes."""
    git_dir = temp_dir / "no_remote_repo"
    git_dir.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=git_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=git_dir, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=git_dir, check=True)

    # Create a test file and commit
    test_file = git_dir / "test_file.py"
    test_file.write_text("# Test file\nprint('hello')\n")
    subprocess.run(["git", "add", "."], cwd=git_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=git_dir, check=True)
    os.chdir(git_dir)

    # Should raise an exception when trying to get repo info
    with pytest.raises(AssertionError):
        get_github_repo_info(git_dir)
