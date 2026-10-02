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
"""Tests for local and GitHub Actions command-line behavior."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tools import docs_delta
from tools.tests.docs_delta_test_support import git, need, write_needs


def test_missing_baseline_writes_unavailable_report(tmp_path: Path) -> None:
    output = tmp_path / "nested" / "delta.md"

    assert (
        docs_delta.main(
            [
                "--baseline-dir",
                str(tmp_path / "missing"),
                "--current-dir",
                str(tmp_path / "current"),
                "--base-url",
                "https://docs.example/main",
                "--pr-url",
                "https://docs.example/pr/1",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    assert "## Delta unavailable" in output.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("mode", "extra_args", "message"),
    [
        ("directory", [], "--baseline-dir is required"),
        ("gh-pages", [], "requires a GitHub pull request event"),
        (
            "gh-pages",
            ["--baseline-dir", "somewhere"],
            "cannot be used with --baseline-mode gh-pages",
        ),
    ],
)
def test_baseline_mode_rejects_incompatible_options(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mode: str,
    extra_args: list[str],
    message: str,
) -> None:
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)

    result = docs_delta.main(
        [
            "--baseline-mode",
            mode,
            *extra_args,
            "--current-dir",
            str(tmp_path / "current"),
            "--output",
            str(tmp_path / "delta.md"),
        ]
    )

    assert result == 2
    assert message in capsys.readouterr().err


def test_cli_reports_missing_current_directory_as_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    baseline = tmp_path / "baseline"
    baseline.mkdir()
    write_needs(baseline, {})

    result = docs_delta.main(
        [
            "--baseline-dir",
            str(baseline),
            "--current-dir",
            str(tmp_path / "missing-current"),
            "--base-url",
            "https://docs.example/main",
            "--pr-url",
            "https://docs.example/pr/1",
            "--output",
            str(tmp_path / "delta.md"),
        ]
    )

    assert result == 2
    assert "documentation directory is missing" in capsys.readouterr().err


def test_cli_writes_complete_fixture_report(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    current = tmp_path / "current"
    baseline.mkdir()
    current.mkdir()
    write_needs(
        baseline,
        {
            "same": need("same", "Same", id="same"),
            "changed": need("guide", "Old title", id="changed"),
            "removed": need("removed", "Removed", id="removed"),
        },
    )
    write_needs(
        current,
        {
            "same": need("same", "Same", id="same"),
            "changed": need("guide", "New title", id="changed"),
            "added": need("new", "Added", id="added"),
        },
    )
    (baseline / "guide.html").write_text("<p>old</p>\n", encoding="utf-8")
    (current / "guide.html").write_text("<p>new</p>\n", encoding="utf-8")
    (current / "new.html").write_text("<p>new page</p>\n", encoding="utf-8")
    output = tmp_path / "delta.md"

    assert (
        docs_delta.main(
            [
                "--baseline-dir",
                str(baseline),
                "--current-dir",
                str(current),
                "--base-url",
                "https://docs.example/main",
                "--pr-url",
                "https://docs.example/pr/1",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    report = output.read_text(encoding="utf-8")
    assert "Needs: 1 added, 1 removed, 1 modified, 1 unchanged" in report
    assert "Rendered pages: 1 added, 0 removed, 1 modified, 0 unchanged" in report
    assert '`title`: "Old title" → "New title"' in report
    assert (
        "`guide.html` ([old](https://docs.example/main/guide.html) / [new](https://docs.example/pr/1/guide.html))"
        in report
    )


def test_cli_uses_github_environment_urls_when_options_are_omitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    baseline = tmp_path / "baseline"
    current = tmp_path / "current"
    baseline.mkdir()
    current.mkdir()
    write_needs(baseline, {})
    write_needs(current, {})
    monkeypatch.setenv("GITHUB_REPOSITORY", "eclipse-score/docs-as-code")
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    monkeypatch.setenv("GITHUB_HEAD_REF", "feature/docs-delta")
    output = tmp_path / "delta.md"

    assert (
        docs_delta.main(
            [
                "--baseline-dir",
                str(baseline),
                "--current-dir",
                str(current),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    report = output.read_text(encoding="utf-8")
    assert "https://eclipse-score.github.io/docs-as-code/main" in report
    assert "https://eclipse-score.github.io/docs-as-code/feature%2Fdocs-delta" in report


def test_cli_automatically_selects_matching_gh_pages_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PR mode must select the historical publication matching the base SHA."""

    gh_pages = tmp_path / ".docs-baseline"
    gh_pages.mkdir()
    subprocess.run(
        ["git", "init", "--initial-branch=gh-pages", str(gh_pages)],
        check=True,
        capture_output=True,
        text=True,
    )
    git(gh_pages, "config", "user.name", "Documentation Delta Test")
    git(gh_pages, "config", "user.email", "docs-delta@example.invalid")

    base_sha = "0123456789abcdef0123456789abcdef01234567"
    latest_sha = "fedcba9876543210fedcba9876543210fedcba98"
    main_docs = gh_pages / "main"
    main_docs.mkdir()
    write_needs(
        main_docs,
        {
            "need": need(
                "guide", "Base publication", id="need", source_code_link=base_sha
            )
        },
    )
    (main_docs / "guide.html").write_text("<p>Base publication</p>\n", encoding="utf-8")
    git(gh_pages, "add", ".")
    git(gh_pages, "commit", "-m", "Publish base documentation")

    write_needs(
        main_docs,
        {
            "need": need(
                "guide",
                "Newer base publication",
                id="need",
                source_code_link=base_sha,
            )
        },
    )
    (main_docs / "guide.html").write_text(
        "<p>Newer base publication</p>\n", encoding="utf-8"
    )
    git(gh_pages, "add", ".")
    git(gh_pages, "commit", "-m", "Republish base documentation")
    write_needs(
        main_docs,
        {
            "need": need(
                "guide", "Latest publication", id="need", source_code_link=latest_sha
            )
        },
    )
    (main_docs / "guide.html").write_text(
        "<p>Latest publication</p>\n", encoding="utf-8"
    )
    git(gh_pages, "add", ".")
    git(gh_pages, "commit", "-m", "Publish latest documentation")

    current = tmp_path / "docs-artifact"
    current.mkdir()
    write_needs(
        current,
        {
            "need": need(
                "guide",
                "Newer base publication",
                id="need",
                source_code_link="pr-sha",
            )
        },
    )
    (current / "guide.html").write_text(
        "<p>Newer base publication</p>\n", encoding="utf-8"
    )

    event = tmp_path / "event.json"
    event.write_text(
        json.dumps(
            {
                "pull_request": {
                    "number": 123,
                    "base": {"ref": "main", "sha": base_sha},
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))
    monkeypatch.setenv("GITHUB_REPOSITORY", "eclipse-score/docs-as-code")
    monkeypatch.setenv("GITHUB_BASE_REF", "main")

    assert docs_delta.main([]) == 0
    report = (current / "docs-delta.md").read_text(encoding="utf-8")
    assert "Needs: 0 added, 0 removed, 0 modified, 1 unchanged" in report
    assert "Rendered pages: 0 added, 0 removed, 0 modified, 1 unchanged" in report
    assert "https://eclipse-score.github.io/docs-as-code/pr-123" in report
