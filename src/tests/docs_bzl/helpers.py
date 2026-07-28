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
"""Helpers for Category-2 e2e tests: run real bazel against in-repo fixtures."""

import json
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from src.helper_lib import find_git_root

FIXTURES = Path(__file__).parent / "fixtures"
GIT_ROOT = find_git_root()
assert GIT_ROOT
FIXTURES_BAZEL = "//" + str(FIXTURES.relative_to(GIT_ROOT))


def repo_root() -> Path:
    root = find_git_root()
    assert root is not None, "git root not found"
    return root


def run_bazel(args: list[str], expect_error: bool = False):
    start_time = time.time()
    cmd = ["bazel", *args]
    cmd_str = " ".join(cmd)

    p = subprocess.run(
        cmd,
        cwd=repo_root(),
        capture_output=True,
        text=True,
    )
    end_time = time.time()
    print(f"Running 'bazel {' '.join(args)}' took {end_time - start_time:.4f} seconds")

    if expect_error and p.returncode == 0:
        raise RuntimeError(
            f"{cmd_str} was expected to fail but succeeded\n"
            f"stdout:\n{p.stdout}\n"
            f"stderr:\n{p.stderr}"
        )

    if not expect_error and p.returncode != 0:
        raise RuntimeError(
            f"bazel {args} failed with exit code {p.returncode}\n"
            f"stdout:\n{p.stdout}\n"
            f"stderr:\n{p.stderr}"
        )

    return p


@dataclass
class RunResult:
    stdout: str
    stderr: str
    build_dir: Path
    artifacts: dict[str, Path] | None


def run_fixture(
    bazel_cmd: str,
    fixture: str,
    target: str,
    expect_error: bool = False,
) -> RunResult:
    """Run bazel in a fixture subdirectory."""
    assert bazel_cmd in ("build", "run"), "only build and run are supported"
    assert target.startswith(":"), "target must be relative to fixture"

    if not (FIXTURES / fixture).is_dir():
        raise ValueError(f"fixture {fixture} does not exist in {FIXTURES}")

    # Split logs by bazel commands visually without adding any fancy formatting dependency
    print("")

    full_target = FIXTURES_BAZEL + "/" + fixture + target

    clean_build(FIXTURES / fixture)

    p1 = run_bazel([bazel_cmd, full_target], expect_error=expect_error)

    if bazel_cmd == "build":
        # Generic solution needs to use cquery.
        # That extra cquery is about 0,5 seconds, which sounds horrible for testing,
        # but considering how slow bazel is anyway...
        RUN_CQUERY = False
        if RUN_CQUERY:
            p2 = run_bazel(["cquery", "--output=files", full_target])
            artifacts_dir = Path(p2.stdout.strip().splitlines()[0])
        else:
            assert GIT_ROOT
            # e.g. bazel-out/k8-fastbuild/bin/src/tests/docs_bzl/fixtures/external_needs/producer/needs_json/_build/needs
            artifacts_dir = (
                GIT_ROOT
                / "bazel-out/k8-fastbuild/bin/"
                / FIXTURES.relative_to(GIT_ROOT)
                / fixture
                / target[1:]
                / "_build/needs"
            )

        assert artifacts_dir.is_dir(), (
            f"expected output artifacts to be a directory, got {artifacts_dir}"
        )
        artifacts = {f.name: f for f in artifacts_dir.iterdir()}
    else:
        artifacts = None

    return RunResult(
        stdout=p1.stdout,
        stderr=p1.stderr,
        build_dir=FIXTURES / fixture / "_build",
        artifacts=artifacts,
    )


def clean_build(path: Path) -> None:
    """Delete the _build directory in a path, if it exists."""
    shutil.rmtree(path / "_build", ignore_errors=True)


def load_needs(needs_json: Path):
    data = json.loads(needs_json.read_text(encoding="utf-8"))
    needs: dict[str, object] = {}
    for version in data.get("versions", {}).values():
        needs.update(version.get("needs", {}))
    return needs
