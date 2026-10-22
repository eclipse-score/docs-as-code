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
"""GitHub Actions metadata and published gh-pages baseline resolution."""

from __future__ import annotations

import argparse
import io
import json
import shutil
import subprocess
import tarfile
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from urllib.parse import quote

from .comparison import DocsDeltaError


@dataclass(frozen=True)
class GithubPullRequest:
    """The source revision that a PR documentation baseline must represent.

    ``base_ref`` selects the published documentation directory and ``base_sha``
    identifies the commit that directory must contain. These are separate
    because gh-pages may publish the branch after the PR event was created.
    """

    base_ref: str
    base_sha: str
    number: str | None


def workspace_path(environ: Mapping[str, str], relative_path: str) -> Path:
    """Resolve a workflow-relative path, with a cwd-based local fallback."""
    workspace = environ.get("GITHUB_WORKSPACE")
    if workspace:
        return Path(workspace) / relative_path
    return Path(relative_path)


def github_pull_request(environ: Mapping[str, str]) -> GithubPullRequest | None:
    """Read PR base ref/SHA from Actions metadata, if this is a PR event.

    The event payload is authoritative for PR identity. The dedicated base
    variables take precedence when present, since they describe the checkout
    context in which the workflow is running.
    """

    event_name = environ.get("GITHUB_EVENT_NAME")
    event_path = environ.get("GITHUB_EVENT_PATH")
    if event_name != "pull_request":
        return None
    if not event_path:
        raise DocsDeltaError(
            "GITHUB_EVENT_PATH is required to resolve a pull request baseline"
        )

    try:
        payload = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DocsDeltaError(
            f"cannot read GitHub event payload {event_path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise DocsDeltaError(f"GitHub event payload is not an object: {event_path}")

    event_payload = cast(dict[str, object], payload)
    pull_request_value = event_payload.get("pull_request")
    if not isinstance(pull_request_value, dict):
        return None
    pull_request = cast(dict[str, object], pull_request_value)
    base_value = pull_request.get("base")
    if not isinstance(base_value, dict):
        return None
    base = cast(dict[str, object], base_value)

    base_ref = environ.get("GITHUB_BASE_REF") or base.get("ref")
    base_sha = environ.get("GITHUB_BASE_SHA") or base.get("sha")
    if not isinstance(base_ref, str) or not base_ref:
        return None
    if not isinstance(base_sha, str) or not base_sha:
        return None

    number: object = pull_request.get("number")
    if not isinstance(number, int | str) or isinstance(number, bool):
        number = None
    else:
        number = str(number)
    return GithubPullRequest(base_ref=base_ref, base_sha=base_sha, number=number)


def _find_published_baseline_commit(
    gh_pages_dir: Path, pull_request: GithubPullRequest
) -> tuple[str | None, str]:
    """Find the newest published base-branch tree containing the PR base SHA.

    The docs publishing workflow updates a branch directory on ``gh-pages``
    only after a successful docs build. Looking up ``needs.json`` history for
    the base branch and checking its embedded source SHA avoids selecting a
    previous successful build when the current base commit has not been
    published. ``git log`` returns newest commits first, so the first match is
    the latest publication that represents this exact source revision.
    """

    if not gh_pages_dir.is_dir():
        return None, f"gh-pages checkout is missing: {gh_pages_dir}"

    try:
        git_check = subprocess.run(
            ["git", "-C", str(gh_pages_dir), "rev-parse", "--git-dir"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return None, f"cannot inspect gh-pages checkout {gh_pages_dir}: {exc}"
    if git_check.returncode != 0:
        return None, f"gh-pages checkout is not a Git repository: {gh_pages_dir}"

    # The Needs export carries the source revision that produced a published
    # docs tree. Searching this file's history also avoids treating an older
    # successful publication as the baseline for a newer, unpublished commit.
    needs_path = f"{pull_request.base_ref}/needs.json"
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(gh_pages_dir),
                "log",
                "--all",
                "--full-history",
                "--format=%H",
                "--",
                needs_path,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return None, f"cannot search gh-pages history: {exc}"
    if result.returncode != 0:
        detail = result.stderr.strip() or "git log failed"
        return None, f"cannot search gh-pages history: {detail}"

    candidate_commits = [
        line.strip() for line in result.stdout.splitlines() if line.strip()
    ]
    # ``git log`` is newest-first; stop at the most recent publication that
    # proves it was built from the PR's exact base SHA.
    for commit in candidate_commits:
        try:
            needs = subprocess.run(
                [
                    "git",
                    "-C",
                    str(gh_pages_dir),
                    "show",
                    f"{commit}:{needs_path}",
                ],
                check=False,
                capture_output=True,
            )
        except OSError as exc:
            return None, f"cannot inspect published needs JSON: {exc}"
        if needs.returncode == 0 and pull_request.base_sha.encode() in needs.stdout:
            return commit, ""

    return (
        None,
        f"no published {pull_request.base_ref} baseline contains "
        f"source commit {pull_request.base_sha}",
    )


def extract_git_tree(
    gh_pages_dir: Path, commit: str, tree_path: str, destination: Path
) -> None:
    """Copy a docs subtree from a commit into a temporary directory.

    ``git archive`` reads the selected immutable tree without checking out or
    disturbing the shared gh-pages worktree. Members are copied explicitly
    instead of using ``extractall`` so unexpected paths or special files in
    the archive cannot escape the temporary baseline directory.
    """

    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(gh_pages_dir),
                "archive",
                "--format=tar",
                f"{commit}:{tree_path}",
            ],
            check=False,
            capture_output=True,
        )
    except OSError as exc:
        raise DocsDeltaError(f"cannot extract gh-pages baseline: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.decode(errors="replace").strip() or "git archive failed"
        raise DocsDeltaError(f"cannot extract gh-pages baseline: {detail}")

    destination.mkdir(parents=True, exist_ok=True)
    try:
        with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r:") as archive:
            for member in archive.getmembers():
                relative = Path(member.name)
                if relative.is_absolute() or ".." in relative.parts:
                    raise DocsDeltaError(
                        f"gh-pages archive contains unsafe path: {member.name}"
                    )
                target = destination / relative
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    source = archive.extractfile(member)
                    if source is None:
                        raise DocsDeltaError(
                            f"cannot read gh-pages archive member: {member.name}"
                        )
                    with source, target.open("wb") as output:
                        shutil.copyfileobj(source, output)
                else:
                    raise DocsDeltaError(
                        f"unsupported gh-pages archive member: {member.name}"
                    )
    except (OSError, tarfile.TarError) as exc:
        raise DocsDeltaError(f"cannot extract gh-pages baseline: {exc}") from exc


@contextmanager
def resolved_baseline(
    args: argparse.Namespace,
    github_pull_request: GithubPullRequest | None,
    environ: Mapping[str, str],
) -> Iterator[tuple[Path | None, str]]:
    """Yield a baseline directory, or ``None`` plus a reportable reason.

    Directory mode is useful for local comparisons and explicit artifacts.
    PR Actions defaults to gh-pages mode, where the extracted directory only
    lives for the duration of this context manager. A baseline lookup failure
    is data for the report; malformed CLI choices remain hard errors.
    """

    if args.baseline_mode is None:
        # Local callers usually provide a directory. PR Actions has no such
        # artifact, so use the published branch history by default.
        mode = (
            "directory"
            if args.baseline_dir is not None or github_pull_request is None
            else "gh-pages"
        )
    else:
        mode = args.baseline_mode

    if mode == "directory":
        if args.baseline_dir is None:
            raise DocsDeltaError(
                "--baseline-dir is required outside GitHub pull request mode"
            )
        yield args.baseline_dir, ""
        return

    if args.baseline_dir is not None:
        raise DocsDeltaError(
            "--baseline-dir cannot be used with --baseline-mode gh-pages"
        )
    if github_pull_request is None:
        raise DocsDeltaError(
            "gh-pages baseline mode requires a GitHub pull request event"
        )

    gh_pages_dir = args.gh_pages_dir or workspace_path(environ, ".docs-baseline")
    commit, reason = _find_published_baseline_commit(gh_pages_dir, github_pull_request)
    if commit is None:
        yield None, reason
        return

    with tempfile.TemporaryDirectory(prefix="docs-delta-baseline-") as temporary_dir:
        baseline_dir = Path(temporary_dir)
        try:
            extract_git_tree(
                gh_pages_dir,
                commit,
                github_pull_request.base_ref,
                baseline_dir,
            )
        except DocsDeltaError as exc:
            yield None, str(exc)
            return
        yield baseline_dir, ""


def _github_url_defaults(
    environ: Mapping[str, str],
    github_pull_request: GithubPullRequest | None = None,
) -> tuple[str | None, str | None]:
    """Derive base and PR preview URLs from the repository and Actions context.

    PR previews conventionally live under ``pr-N``. Branch refs are URL-quoted
    as one segment so a feature branch containing ``/`` cannot be mistaken for
    a nested path under the Pages site.
    """

    repository = environ.get("GITHUB_REPOSITORY", "")
    if "/" not in repository:
        return None, None
    owner, name = repository.split("/", 1)
    if not owner or not name:
        return None, None
    pages_root = environ.get("GITHUB_PAGES_URL") or f"https://{owner}.github.io/{name}"
    base_ref = (
        github_pull_request.base_ref
        if github_pull_request
        else (environ.get("GITHUB_BASE_REF") or "main")
    )
    if github_pull_request and github_pull_request.number:
        pr_ref = f"pr-{github_pull_request.number}"
    else:
        pr_ref = (
            environ.get("GITHUB_HEAD_REF") or environ.get("GITHUB_REF_NAME") or base_ref
        )

    def pages_ref_url(ref: str) -> str:
        # A branch name is one URL path segment. In particular, a slash in a
        # feature branch must not become a second documentation path segment.
        return pages_root.rstrip("/") + "/" + quote(ref, safe="-._~")

    return (
        pages_ref_url(base_ref),
        pages_ref_url(pr_ref),
    )


def resolve_urls(
    args: argparse.Namespace,
    github_pull_request: GithubPullRequest | None,
    environ: Mapping[str, str],
) -> tuple[str, str]:
    """Use explicit URLs where supplied, otherwise require usable CI defaults."""
    defaults = _github_url_defaults(environ, github_pull_request)
    base_url = args.base_url or defaults[0]
    pr_url = args.pr_url or defaults[1]
    if not base_url or not pr_url:
        raise DocsDeltaError(
            "documentation URLs are required; provide --base-url and --pr-url "
            "or run in GitHub Actions with GITHUB_REPOSITORY set"
        )
    return base_url, pr_url
