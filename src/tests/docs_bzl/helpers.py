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
import re
import shutil
import subprocess
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import cast

from src.helper_lib import find_git_root

TEST_ROOT = Path(__file__).parent
GIT_ROOT = find_git_root()
assert GIT_ROOT
TEST_ROOT_BAZEL = "//" + str(TEST_ROOT.relative_to(GIT_ROOT))
# A separate Bazel module that uses docs-as-code like a real consumer does.
# Its packages are not part of docs-as-code; Bazel runs inside this directory.
CONSUMER_ROOT = TEST_ROOT / "consumer"

# GitHub Actions exposes this variable to the documentation build. Supplying
# the same repository identity locally makes generated GitHub links (such as
# "Edit on GitHub") and the Sphinx theme configuration match CI.
GITHUB_REPOSITORY = "eclipse-score/docs-as-code"
GITHUB_ENV = {"GITHUB_REPOSITORY": GITHUB_REPOSITORY}
# Edit links of a build run with ``GITHUB_ENV``; docs_cli pins the branch to main.
GITHUB_EDIT_URL = f"https://github.com/{GITHUB_REPOSITORY}/edit/main"


def repo_root() -> Path:
    root = find_git_root()
    assert root is not None, "git root not found"
    return root


@contextmanager
def staged_coverage_report(source: Path) -> Iterator[Path]:
    """Stage a fixture at the workflow input path and restore any local report."""
    report = repo_root() / "coverage-report/coverage_report.dat"
    saved = report.read_bytes() if report.exists() else None
    directory_existed = report.parent.exists()
    report.parent.mkdir(exist_ok=True)
    report.write_bytes(source.read_bytes())
    try:
        yield report
    finally:
        if saved is None:
            report.unlink(missing_ok=True)
        else:
            report.write_bytes(saved)
        if not directory_existed:
            report.parent.rmdir()


def run_bazel(
    args: list[str],
    expect_error: bool = False,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
):
    """Run Bazel in ``cwd`` (default: the repo root), optionally overriding
    the environment of the subprocess."""
    start_time = time.time()
    cmd = ["bazel", *args]
    cmd_str = " ".join(cmd)

    p = subprocess.run(
        cmd,
        cwd=cwd or repo_root(),
        capture_output=True,
        text=True,
        env=None if env is None else {**os.environ, **env},
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


@dataclass(frozen=True)
class _BazelPackage:
    """Where Bazel runs for a test package, its label and its output directory."""

    cwd: Path
    label: str
    bin_dir: Path


def _bazel_package(package: str) -> _BazelPackage:
    """Locate a test package (a path relative to ``TEST_ROOT``)."""
    package_dir = TEST_ROOT / package
    if package_dir.is_relative_to(CONSUMER_ROOT):
        relative = package_dir.relative_to(CONSUMER_ROOT)
        return _BazelPackage(
            CONSUMER_ROOT, f"//{relative.as_posix()}", _consumer_bazel_bin() / relative
        )
    root = repo_root()
    return _BazelPackage(
        root,
        f"{TEST_ROOT_BAZEL}/{package}",
        root / "bazel-bin" / TEST_ROOT.relative_to(root) / package,
    )


@cache
def _consumer_bazel_bin() -> Path:
    """The consumer module's bazel-bin. The module creates no bazel-* symlinks."""
    p = run_bazel(["info", "bazel-bin"], cwd=CONSUMER_ROOT)
    return Path(p.stdout.strip())


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

    location = _bazel_package(package)
    full_target = location.label + target

    # aspect_rules_py creates the runtime venv inside the target's runfiles
    # tree. It cannot reliably replace an already-populated tree on a second
    # ``bazel run``. Remove only that disposable venv; Bazel's server and all
    # action/repository caches remain intact.
    if bazel_cmd == "run":
        runfiles_venv = built_output(package, f"{target[1:]}.runfiles/.docs.venv")
        shutil.rmtree(runfiles_venv, ignore_errors=True)

    p1 = run_bazel(
        [bazel_cmd, full_target], expect_error=expect_error, env=env, cwd=location.cwd
    )

    if bazel_cmd == "build" and target == ":needs_json":
        # Generic solution needs to use cquery.
        # That extra cquery is about 0,5 seconds, which sounds horrible for testing,
        # but considering how slow bazel is anyway...
        RUN_CQUERY = False
        if RUN_CQUERY:
            p2 = run_bazel(["cquery", "--output=files", full_target], cwd=location.cwd)
            artifacts_dir = Path(p2.stdout.strip().splitlines()[0])
        else:
            # e.g. bazel-bin/src/tests/docs_bzl/scenarios/reference_integration/score_platform/needs_json/_build/needs
            artifacts_dir = built_output(package, f"{target[1:]}/_build/needs")

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
    env: Mapping[str, str] | None = None,
) -> RunResult:
    """Run one general docs() scenario, in the consumer module if it lives there."""
    in_consumer = (CONSUMER_ROOT / scenario).is_dir()
    package = f"consumer/{scenario}" if in_consumer else f"scenarios/{scenario}"
    return run_package(bazel_cmd, package, target, expect_error, env)


def built_output(package: str, filename: str) -> Path:
    """Return a declared output from a package built in the current configuration."""
    return _bazel_package(package).bin_dir / filename


def load_needs_json(needs_json: Path) -> dict[str, object]:
    raw_data: object = json.loads(needs_json.read_text(encoding="utf-8"))
    if not isinstance(raw_data, dict):
        raise ValueError("needs.json must be an object")
    return cast("dict[str, object]", raw_data)


_TOCTREE_LINK = re.compile(r'<li class="toctree-l1"><a class="[^"]*" href="([^"]*)"')


def _article(page: Path) -> str:
    """Return a rendered page's main content, without the theme's sidebar
    navigation, which repeats the same toctree links."""
    html = page.read_text(encoding="utf-8")
    return html[html.index("<article") : html.index("</article>")]


def toctree_links(page: Path) -> list[str]:
    """Return all first-level toctree link targets in a page's main content.

    This includes links that a mount adds to a page without a toctree of its
    own; those are rendered as a bare list without a toctree wrapper.
    """
    return _TOCTREE_LINK.findall(_article(page))


def toctrees(page: Path) -> list[list[str]]:
    """Return the first-level link targets of each toctree directive, in order.

    An empty toctree yields an empty list, so list positions match a mount's
    ``toctree_index``.
    """
    wrappers = _article(page).split('<div class="toctree-wrapper')[1:]
    return [_TOCTREE_LINK.findall(wrapper) for wrapper in wrappers]


_EDIT_LINK = re.compile(r'<div class="tocsection editthispage">\s*<a href="([^"]*)"')


def edit_link(page: Path) -> str | None:
    """Return a rendered page's "Edit on GitHub" URL, or ``None`` if it has none.

    The link only renders when the build knows the GitHub repository, so the
    page must come from a build run with ``GITHUB_ENV``.
    """
    match = _EDIT_LINK.search(page.read_text(encoding="utf-8"))
    return match[1] if match else None


def assert_no_compatibility_findings(output_dir: Path) -> None:
    """Assert that a docs or Needs build reported no compatibility findings.

    Every build writes ``compatibility-findings.json`` (and an HTML version of
    it) next to its outputs. A scenario without cross-module version
    mismatches must produce an empty report.
    """
    report_path = output_dir / "compatibility-findings.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["findings"] == [], f"unexpected findings in {report_path}"
    assert report["summary"]["count"] == 0
    assert (output_dir / "compatibility-findings.html").is_file()


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
