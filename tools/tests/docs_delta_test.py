# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Unit and fixture-based integration tests for the documentation delta tool."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tools import docs_delta


def _need(docname: str, title: str, **extra: object) -> dict[str, object]:
    return {"id": title.lower(), "docname": docname, "title": title, **extra}


def _write_needs(directory: Path, needs: dict[str, dict[str, object]]) -> None:
    (directory / "needs.json").write_text(
        json.dumps({"versions": {"1": {"needs": needs}}}), encoding="utf-8"
    )


def _git(directory: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(directory), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )


def test_compare_needs_categorizes_changes_and_ignores_volatile_fields() -> None:
    baseline = {
        "same": _need(
            "same",
            "Same",
            id="same",
            lineno=10,
            source="old.rst",
            source_code_link="old-commit",
            testlink="old-result",
        ),
        "changed": _need(
            "changed",
            "Old",
            id="changed",
            lineno=10,
            source="old.rst",
            source_code_link="old-commit",
            testlink="old-result",
        ),
        "removed": _need("removed", "Removed", id="removed"),
    }
    current = {
        "same": _need(
            "same",
            "Same",
            id="same",
            lineno=999,
            source="new.rst",
            source_code_link="new-commit",
            testlink="new-result",
        ),
        "changed": _need(
            "changed",
            "New",
            id="changed",
            lineno=20,
            source="new.rst",
            source_code_link="new-commit",
            testlink="new-result",
        ),
        "added": _need("added", "Added", id="added"),
    }

    result = docs_delta.compare_needs(baseline, current)

    assert [entry.need_id for entry in result.added] == ["added"]
    assert [entry.need_id for entry in result.removed] == ["removed"]
    assert [entry.need_id for entry in result.modified] == ["changed"]
    assert result.modified[0].changed_fields == ("title",)
    assert result.unchanged_count == 1


def test_modified_need_reports_all_changed_fields_and_one_sided_links() -> None:
    result = docs_delta.render_report(
        docs_delta.NeedComparison(
            added=(docs_delta.NeedChange("added", None, _need("new/page", "Added")),),
            removed=(
                docs_delta.NeedChange("removed", _need("old/page", "Removed"), None),
            ),
            modified=(
                docs_delta.NeedChange(
                    "changed",
                    _need("old/page", "Old", tags=["old"], extra="before"),
                    _need("new/page", "New", tags=["new"], extra="after"),
                ),
            ),
            unchanged_count=0,
        ),
        docs_delta.PageComparison((), (), (), 0),
        base_url="https://docs.example/main",
        pr_url="https://docs.example/pr/1",
    )

    assert "[old](https://docs.example/main/old/page.html#changed)" in result
    assert "[new](https://docs.example/pr/1/new/page.html#changed)" in result
    assert '`extra`: "before" → "after"' in result
    assert '`tags`: ["old"] → ["new"]' in result
    assert "https://docs.example/pr/1/new/page.html#added" in result
    assert "https://docs.example/main/old/page.html#removed" in result


def test_large_changed_values_are_truncated() -> None:
    large_old = "a" * (docs_delta.MAX_RENDERED_VALUE_LENGTH + 20)
    large_new = "b" * (docs_delta.MAX_RENDERED_VALUE_LENGTH + 20)
    change = docs_delta.NeedChange(
        "changed",
        _need("page", "Old", details=large_old),
        _need("page", "New", details=large_new),
    )

    report = docs_delta.render_report(
        docs_delta.NeedComparison((), (), (change,), 0),
        docs_delta.PageComparison((), (), (), 0),
        base_url="https://docs.example/main",
        pr_url="https://docs.example/pr/1",
    )

    assert "…" in report
    assert large_old not in report
    assert large_new not in report


def test_normalize_html_ignores_generated_metadata_but_keeps_content_changes() -> None:
    old = (
        '<html data-build-timestamp="2026-09-01T10:00:00Z">\r\n'
        '<meta name="generator" content="Sphinx 8">\r\n'
        "<!-- generated at 10:00 -->\r\n"
        "<p>Documentation</p>  \r\n</html>"
    )
    new = (
        '<html data-build-timestamp="2026-09-02T10:00:00Z">\n'
        '<meta name="generator" content="Sphinx 8">\n'
        "<!-- generated at 11:00 -->\n"
        "<p>Documentation</p>\n</html>"
    )

    assert docs_delta.normalize_html(old) == docs_delta.normalize_html(new)
    assert docs_delta.normalize_html(new).replace(
        "Documentation", "Changed"
    ) != docs_delta.normalize_html(old)


def test_compare_html_categorizes_added_removed_modified_and_unchanged(
    tmp_path: Path,
) -> None:
    baseline = tmp_path / "baseline"
    current = tmp_path / "current"
    (baseline / "nested").mkdir(parents=True)
    (current / "nested").mkdir(parents=True)
    (baseline / "same.html").write_text("<p>same</p>\n", encoding="utf-8")
    (current / "same.html").write_text("<p>same</p>\n", encoding="utf-8")
    (baseline / "changed.html").write_text("<p>old</p>\n", encoding="utf-8")
    (current / "changed.html").write_text("<p>new</p>\n", encoding="utf-8")
    (baseline / "removed.html").write_text("<p>removed</p>\n", encoding="utf-8")
    (current / "added.html").write_text("<p>added</p>\n", encoding="utf-8")
    (baseline / "nested/page.html").write_text("<p>old</p>\n", encoding="utf-8")
    (current / "nested/page.html").write_text("<p>old</p>\n", encoding="utf-8")

    result = docs_delta.compare_html(baseline, current)

    assert [entry.path for entry in result.added] == ["added.html"]
    assert [entry.path for entry in result.removed] == ["removed.html"]
    assert [entry.path for entry in result.modified] == ["changed.html"]
    assert result.unchanged_count == 2


def test_detail_threshold_is_independent_for_needs_and_pages() -> None:
    needs = docs_delta.NeedComparison(
        added=tuple(
            docs_delta.NeedChange(str(index), None, _need("page", str(index)))
            for index in range(16)
        ),
        removed=(),
        modified=(),
        unchanged_count=0,
    )
    pages = docs_delta.PageComparison(
        added=tuple(docs_delta.PageChange(f"page-{index}.html") for index in range(2)),
        removed=(),
        modified=(),
        unchanged_count=0,
    )

    report = docs_delta.render_report(
        needs,
        pages,
        base_url="https://docs.example/main",
        pr_url="https://docs.example/pr/1",
    )

    assert "16 entries changed; details omitted." in report
    assert "`page-0.html`" in report
    assert "`0`" not in report


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


def test_cli_writes_complete_fixture_report(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    current = tmp_path / "current"
    baseline.mkdir()
    current.mkdir()
    _write_needs(
        baseline,
        {
            "same": _need("same", "Same", id="same"),
            "changed": _need("guide", "Old title", id="changed"),
            "removed": _need("removed", "Removed", id="removed"),
        },
    )
    _write_needs(
        current,
        {
            "same": _need("same", "Same", id="same"),
            "changed": _need("guide", "New title", id="changed"),
            "added": _need("new", "Added", id="added"),
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
    _write_needs(baseline, {})
    _write_needs(current, {})
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
    _git(gh_pages, "config", "user.name", "Documentation Delta Test")
    _git(gh_pages, "config", "user.email", "docs-delta@example.invalid")

    base_sha = "0123456789abcdef0123456789abcdef01234567"
    latest_sha = "fedcba9876543210fedcba9876543210fedcba98"
    main_docs = gh_pages / "main"
    main_docs.mkdir()
    _write_needs(
        main_docs,
        {
            "need": _need(
                "guide", "Base publication", id="need", source_code_link=base_sha
            )
        },
    )
    (main_docs / "guide.html").write_text("<p>Base publication</p>\n", encoding="utf-8")
    _git(gh_pages, "add", ".")
    _git(gh_pages, "commit", "-m", "Publish base documentation")

    _write_needs(
        main_docs,
        {
            "need": _need(
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
    _git(gh_pages, "add", ".")
    _git(gh_pages, "commit", "-m", "Republish base documentation")
    newer_base_publication_commit = subprocess.run(
        ["git", "-C", str(gh_pages), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    _write_needs(
        main_docs,
        {
            "need": _need(
                "guide", "Latest publication", id="need", source_code_link=latest_sha
            )
        },
    )
    (main_docs / "guide.html").write_text(
        "<p>Latest publication</p>\n", encoding="utf-8"
    )
    _git(gh_pages, "add", ".")
    _git(gh_pages, "commit", "-m", "Publish latest documentation")

    selected_commit, selection_reason = docs_delta._find_published_baseline_commit(
        gh_pages,
        docs_delta.GithubPullRequest("main", base_sha, "123"),
    )
    assert selected_commit == newer_base_publication_commit, selection_reason

    current = tmp_path / "docs-artifact"
    current.mkdir()
    _write_needs(
        current,
        {
            "need": _need(
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
