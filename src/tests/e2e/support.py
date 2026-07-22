# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
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
# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Shared runner for end-to-end tests of docs() binaries."""

import os
import shutil
import subprocess
from pathlib import Path


def test_dir() -> Path:
    """
    Return the path to the test directory.
    e.g. /home/alex/git/etas-contrib/eclipse-score_docs-as-code/src/tests/docs_e2e

    WARNING: Using this will make the test non-hermetic, as it will depend on the source tree being present.
    """
    return Path(__file__).resolve().parent


def runfiles_dir() -> Path:
    """
    Return the path to bazel runfiles (content as provided via `data` in the BUILD file).

    e.g. /home/alex/.cache/bazel/_bazel_alex/ec58ecca617edd0b2864120a40405cd7/sandbox/linux-sandbox/2190/execroot/_main/bazel-out/k8-fastbuild/bin/src/tests/docs_e2e/basic.runfiles/_main

    Note: this should be used for accessing runfiles, not test_dir(), as it is hermetic
    and will work even with remote execution. The test_dir() is only useful for
    debugging and development.
    """
    return Path(os.environ["TEST_SRCDIR"]) / os.environ["TEST_WORKSPACE"]


def list_runfiles_dir() -> None:
    """List all content of runfiles_dir for debugging purposes."""

    print("----")
    for item in runfiles_dir().iterdir():
        print(f"runfiles_dir: {item.relative_to(runfiles_dir())}")
    print("----")


def runfile(path_env: str) -> Path:
    """Resolve a runfiles-relative path passed through a test environment variable."""

    return runfiles_dir() / os.environ[path_env]


def run_docs_build(
    tmp_path: Path,
    *,
    docs_binary: Path,
    source_dir: Path,
) -> subprocess.CompletedProcess[str]:
    """Run prepared docs() in an isolated writable workspace.

    The binary normally runs from a developer's workspace. This helper provides
    the small writable equivalent needed by a Bazel test while preserving the
    runfiles layout used to resolve in-tree mount sources.
    """

    (tmp_path / "src").symlink_to(runfiles_dir() / "src", target_is_directory=True)

    source_dir = tmp_path / "docs"
    shutil.copytree(source_dir, tmp_path / "docs")
    for name in ["MODULE.bazel", "MODULE.bazel.lock", "BUILD"]:
        (tmp_path / name).touch()

    # env preparation normally happens in the docs() binary,
    # but since we need to execute it ourselfes,
    # we need to prepare the environment manually.
    env = os.environ.copy()
    env["SOURCE_DIRECTORY"] = str(source_dir)
    env["DATA"] = "[]"
    env["ACTION"] = "incremental"

    return subprocess.run(
        [str(docs_binary)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
