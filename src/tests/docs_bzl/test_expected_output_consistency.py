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
"""Behavioral tests for the checked-in expected-output contract."""

from pathlib import Path

import pytest

import src.tests.docs_bzl.expected_outputs as expected_outputs
from src.tests.docs_bzl.expected_outputs import (
    ExpectedOutput,
    ExpectedTarget,
    update_expected_output,
)


def _stub_expected_output_execution(
    monkeypatch: pytest.MonkeyPatch,
    expected_path: Path,
    actual_path: Path,
) -> ExpectedOutput:
    """Replace Bazel execution with one deterministic Expected-/Actual-file pair."""
    expected = ExpectedOutput(
        short_name="fixture",
        target=ExpectedTarget(
            label=":fixture",
            command="build",
            output_kind="file",
            output_path="fixture",
        ),
        expected_path=expected_path,
    )
    monkeypatch.setattr(
        expected_outputs,
        "_run_expected_target",
        lambda scenario, expected: None,
    )
    monkeypatch.setattr(
        expected_outputs,
        "_expected_file_pairs",
        lambda expected, scenario: [(expected_path, actual_path)],
    )
    return expected


@pytest.mark.bazel_cached
def test_changed_expected_output_is_reported_with_diff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Changed output is written and reported for review as a failing check."""
    expected_path = tmp_path / "expected.txt"
    actual_path = tmp_path / "actual.txt"
    expected_path.write_text("before\n", encoding="utf-8")
    actual_path.write_text("after\n", encoding="utf-8")
    expected = _stub_expected_output_execution(monkeypatch, expected_path, actual_path)

    with pytest.raises(AssertionError, match="expected outputs changed") as failure:
        update_expected_output("fixture", expected)

    assert expected_path.read_text(encoding="utf-8") == "after\n"
    assert "-before" in str(failure.value)
    assert "+after" in str(failure.value)


@pytest.mark.bazel_cached
def test_unchanged_expected_output_is_accepted_without_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stable generated output passes and does not rewrite its expected file."""
    expected_path = tmp_path / "expected.txt"
    actual_path = tmp_path / "actual.txt"
    expected_path.write_text("stable\n", encoding="utf-8")
    actual_path.write_text("stable\n", encoding="utf-8")
    expected = _stub_expected_output_execution(monkeypatch, expected_path, actual_path)
    write_calls: list[tuple[Path, bytes]] = []
    monkeypatch.setattr(
        expected_outputs,
        "_write_expected_file",
        lambda path, content: write_calls.append((path, content)),
    )

    update_expected_output("fixture", expected)

    assert expected_path.read_text(encoding="utf-8") == "stable\n"
    assert write_calls == []
