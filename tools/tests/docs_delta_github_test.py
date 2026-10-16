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
"""Tests for Actions metadata and gh-pages baseline resolution."""

from __future__ import annotations

import io
import json
import subprocess
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools import docs_delta
from tools.docs_delta import github
from tools.tests.docs_delta_test_support import git, need, write_needs


def test_pull_request_metadata_is_only_read_for_pr_events(
    tmp_path: Path,
) -> None:
    assert github.github_pull_request({"GITHUB_EVENT_NAME": "push"}) is None

    event = tmp_path / "event.json"
    event.write_text("not JSON", encoding="utf-8")
    with pytest.raises(docs_delta.DocsDeltaError, match="cannot read GitHub event"):
        github.github_pull_request(
            {
                "GITHUB_EVENT_NAME": "pull_request",
                "GITHUB_EVENT_PATH": str(event),
            }
        )


def test_workspace_path_falls_back_to_relative_paths_locally() -> None:
    assert github.workspace_path({}, "docs-artifact") == Path("docs-artifact")
    assert github.workspace_path(
        {"GITHUB_WORKSPACE": "/workspace"}, "docs-artifact"
    ) == Path("/workspace/docs-artifact")


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"pull_request": "not an object"},
        {"pull_request": {"base": "not an object"}},
        {"pull_request": {"base": {"ref": "", "sha": ""}}},
    ],
)
def test_incomplete_pull_request_payload_does_not_create_a_baseline(
    tmp_path: Path, payload: object
) -> None:
    event = tmp_path / "event.json"
    event.write_text(json.dumps(payload), encoding="utf-8")

    assert (
        github.github_pull_request(
            {
                "GITHUB_EVENT_NAME": "pull_request",
                "GITHUB_EVENT_PATH": str(event),
            }
        )
        is None
    )


def test_non_object_event_payload_is_rejected(tmp_path: Path) -> None:
    event = tmp_path / "event.json"
    event.write_text("[]", encoding="utf-8")

    with pytest.raises(docs_delta.DocsDeltaError, match="payload is not an object"):
        github.github_pull_request(
            {
                "GITHUB_EVENT_NAME": "pull_request",
                "GITHUB_EVENT_PATH": str(event),
            }
        )


def test_pull_request_payload_rejects_missing_event_path() -> None:
    with pytest.raises(
        docs_delta.DocsDeltaError, match="GITHUB_EVENT_PATH is required"
    ):
        github.github_pull_request({"GITHUB_EVENT_NAME": "pull_request"})


def test_pull_request_metadata_uses_actions_overrides_and_ignores_boolean_number(
    tmp_path: Path,
) -> None:
    event = tmp_path / "event.json"
    event.write_text(
        json.dumps(
            {
                "pull_request": {
                    "number": True,
                    "base": {"ref": "event-main", "sha": "event-sha"},
                }
            }
        ),
        encoding="utf-8",
    )

    pull_request = github.github_pull_request(
        {
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_EVENT_PATH": str(event),
            "GITHUB_BASE_REF": "actions-main",
            "GITHUB_BASE_SHA": "actions-sha",
        }
    )

    assert pull_request == github.GithubPullRequest(
        base_ref="actions-main", base_sha="actions-sha", number=None
    )


def test_resolve_urls_requires_complete_defaults() -> None:
    args = docs_delta.cli.argument_parser().parse_args([])

    with pytest.raises(
        docs_delta.DocsDeltaError, match="documentation URLs are required"
    ):
        github.resolve_urls(args, None, {})


def test_unsafe_archive_path_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive_data = io.BytesIO()
    with tarfile.open(fileobj=archive_data, mode="w") as archive:
        member = tarfile.TarInfo("../escaped.html")
        member.size = len(b"unsafe")
        archive.addfile(member, io.BytesIO(b"unsafe"))

    monkeypatch.setattr(
        github.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0, stdout=archive_data.getvalue(), stderr=b""
        ),
    )
    destination = tmp_path / "baseline"

    with pytest.raises(docs_delta.DocsDeltaError, match="unsafe path"):
        github.extract_git_tree(tmp_path, "commit", "main", destination)

    assert not (tmp_path / "escaped.html").exists()


def test_unsupported_archive_member_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive_data = io.BytesIO()
    with tarfile.open(fileobj=archive_data, mode="w") as archive:
        member = tarfile.TarInfo("external-link")
        member.type = tarfile.SYMTYPE
        member.linkname = "outside"
        archive.addfile(member)

    monkeypatch.setattr(
        github.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0, stdout=archive_data.getvalue(), stderr=b""
        ),
    )

    with pytest.raises(
        docs_delta.DocsDeltaError, match="unsupported gh-pages archive member"
    ):
        github.extract_git_tree(tmp_path, "commit", "main", tmp_path / "baseline")


def test_archive_command_failure_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        github.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1, stdout=b"", stderr=b"missing tree"
        ),
    )

    with pytest.raises(docs_delta.DocsDeltaError, match="missing tree"):
        github.extract_git_tree(tmp_path, "commit", "main", tmp_path / "baseline")


def test_missing_gh_pages_checkout_writes_unavailable_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    current = tmp_path / "docs-artifact"
    current.mkdir()
    event = tmp_path / "event.json"
    event.write_text(
        json.dumps(
            {
                "pull_request": {
                    "number": 125,
                    "base": {"ref": "main", "sha": "base-sha"},
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))

    assert docs_delta.main([]) == 0
    report_text = (current / "docs-delta.md").read_text(encoding="utf-8")
    assert "gh-pages checkout is missing" in report_text


def test_non_git_gh_pages_checkout_writes_unavailable_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    gh_pages = tmp_path / ".docs-baseline"
    gh_pages.mkdir()
    current = tmp_path / "docs-artifact"
    current.mkdir()
    event = tmp_path / "event.json"
    event.write_text(
        json.dumps(
            {
                "pull_request": {
                    "number": 126,
                    "base": {"ref": "main", "sha": "base-sha"},
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))

    assert docs_delta.main([]) == 0
    report_text = (current / "docs-delta.md").read_text(encoding="utf-8")
    assert "gh-pages checkout is not a Git repository" in report_text


def test_unpublished_base_commit_writes_unavailable_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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
    main_docs = gh_pages / "main"
    main_docs.mkdir()
    write_needs(main_docs, {"need": need("guide", "Published", id="need")})
    git(gh_pages, "add", ".")
    git(gh_pages, "commit", "-m", "Publish older documentation")

    current = tmp_path / "docs-artifact"
    current.mkdir()
    write_needs(current, {})
    event = tmp_path / "event.json"
    event.write_text(
        json.dumps(
            {
                "pull_request": {
                    "number": 124,
                    "base": {
                        "ref": "main",
                        "sha": "abcdef0123456789abcdef0123456789abcdef01",
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))

    assert docs_delta.main([]) == 0
    report_text = (current / "docs-delta.md").read_text(encoding="utf-8")
    assert "## Delta unavailable" in report_text
    assert "no published main baseline contains source commit" in report_text
