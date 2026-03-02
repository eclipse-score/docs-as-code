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
import sys
from pathlib import Path

from runfiles import Runfiles
from sphinx_needs.logging import get_logger

LOGGER = get_logger(__name__)


def find_ws_root() -> Path | None:
    """
    Find the current MODULE.bazel workspace root directory.

    Execution context behavior:
    - 'bazel run' => ✅ Full workspace path
    - 'bazel build' => ❌ None (sandbox isolation)
    - 'direct sphinx' => ❌ None (no Bazel environment)
    """
    ws_dir = os.environ.get("BUILD_WORKSPACE_DIRECTORY", None)
    return Path(ws_dir) if ws_dir else None


def find_git_root() -> Path | None:
    """
    Find the git root directory, starting from workspace root or current directory.

    Execution context behavior:
    - 'bazel run' => ✅ Git root path (starts from workspace)
    - 'bazel build' => ❌ None (sandbox has no .git)
    - 'direct sphinx' => ✅ Git root path (fallback to cwd)
    """
    start_path = find_ws_root()
    if start_path is None:
        start_path = Path.cwd()
    git_root = Path(start_path).resolve()
    while not (git_root / ".git").exists():
        git_root = git_root.parent
        if git_root == Path("/"):
            return None
    return git_root


def parse_remote_git_output(str_line: str) -> str:
    """
    Parse git remote output and extract <user/org>/<repository> format.

    Example:
        Input:  'origin git@github.com:MaximilianSoerenPollak/docs-as-code.git'
        Output: 'MaximilianSoerenPollak/docs-as-code'
    """
    parts = str_line.split(
        maxsplit=2
    )  # split into up to three parts [remote, url, ...]
    if len(parts) < 2:
        LOGGER.warning(
            f"Got wrong input line from 'get_github_repo_info'. Input: {str_line}. "
            + "Expected example: 'origin git@github.com:user/repo.git'"
        )
        return ""

    url = parts[1]  # Get the URL part

    # Handle SSH vs HTTPS formats directly
    if url.startswith("git@"):
        path = url.split(":", 1)[-1]
    else:
        path = "/".join(url.split("/")[3:])

    return path.removesuffix(".git")


def get_github_repo_info(git_root_cwd: Path) -> str:
    """
    Query git for the github remote repository (based on heuristic).

    Execution context behavior:
    - Works consistently across all contexts when given valid git directory
    - Fails only when input path has no git repository

    Args:
        git_root_cwd: Path to directory containing .git folder

    Returns:
        Repository in format 'user/repo' or 'org/repo'
    """
    process = subprocess.run(
        ["git", "remote", "-v"], capture_output=True, text=True, cwd=git_root_cwd
    )
    repo = ""
    for line in process.stdout.split("\n"):
        if "origin" in line and "(fetch)" in line:
            repo = parse_remote_git_output(line)
            break
    else:
        # If we do not find 'origin' we just take the first line
        LOGGER.info(
            "Did not find origin remote name. Will now take first result from:"
            + "'git remote -v'"
        )
        repo = parse_remote_git_output(process.stdout.split("\n")[0])
    assert repo != "", (
        "Remote repository is not defined. Make sure you have a remote set. "
        + "Check this via 'git remote -v'"
    )
    return repo


def get_github_base_url() -> str:
    """
    Generate GitHub base URL for the current repository.

    Execution context behavior:
    - 'bazel run' => ✅ Correct GitHub URL
    - 'bazel build' => ⚠️ Uses Path() fallback when git_root is None
    - 'direct sphinx' => ✅ Correct GitHub URL

    Returns:
        GitHub URL in format 'https://github.com/user/repo'
    """
    passed_git_root = find_git_root()
    if passed_git_root is None:
        passed_git_root = Path()
    repo_info = get_github_repo_info(passed_git_root)
    return f"https://github.com/{repo_info}"


def get_current_git_hash(git_root: Path) -> str:
    """
    Get the current git commit hash.

    Execution context behavior:
    - Works consistently across all contexts when given valid git directory
    - Fails only when input path has no git repository

    Args:
        git_root: Path to directory containing .git folder

    Returns:
        Full commit hash (40 character hex string)
    """
    try:
        result = subprocess.run(
            ["git", "log", "-n", "1", "--pretty=format:%H"],
            cwd=git_root,
            text=True,  # ✅ decode automatically
            capture_output=True,
            check=True,
        )
        decoded_result = result.stdout.strip()

        if len(decoded_result) != 40:
            raise ValueError(f"Unexpected git hash length: {decoded_result}")

        if not all(c in "0123456789abcdef" for c in decoded_result):
            raise ValueError(f"Invalid characters in git hash: {decoded_result}")

        return decoded_result
    except Exception as e:
        LOGGER.warning(
            f"Unexpected error while trying to get git_hash. Executed in: {git_root}",
            exc_info=e,
        )
        raise


def get_runfiles_dir() -> Path:
    """
    Find the Bazel runfiles directory using bazel_runfiles convention,
    fallback to RUNFILES_DIR or relative traversal if needed.
    """
    if (r := Runfiles.Create()) and (rd := r.EnvVars().get("RUNFILES_DIR")):
        runfiles_dir = Path(rd)
    else:
        # The only way to land here is when running from within the virtual
        # environment created by the `:ide_support` rule in the BUILD file.
        # i.e. esbonio or manual sphinx-build execution within the virtual
        # environment.
        # We'll still use the plantuml binary from the bazel build.
        # But we need to find it first.
        LOGGER.debug("Running outside bazel.")

        git_root = find_git_root()
        if git_root is None:
            sys.exit("Could not find git root.")

        runfiles_dir = git_root / "bazel-bin" / "ide_support.runfiles"

    if not runfiles_dir.exists():
        sys.exit(
            f"Could not find runfiles_dir at {runfiles_dir}. "
            "Have a look at README.md for instructions on how to build docs."
        )
    return runfiles_dir
