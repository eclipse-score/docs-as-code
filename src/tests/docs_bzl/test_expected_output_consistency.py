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


@pytest.mark.bazel_cached
def test_html_comparison_normalizes_wrapper_uuids_and_preserves_need_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Random wrapper IDs are incidental; Need anchors and coverage values are the contract."""
    expected_path = tmp_path / "expected.html"
    actual_path = tmp_path / "actual.html"
    html = (
        '<div class="need_container docutils container" id="SNCB-1234abcd">'
        '<table id="REQ_1"><td>67%</td></table></div>'
        '<div class="need_container docutils container" id="SNCB-5678abcd">'
        '<table id="REQ_2"></table></div>'
        '<span id="SNCB-fedcba98">User-defined anchor</span>'
    )
    expected_path.write_text(html)
    changed_ids = html.replace("1234abcd", "abcdef12").replace("5678abcd", "abcdef34")
    actual_path.write_text(changed_ids)
    expected = _stub_expected_output_execution(monkeypatch, expected_path, actual_path)

    update_expected_output("fixture", expected)
    assert expected_path.read_text() == html

    for old, new in (
        ("REQ_1", "REQ_CHANGED"),
        ("67%", "68%"),
        ("fedcba98", "fedcba99"),
    ):
        expected_path.write_text(html)
        actual_path.write_text(changed_ids.replace(old, new))
        with pytest.raises(AssertionError, match="expected outputs changed"):
            update_expected_output("fixture", expected)
        normalized = expected_path.read_text()
        assert 'id="SNCB-00000001"' in normalized
        assert 'id="SNCB-00000002"' in normalized
        assert new in normalized


@pytest.mark.bazel_cached
def test_html_source_links_ignore_checkout_metadata_but_preserve_link_targets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A new checkout must pass; changed source files, lines and external links must fail."""
    expected_path = tmp_path / "expected.html"
    actual_path = tmp_path / "actual.html"
    prefix = "https://github.com/owner/repo/blob/" + "a" * 40 + "/"
    source = "src/tests/docs_bzl/scenarios/example/code.cc#L17"
    dependency = "external/dep/code.cc#L3"
    html = (
        '<span class="needs_source_code_link"><span class="needs_data">'
        f'<a href="{prefix}{source}">code.cc:17</a>'
        f'<a href="{prefix}{dependency}">dependency</a></span></div>'
        f'<a href="{prefix}{source}">Ordinary link</a>'
    )
    other_checkout = html.replace(
        prefix + source,
        "https://github.com/fork/project/blob/" + "b" * 40 + "/" + source,
        1,
    )
    expected_path.write_text(html)
    actual_path.write_text(other_checkout)
    expected = _stub_expected_output_execution(monkeypatch, expected_path, actual_path)

    update_expected_output("fixture", expected)
    assert expected_path.read_text() == html

    for old, new in (
        ("example/code.cc#L17", "example/other.cc#L17"),
        ("code.cc#L17", "code.cc#L18"),
        (prefix + dependency, prefix.replace("owner/repo", "other/repo") + dependency),
        (f'{prefix}{source}">Ordinary', f'{prefix}{source}0">Ordinary'),
    ):
        expected_path.write_text(html)
        actual_path.write_text(other_checkout.replace(old, new))
        with pytest.raises(AssertionError, match="expected outputs changed"):
            update_expected_output("fixture", expected)
