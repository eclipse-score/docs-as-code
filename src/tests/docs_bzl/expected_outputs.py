# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Golden-output verification for public ``docs.bzl`` scenarios.

Expected output names are discovered below the scenario's ``_expected``
directory. The target catalog below is the only place that maps a short
expected-output name to the Bazel target and to the output location used by the
harness.
"""

from __future__ import annotations

import contextlib
import difflib
import json
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path

from src.tests.docs_bzl.helpers import (
    TEST_ROOT,
    TEST_ROOT_BAZEL,
    built_output,
    run_bazel,
    run_package,
)

# GitHub Actions exposes this variable to the documentation build. Supplying
# the same repository identity locally makes generated GitHub links and the
# Sphinx theme configuration match the HTML produced in CI.
EXPECTED_GITHUB_REPOSITORY = "eclipse-score/docs-as-code"
EXPECTED_GITHUB_ENV = {"GITHUB_REPOSITORY": EXPECTED_GITHUB_REPOSITORY}
EXPECTED_GITHUB_ACTION_ENV = (
    f"--action_env=GITHUB_REPOSITORY={EXPECTED_GITHUB_REPOSITORY}"
)


@dataclass(frozen=True)
class ExpectedTarget:
    """Describe one target that can have a checked-in expected output."""

    label: str
    command: str
    output_kind: str
    output_path: str


# Keep this mapping centralized. Scenario directories only use the short names
# in ``_expected/`` and do not repeat Bazel labels or output path knowledge in
# their Python tests.
TARGETS: dict[str, ExpectedTarget] = {
    "docs": ExpectedTarget(
        label=":docs",
        command="run",
        output_kind="directory",
        output_path="_build",
    ),
    "needs_json": ExpectedTarget(
        label=":needs_json",
        command="build",
        output_kind="directory",
        output_path="needs_json/_build/needs",
    ),
    "needs_local": ExpectedTarget(
        label=":docs_bundle.__internal__.needs_local",
        command="build",
        output_kind="file",
        output_path="docs_bundle.__internal__.needs_local/_build/needs/needs.json",
    ),
    "data_bundle_needs": ExpectedTarget(
        label=":data_bundle.__internal__.needs_local",
        command="build",
        output_kind="directory",
        output_path="data_bundle.__internal__.needs_local/_build/needs",
    ),
    "isolated_source_bundle_needs": ExpectedTarget(
        label=":isolated_source_bundle.__internal__.needs_local",
        command="build",
        output_kind="directory",
        output_path="isolated_source_bundle.__internal__.needs_local/_build/needs",
    ),
    "sourcelinks_json": ExpectedTarget(
        label=":sourcelinks_json",
        command="build",
        output_kind="file",
        output_path="sourcelinks_json.json",
    ),
    "metrics_json": ExpectedTarget(
        label=":metrics_json",
        command="build",
        output_kind="file",
        output_path="metrics.json",
    ),
    "generated_config": ExpectedTarget(
        label=":_docs_generated_config",
        command="build",
        output_kind="file",
        output_path="docs/conf.py",
    ),
    "mounts_manifest": ExpectedTarget(
        label=":_mounts_manifest",
        command="build",
        output_kind="file",
        output_path="_mounts_manifest.json",
    ),
    "ordered_aggregate_manifest": ExpectedTarget(
        label=":ordered_aggregate_manifest",
        command="build",
        output_kind="file",
        output_path="ordered_aggregate_manifest.json",
    ),
}


@dataclass(frozen=True)
class ExpectedOutput:
    """Connect one discovered expected path to its central target definition."""

    short_name: str
    target: ExpectedTarget
    expected_path: Path


def _scenario_dir(scenario: str) -> Path:
    path = TEST_ROOT / "scenarios" / scenario
    if not path.is_dir():
        raise ValueError(f"docs.bzl scenario does not exist: {scenario}")
    return path


def discover_expected_scenarios() -> list[str]:
    """Find scenario packages that opt into golden-output verification."""
    scenarios_root = TEST_ROOT / "scenarios"
    return sorted(
        str(expected_root.parent.relative_to(scenarios_root))
        for expected_root in scenarios_root.rglob("_expected")
        if expected_root.is_dir()
    )


def discover_expected_outputs(scenario: str) -> list[ExpectedOutput]:
    """Discover expected target files and directories in one scenario."""
    scenario_dir = _scenario_dir(scenario)
    expected_root = scenario_dir / "_expected"
    if not expected_root.is_dir():
        raise ValueError(f"scenario {scenario!r} has no _expected directory")

    discovered: list[ExpectedOutput] = []

    for path in sorted(expected_root.iterdir()):
        matches = [
            short_name
            for short_name in TARGETS
            if path.name == short_name or path.name.startswith(f"{short_name}.")
        ]
        if not matches:
            known = ", ".join(sorted(TARGETS))
            raise ValueError(
                f"unknown expected output {path.name!r} in {expected_root}; "
                f"known target names: {known}"
            )
        if len(matches) != 1:
            raise ValueError(
                f"expected output name {path.name!r} is ambiguous; matches {matches}"
            )

        short_name = matches[0]
        target = TARGETS[short_name]
        if target.output_kind == "directory" and not path.is_dir():
            raise ValueError(
                f"expected output {path} must be a directory for target {target.label}"
            )
        if target.output_kind == "file" and not path.is_file():
            raise ValueError(
                f"expected output {path} must be a file for target {target.label}"
            )

        discovered.append(
            ExpectedOutput(
                short_name=short_name,
                target=target,
                expected_path=path,
            )
        )

    if not discovered:
        raise ValueError(f"scenario {scenario!r} has no expected outputs")
    return discovered


def _full_label(scenario: str, target: ExpectedTarget) -> str:
    return f"{TEST_ROOT_BAZEL}/scenarios/{scenario}{target.label}"


def _actual_path(scenario: str, target: ExpectedTarget) -> Path:
    package = f"scenarios/{scenario}"
    if target.command == "run":
        return _scenario_dir(scenario) / target.output_path
    return built_output(package, target.output_path)


def _text_diff(expected: bytes, actual: bytes, path: Path) -> str:
    try:
        expected_text = expected.decode("utf-8").splitlines(keepends=True)
        actual_text = actual.decode("utf-8").splitlines(keepends=True)
    except UnicodeDecodeError:
        return (
            f"{path}: byte content differs "
            f"(expected {len(expected)} bytes, actual {len(actual)} bytes)"
        )

    diff = "".join(
        difflib.unified_diff(
            expected_text,
            actual_text,
            fromfile=f"expected/{path.name}",
            tofile=f"actual/{path.name}",
        )
    )
    return f"{path}: byte content differs\n{diff}"


def _comparison_bytes(path: Path) -> bytes:
    """Return the representation used for comparing one expected file.

    JSON output is formatted for humans before comparison. This keeps checked-in
    expected files readable while still checking the complete parsed document;
    object-key order is intentionally normalized, but array order and all JSON
    values remain significant. Other file types retain strict byte comparison.
    """
    raw = path.read_bytes()
    if path.suffix != ".json":
        return raw

    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"{path}: invalid JSON: {exc}") from exc
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _expected_file_diff(expected_path: Path, actual_path: Path) -> str | None:
    """Return a diff for one expected file, or ``None`` when it matches."""
    if not actual_path.is_file():
        raise AssertionError(f"expected file is missing: {actual_path}")

    expected = _comparison_bytes(expected_path)
    actual = _comparison_bytes(actual_path)
    if expected == actual:
        return None
    return _text_diff(expected, actual, expected_path)


def _expected_file_pairs(
    expected: ExpectedOutput, scenario: str
) -> list[tuple[Path, Path]]:
    """Return checked-in files and their corresponding actual output files."""
    actual_root = _actual_path(scenario, expected.target)
    if expected.expected_path.is_file():
        return [(expected.expected_path, actual_root)]

    if not actual_root.is_dir():
        raise AssertionError(f"expected output directory is missing: {actual_root}")

    return [
        (
            expected_file,
            actual_root / expected_file.relative_to(expected.expected_path),
        )
        for expected_file in sorted(
            file for file in expected.expected_path.rglob("*") if file.is_file()
        )
    ]


def _write_expected_file(path: Path, content: bytes) -> None:
    """Replace an expected file atomically while preserving its file mode."""
    mode = stat.S_IMODE(path.stat().st_mode)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}."
    )
    try:
        with os.fdopen(descriptor, "wb") as temporary_file:
            descriptor = -1
            temporary_file.write(content)
        os.chmod(temporary_name, mode)
        os.replace(temporary_name, path)
    except BaseException:
        if descriptor != -1:
            os.close(descriptor)
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temporary_name)
        raise


def _run_expected_target(scenario: str, expected: ExpectedOutput) -> None:
    """Build or run one target whose output is checked by a test case."""
    full_label = _full_label(scenario, expected.target)
    if expected.target.command == "build":
        run_bazel(
            ["build", EXPECTED_GITHUB_ACTION_ENV, full_label],
            env=EXPECTED_GITHUB_ENV,
        )
    elif expected.target.command == "run":
        run_package(
            "run",
            f"scenarios/{scenario}",
            expected.target.label,
            env=EXPECTED_GITHUB_ENV,
        )
    else:
        raise ValueError(f"unknown expected target command: {expected.target.command}")


def update_expected_output(scenario: str, expected_output: ExpectedOutput) -> None:
    """Update changed expected files and fail when the scenario changed.

    The checked-in files below this target define the update scope. This
    deliberately does not copy every file from an output directory, because
    generated docs directories often contain additional files or unstable
    artifacts that are not part of the scenario contract. The failure after an
    update makes this function suitable for a pre-commit-style pytest check:
    the changed files can be reviewed and committed, then the test passes on
    the next run.
    """
    _run_expected_target(scenario, expected_output)

    changes: list[tuple[Path, bytes, str]] = []
    for expected_path, actual_path in _expected_file_pairs(expected_output, scenario):
        if not actual_path.is_file():
            raise AssertionError(f"expected file is missing: {actual_path}")
        actual_bytes = _comparison_bytes(actual_path)
        diff = _expected_file_diff(expected_path, actual_path)
        if diff is not None:
            changes.append((expected_path, actual_bytes, diff))

    for expected_path, actual_bytes, _ in changes:
        _write_expected_file(expected_path, actual_bytes)

    if changes:
        diff = "\n\n".join(change_diff for _, _, change_diff in changes)
        raise AssertionError(
            f"expected outputs changed; review and commit the updated files:\n{diff}"
        )
