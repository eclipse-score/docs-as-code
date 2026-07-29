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
"""Shared runner for end-to-end tests of docs() binaries."""

import os
import shutil
import subprocess
from pathlib import Path


def runfile(path_env: str) -> Path:
    """Resolve a test runfile without allowing its env value to escape runfiles."""
    runfiles_root = _runfiles_root()
    candidate = os.path.normpath(os.path.join(runfiles_root, os.environ[path_env]))
    if not candidate.startswith(str(runfiles_root) + os.sep):
        raise ValueError(f"runfile path escapes TEST_SRCDIR: {candidate!r}")
    return Path(candidate)


def _runfiles_root() -> Path:
    """Return this test's Bazel-managed runfiles root."""
    return Path(
        os.path.normpath(
            os.path.join(os.environ["TEST_SRCDIR"], os.environ["TEST_WORKSPACE"])
        )
    )


def run_docs_build(
    tmp_path: Path,
    *,
    docs_binary: Path,
    source_dir: Path,
    sourcelinks: Path,
    mounts_manifest: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a docs() binary in an isolated writable workspace.

    The binary normally runs from a developer's workspace. This helper provides
    the small writable equivalent needed by a Bazel test while preserving the
    runfiles layout used to resolve in-tree mount sources.
    """
    runfiles_workspace = _runfiles_root()
    (tmp_path / "src").symlink_to(runfiles_workspace / "src", target_is_directory=True)

    copied_source_dir = tmp_path / "docs"
    shutil.copytree(source_dir, copied_source_dir)
    for name in ["MODULE.bazel", "MODULE.bazel.lock", "BUILD"]:
        (tmp_path / name).touch()

    env = os.environ.copy()
    env["SOURCE_DIRECTORY"] = str(copied_source_dir)
    if mounts_manifest:
        copied_manifest = tmp_path / "_mounts_manifest.json"
        shutil.copyfile(mounts_manifest, copied_manifest)
        env["MOUNTS_MANIFEST"] = copied_manifest.name
    else:
        env["MOUNTS_MANIFEST"] = ""
    env["DATA"] = "[]"
    env["ACTION"] = "incremental"
    env["SCORE_SOURCELINKS"] = str(sourcelinks)

    return subprocess.run(
        [str(docs_binary)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
