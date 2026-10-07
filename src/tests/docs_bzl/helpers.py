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
"""Helpers for public docs.bzl integration tests driven through Bazel."""

import json
import os
import shutil
import subprocess
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from src.helper_lib import find_git_root

TEST_ROOT = Path(__file__).parent
GIT_ROOT = find_git_root()
assert GIT_ROOT
TEST_ROOT_BAZEL = "//" + str(TEST_ROOT.relative_to(GIT_ROOT))


def repo_root() -> Path:
    root = find_git_root()
    assert root is not None, "git root not found"
    return root


def _coverage_env() -> dict[str, str]:
    """Return the coverage.py settings for the Sphinx runs Bazel starts.

    Coverage is switched on through DOCS_BZL_COVERAGE_DIR rather than the
    COVERAGE_* variables themselves: coverage.py's .pth start-up hook would
    otherwise also measure this pytest process, whose code is not under test.
    The directory must be outside /tmp, because each Bazel sandbox gets a
    private /tmp and data written there is lost.
    """
    directory = os.environ.get("DOCS_BZL_COVERAGE_DIR")
    if not directory:
        return {}
    data_dir = Path(directory).absolute()
    data_dir.mkdir(parents=True, exist_ok=True)
    return {
        # An absolute path in the checkout is readable from every sandbox and
        # runfiles tree the Sphinx runs start in.
        "COVERAGE_PROCESS_START": str(repo_root() / "pyproject.toml"),
        "COVERAGE_FILE": str(data_dir / ".coverage"),
    }


def _coverage_flags(command: str, coverage_env: Mapping[str, str]) -> list[str]:
    """Forward coverage.py settings into Bazel's Sphinx Needs actions.

    `bazel run` hands its environment to cli.py; build actions only see the
    settings through these flags.
    """
    # Commands that build share one configuration, so a coverage run neither
    # rebuilds nor looks up outputs of a different one. `query` takes no build
    # flags at all.
    if not coverage_env or command not in ("build", "run", "cquery"):
        return []
    coverage_file = Path(coverage_env["COVERAGE_FILE"])
    return [
        "--//src/docs_cli:coverage_process_start="
        + coverage_env["COVERAGE_PROCESS_START"],
        f"--//src/docs_cli:coverage_file={coverage_file}",
        # Sandboxed actions may only write their declared outputs; this lets
        # the Sphinx action write its coverage data as well.
        f"--sandbox_writable_path={coverage_file.parent}",
    ]


def run_bazel(
    args: list[str],
    expect_error: bool = False,
    env: Mapping[str, str] | None = None,
):
    """Run Bazel, optionally overriding the environment of the subprocess."""
    start_time = time.time()
    coverage_env = _coverage_env()
    cmd = ["bazel", args[0], *_coverage_flags(args[0], coverage_env), *args[1:]]
    cmd_str = " ".join(cmd)

    p = subprocess.run(
        cmd,
        cwd=repo_root(),
        capture_output=True,
        text=True,
        # `bazel run` hands this environment on to cli.py, which is how the
        # coverage settings reach the Sphinx runs that are not build actions.
        env=(
            None
            if env is None and not coverage_env
            else {**os.environ, **coverage_env, **(env or {})}
        ),
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


def run_package(
    bazel_cmd: str,
    package: str,
    target: str,
    expect_error: bool = False,
    env: Mapping[str, str] | None = None,
) -> RunResult:
    """Run Bazel against one package, with optional target environment overrides."""
    assert bazel_cmd in ("build", "run"), "only build and run are supported"
    assert target.startswith(":"), "target must be relative to package"

    package_dir = TEST_ROOT / package
    if not package_dir.is_dir():
        raise ValueError(f"test package {package} does not exist in {TEST_ROOT}")

    # Split logs by bazel commands visually without adding any fancy formatting dependency
    print("")

    full_target = TEST_ROOT_BAZEL + "/" + package + target

    # aspect_rules_py creates the runtime venv inside the target's runfiles
    # tree. It cannot reliably replace an already-populated tree on a second
    # ``bazel run``. Remove only that disposable venv; Bazel's server and all
    # action/repository caches remain intact.
    if bazel_cmd == "run":
        runfiles_venv = built_output(package, f"{target[1:]}.runfiles/.docs.venv")
        shutil.rmtree(runfiles_venv, ignore_errors=True)

    p1 = run_bazel([bazel_cmd, full_target], expect_error=expect_error, env=env)

    if bazel_cmd == "build" and target == ":needs_json":
        # Generic solution needs to use cquery.
        # That extra cquery is about 0,5 seconds, which sounds horrible for testing,
        # but considering how slow bazel is anyway...
        RUN_CQUERY = False
        if RUN_CQUERY:
            p2 = run_bazel(["cquery", "--output=files", full_target])
            artifacts_dir = Path(p2.stdout.strip().splitlines()[0])
        else:
            assert GIT_ROOT
            # e.g. bazel-out/k8-fastbuild/bin/src/tests/docs_bzl/scenarios/reference_integration/score_platform/needs_json/_build/needs
            artifacts_dir = (
                GIT_ROOT
                / "bazel-out/k8-fastbuild/bin/"
                / TEST_ROOT.relative_to(GIT_ROOT)
                / package
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
        build_dir=package_dir / "_build",
        artifacts=artifacts,
    )


def run_scenario(
    bazel_cmd: str,
    scenario: str,
    target: str,
    expect_error: bool = False,
) -> RunResult:
    """Run one general docs() scenario."""
    return run_package(bazel_cmd, f"scenarios/{scenario}", target, expect_error)


def built_output(package: str, filename: str) -> Path:
    """Return a declared output from a package built in the current configuration."""
    root = repo_root()
    return root / "bazel-bin" / TEST_ROOT.relative_to(root) / package / filename


def load_needs_json(needs_json: Path) -> dict[str, object]:
    raw_data: object = json.loads(needs_json.read_text(encoding="utf-8"))
    if not isinstance(raw_data, dict):
        raise ValueError("needs.json must be an object")
    return cast("dict[str, object]", raw_data)


def load_needs(needs_json: Path) -> dict[str, object]:
    data = load_needs_json(needs_json)
    needs: dict[str, object] = {}
    versions = data.get("versions", {})
    if not isinstance(versions, dict):
        raise ValueError("needs.json field 'versions' must be an object")
    typed_versions = cast("dict[str, object]", versions)
    for version in typed_versions.values():
        if isinstance(version, dict):
            typed_version = cast("dict[str, object]", version)
            version_needs = typed_version.get("needs", {})
            if isinstance(version_needs, dict):
                needs.update(cast("dict[str, object]", version_needs))
    return needs
