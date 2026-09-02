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
"""Compare rendered documentation trees and write a Markdown delta report.

The tool works on artifacts already produced by a docs build. In GitHub Actions
it can additionally resolve the matching published baseline from a local,
full-history checkout of ``gh-pages``. It never fetches from GitHub or invokes
Sphinx, which keeps the comparison useful both in CI and as a local command.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

JsonObject = dict[str, object]
NeedMap = Mapping[str, JsonObject]

DETAIL_LIMIT = 15
MAX_RENDERED_VALUE_LENGTH = 600

# These values are generated from source/test links or Sphinx's internal
# bookkeeping. They can change when a build is moved to another checkout or
# when the same source is rebuilt, without representing a documentation delta.
# Keep this list deliberately explicit: fields not listed here are part of the
# comparison contract and must be reviewed when Sphinx-Needs adds new output.
VOLATILE_NEED_FIELDS = frozenset(
    {
        "lineno",
        "lineno_content",
        "source",
        "target_id",
        "is_modified",
        "source_code_link",
        "testlink",
    }
)

_MISSING = object()
_META_TAG = re.compile(r"<meta\b[^>]*>", re.IGNORECASE)
_META_ATTRIBUTE = re.compile(
    r"(?:name|property|itemprop)\s*=\s*([\"'])(.*?)\1", re.IGNORECASE
)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.IGNORECASE | re.DOTALL)
_VOLATILE_ATTRIBUTE = re.compile(
    r"\s+data-(?:build|generated|timestamp|last-modified)(?:-[\w-]+)?\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)",
    re.IGNORECASE,
)
_VOLATILE_META_NAMES = frozenset(
    {
        "build-date",
        "build_date",
        "created",
        "date",
        "generated",
        "generated-at",
        "generated_at",
        "generator",
        "last-modified",
        "last_modified",
        "timestamp",
    }
)
_VOLATILE_COMMENT_WORDS = re.compile(
    r"\b(?:build|built|generated|generator|last\s+updated|timestamp)\b",
    re.IGNORECASE,
)


class DocsDeltaError(ValueError):
    """A user-actionable input or report-generation error."""


@dataclass(frozen=True)
class GithubPullRequest:
    """Pull request provenance obtained from the Actions environment."""

    base_ref: str
    base_sha: str
    number: str | None


@dataclass(frozen=True)
class NeedChange:
    """One Need and, for modified entries, its two versions."""

    need_id: str
    baseline: JsonObject | None
    current: JsonObject | None

    @property
    def changed_fields(self) -> tuple[str, ...]:
        """Return changed non-volatile fields in deterministic order."""

        if self.baseline is None or self.current is None:
            return ()
        names = set(self.baseline) | set(self.current)
        return tuple(
            sorted(
                name
                for name in names
                if name not in VOLATILE_NEED_FIELDS
                and not _json_values_equal(
                    self.baseline.get(name, _MISSING),
                    self.current.get(name, _MISSING),
                )
            )
        )


@dataclass(frozen=True)
class NeedComparison:
    """Categorized comparison result for a pair of Need inventories."""

    added: tuple[NeedChange, ...]
    removed: tuple[NeedChange, ...]
    modified: tuple[NeedChange, ...]
    unchanged_count: int


@dataclass(frozen=True)
class PageChange:
    """One rendered HTML path that was added, removed, or modified."""

    path: str


@dataclass(frozen=True)
class PageComparison:
    """Categorized comparison result for rendered HTML pages."""

    added: tuple[PageChange, ...]
    removed: tuple[PageChange, ...]
    modified: tuple[PageChange, ...]
    unchanged_count: int


def _json_values_equal(left: object, right: object) -> bool:
    """Compare JSON values without conflating booleans and numbers."""

    if left is _MISSING or right is _MISSING:
        return left is right
    return json.dumps(left, sort_keys=True, ensure_ascii=False) == json.dumps(
        right, sort_keys=True, ensure_ascii=False
    )


def _flatten_needs(path: Path) -> dict[str, JsonObject]:
    """Load all Need entries from every version in a Sphinx-Needs export."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DocsDeltaError(f"cannot read needs JSON {path}: {exc}") from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("versions"), dict):
        raise DocsDeltaError(f"needs JSON has no versions map: {path}")

    result: dict[str, JsonObject] = {}
    for version in payload["versions"].values():
        if not isinstance(version, dict) or not isinstance(version.get("needs"), dict):
            continue
        for need_id, need in version["needs"].items():
            if not isinstance(need_id, str) or not isinstance(need, dict):
                raise DocsDeltaError(f"invalid Need entry in {path}")
            result[need_id] = need
    return result


def load_needs(directory: Path) -> dict[str, JsonObject]:
    """Load the root ``needs.json`` file from a documentation directory."""

    needs_path = directory / "needs.json"
    if not needs_path.is_file():
        raise DocsDeltaError(f"needs JSON is missing: {needs_path}")
    return _flatten_needs(needs_path)


def compare_needs(baseline: NeedMap, current: NeedMap) -> NeedComparison:
    """Compare Needs by ID while ignoring only the volatile field allowlist."""

    added: list[NeedChange] = []
    removed: list[NeedChange] = []
    modified: list[NeedChange] = []
    unchanged_count = 0

    for need_id in sorted(set(baseline) | set(current)):
        old = baseline.get(need_id)
        new = current.get(need_id)
        change = NeedChange(need_id, old, new)
        if old is None:
            added.append(change)
        elif new is None:
            removed.append(change)
        elif change.changed_fields:
            modified.append(change)
        else:
            unchanged_count += 1

    return NeedComparison(
        added=tuple(added),
        removed=tuple(removed),
        modified=tuple(modified),
        unchanged_count=unchanged_count,
    )


def _html_metadata_name(tag: str) -> str | None:
    for match in _META_ATTRIBUTE.finditer(tag):
        name = match.group(2).lower()
        if name in _VOLATILE_META_NAMES:
            return name
    return None


def normalize_html(content: str) -> str:
    """Normalize generated HTML without hiding ordinary page content changes."""

    normalized = content.replace("\r\n", "\n").replace("\r", "\n")

    def remove_meta(match: re.Match[str]) -> str:
        return "" if _html_metadata_name(match.group(0)) else match.group(0)

    normalized = _META_TAG.sub(remove_meta, normalized)

    def remove_comment(match: re.Match[str]) -> str:
        return "" if _VOLATILE_COMMENT_WORDS.search(match.group(0)) else match.group(0)

    normalized = _HTML_COMMENT.sub(remove_comment, normalized)
    normalized = _VOLATILE_ATTRIBUTE.sub("", normalized)
    normalized = "\n".join(line.rstrip() for line in normalized.splitlines())
    return normalized.strip()


def _html_files(directory: Path) -> dict[str, str]:
    """Return normalized HTML keyed by POSIX-relative path."""

    if not directory.is_dir():
        raise DocsDeltaError(f"documentation directory is missing: {directory}")
    result: dict[str, str] = {}
    for path in sorted(directory.rglob("*.html")):
        if path.is_file():
            relative = path.relative_to(directory).as_posix()
            try:
                result[relative] = normalize_html(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError) as exc:
                raise DocsDeltaError(
                    f"cannot read rendered page {path}: {exc}"
                ) from exc
    return result


def compare_html(baseline_dir: Path, current_dir: Path) -> PageComparison:
    """Compare normalized recursive HTML output from two build directories."""

    baseline = _html_files(baseline_dir)
    current = _html_files(current_dir)
    added: list[PageChange] = []
    removed: list[PageChange] = []
    modified: list[PageChange] = []
    unchanged_count = 0

    for path in sorted(set(baseline) | set(current)):
        old = baseline.get(path)
        new = current.get(path)
        change = PageChange(path)
        if old is None:
            added.append(change)
        elif new is None:
            removed.append(change)
        elif old != new:
            modified.append(change)
        else:
            unchanged_count += 1

    return PageComparison(
        added=tuple(added),
        removed=tuple(removed),
        modified=tuple(modified),
        unchanged_count=unchanged_count,
    )


def _url_with_path(base_url: str, relative_path: str, anchor: str | None = None) -> str:
    url = (
        base_url.rstrip("/")
        + "/"
        + "/".join(
            quote(part, safe="-._~") for part in relative_path.strip("/").split("/")
        )
    )
    if anchor:
        url += "#" + quote(anchor, safe="-._~")
    return url


def _need_url(base_url: str, need: Mapping[str, object]) -> str | None:
    docname = need.get("docname")
    if not isinstance(docname, str) or not docname.strip():
        return None
    rendered_name = docname.strip("/")
    if not rendered_name.endswith(".html"):
        rendered_name += ".html"
    return _url_with_path(base_url, rendered_name)


def _need_link(base_url: str, need_id: str, need: Mapping[str, object]) -> str | None:
    page_url = _need_url(base_url, need)
    if page_url is None:
        return None
    return page_url + "#" + quote(need_id, safe="-._~")


def _markdown_link(label: str, url: str | None) -> str:
    if url is None:
        return f"`{label}`"
    safe_label = label.replace("[", "\\[").replace("]", "\\]")
    return f"[{safe_label}]({url})"


def _display_name(need: Mapping[str, object]) -> str:
    for field in ("title", "name"):
        value = need.get(field)
        if isinstance(value, str) and value:
            return value
    return ""


def _format_value(value: object) -> str:
    if value is _MISSING:
        return "(missing)"
    rendered = json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    if len(rendered) > MAX_RENDERED_VALUE_LENGTH:
        rendered = rendered[:MAX_RENDERED_VALUE_LENGTH] + "…"
    return rendered.replace("`", "\\`").replace("\n", " ")


def _format_need_entry(
    change: NeedChange, *, base_url: str, pr_url: str, include_diff: bool = False
) -> list[str]:
    need = change.current or change.baseline
    assert need is not None
    links = []
    old_link = (
        _need_link(base_url, change.need_id, change.baseline)
        if change.baseline
        else None
    )
    new_link = (
        _need_link(pr_url, change.need_id, change.current) if change.current else None
    )
    if old_link:
        links.append(_markdown_link("old", old_link))
    if new_link:
        links.append(_markdown_link("new", new_link))
    link_text = " / ".join(links)
    title = _display_name(need)
    suffix = f" — {title}" if title else ""
    line = f"- `{change.need_id}`{suffix}"
    if link_text:
        line += f" ({link_text})"
    result = [line]
    if include_diff:
        assert change.baseline is not None and change.current is not None
        for field in change.changed_fields:
            result.append(
                f"  - `{field}`: {_format_value(change.baseline.get(field, _MISSING))} "
                f"→ {_format_value(change.current.get(field, _MISSING))}"
            )
    return result


def _format_page_entry(
    change: PageChange, *, base_url: str, pr_url: str, kind: str
) -> str:
    old = _url_with_path(base_url, change.path) if kind != "added" else None
    new = _url_with_path(pr_url, change.path) if kind != "removed" else None
    links = []
    if old:
        links.append(_markdown_link("old", old))
    if new:
        links.append(_markdown_link("new", new))
    return f"- `{change.path}` ({' / '.join(links)})"


def _section(
    lines: list[str],
    title: str,
    entries: Sequence[object],
    formatter,
    *,
    base_url: str,
    pr_url: str,
    kind: str = "",
) -> None:
    if not entries:
        return
    lines.extend([f"### {title} ({len(entries)})", ""])
    if len(entries) > DETAIL_LIMIT:
        lines.extend([f"{len(entries)} entries changed; details omitted.", ""])
        return
    for entry in entries:
        if isinstance(entry, NeedChange):
            lines.extend(
                formatter(
                    entry,
                    base_url=base_url,
                    pr_url=pr_url,
                    include_diff=kind == "modified",
                )
            )
        else:
            lines.append(formatter(entry, base_url=base_url, pr_url=pr_url, kind=kind))
    lines.append("")


def render_report(
    needs: NeedComparison,
    pages: PageComparison,
    *,
    base_url: str,
    pr_url: str,
) -> str:
    """Render a deterministic Markdown report for comparison results."""

    lines = [
        "# Documentation delta",
        "",
        f"Baseline: {_markdown_link(base_url, base_url)}  ",
        f"PR preview: {_markdown_link(pr_url, pr_url)}",
        "",
        "## Summary",
        "",
        f"- Needs: {len(needs.added)} added, {len(needs.removed)} removed, "
        f"{len(needs.modified)} modified, {needs.unchanged_count} unchanged",
        f"- Rendered pages: {len(pages.added)} added, {len(pages.removed)} removed, "
        f"{len(pages.modified)} modified, {pages.unchanged_count} unchanged",
        "",
        "## Needs",
        "",
    ]
    _section(
        lines,
        "Added",
        needs.added,
        _format_need_entry,
        base_url=base_url,
        pr_url=pr_url,
        kind="added",
    )
    _section(
        lines,
        "Removed",
        needs.removed,
        _format_need_entry,
        base_url=base_url,
        pr_url=pr_url,
        kind="removed",
    )
    _section(
        lines,
        "Modified",
        needs.modified,
        _format_need_entry,
        base_url=base_url,
        pr_url=pr_url,
        kind="modified",
    )
    lines.extend(["## Rendered HTML pages", ""])
    _section(
        lines,
        "Added",
        pages.added,
        _format_page_entry,
        base_url=base_url,
        pr_url=pr_url,
        kind="added",
    )
    _section(
        lines,
        "Removed",
        pages.removed,
        _format_page_entry,
        base_url=base_url,
        pr_url=pr_url,
        kind="removed",
    )
    _section(
        lines,
        "Modified",
        pages.modified,
        _format_page_entry,
        base_url=base_url,
        pr_url=pr_url,
        kind="modified",
    )
    return "\n".join(lines).rstrip() + "\n"


def unavailable_report(reason: str) -> str:
    """Render the successful, explicit report used when baseline is unavailable."""

    return (
        "# Documentation delta\n\n"
        "## Delta unavailable\n\n"
        f"The documentation baseline is unavailable: {reason}\n"
    )


def _write_report(path: Path, content: str) -> None:
    """Atomically write the report so a failed run never leaves partial Markdown."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    file_descriptor: int | None = None
    try:
        file_descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as output:
            file_descriptor = None
            output.write(content)
            output.flush()
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if file_descriptor is not None:
            os.close(file_descriptor)
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _workspace_path(environ: Mapping[str, str], relative_path: str) -> Path:
    workspace = environ.get("GITHUB_WORKSPACE")
    if workspace:
        return Path(workspace) / relative_path
    return Path(relative_path)


def _github_pull_request(environ: Mapping[str, str]) -> GithubPullRequest | None:
    """Read pull request provenance from standard GitHub Actions variables."""

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

    pull_request = payload.get("pull_request")
    if not isinstance(pull_request, dict):
        return None
    base = pull_request.get("base")
    if not isinstance(base, dict):
        return None

    base_ref = environ.get("GITHUB_BASE_REF") or base.get("ref")
    base_sha = environ.get("GITHUB_BASE_SHA") or base.get("sha")
    if not isinstance(base_ref, str) or not base_ref:
        return None
    if not isinstance(base_sha, str) or not base_sha:
        return None

    number = pull_request.get("number")
    if not isinstance(number, int | str) or isinstance(number, bool):
        number = None
    else:
        number = str(number)
    return GithubPullRequest(base_ref=base_ref, base_sha=base_sha, number=number)


def _find_published_baseline_commit(
    gh_pages_dir: Path, pull_request: GithubPullRequest
) -> tuple[str | None, str]:
    """Find the newest gh-pages commit whose generated Needs contain the base SHA."""

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


def _extract_git_tree(
    gh_pages_dir: Path, commit: str, tree_path: str, destination: Path
) -> None:
    """Extract one published documentation tree without changing the checkout."""

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
def _resolved_baseline(
    args: argparse.Namespace,
    github_pull_request: GithubPullRequest | None,
    environ: Mapping[str, str],
) -> Iterator[tuple[Path | None, str]]:
    """Resolve either a directory baseline or a published gh-pages baseline."""

    if args.baseline_mode is None:
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

    gh_pages_dir = args.gh_pages_dir or _workspace_path(environ, ".docs-baseline")
    commit, reason = _find_published_baseline_commit(gh_pages_dir, github_pull_request)
    if commit is None:
        yield None, reason
        return

    with tempfile.TemporaryDirectory(prefix="docs-delta-baseline-") as temporary_dir:
        baseline_dir = Path(temporary_dir)
        try:
            _extract_git_tree(
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
    """Derive conventional GitHub Pages URLs from standard Actions variables."""

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


def _resolve_urls(
    args: argparse.Namespace, github_pull_request: GithubPullRequest | None
) -> tuple[str, str]:
    defaults = _github_url_defaults(os.environ, github_pull_request)
    base_url = args.base_url or defaults[0]
    pr_url = args.pr_url or defaults[1]
    if not base_url or not pr_url:
        raise DocsDeltaError(
            "documentation URLs are required; provide --base-url and --pr-url "
            "or run in GitHub Actions with GITHUB_REPOSITORY set"
        )
    return base_url, pr_url


def argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline-dir",
        type=Path,
        help="directory baseline; defaults to automatic gh-pages mode in PR Actions",
    )
    parser.add_argument(
        "--baseline-mode",
        choices=("directory", "gh-pages"),
        help="baseline source; inferred when omitted",
    )
    parser.add_argument(
        "--gh-pages-dir",
        type=Path,
        help="local full-history gh-pages checkout (defaults to .docs-baseline)",
    )
    parser.add_argument(
        "--current-dir",
        type=Path,
        help="current documentation directory (defaults to docs-artifact)",
    )
    parser.add_argument("--base-url")
    parser.add_argument("--pr-url")
    parser.add_argument(
        "--output",
        type=Path,
        help="report path (defaults to docs-artifact/docs-delta.md)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a non-zero status only for current-input errors."""

    args = argument_parser().parse_args(argv)
    try:
        github_pull_request = _github_pull_request(os.environ)
        current_dir = args.current_dir or _workspace_path(os.environ, "docs-artifact")
        output = args.output or current_dir / "docs-delta.md"

        with _resolved_baseline(args, github_pull_request, os.environ) as (
            baseline_dir,
            baseline_reason,
        ):
            if baseline_dir is None or not baseline_dir.is_dir():
                reason = baseline_reason or f"directory is missing: {baseline_dir}"
                _write_report(output, unavailable_report(reason))
                return 0
            try:
                baseline_needs = load_needs(baseline_dir)
            except DocsDeltaError as exc:
                _write_report(output, unavailable_report(str(exc)))
                return 0

            if not current_dir.is_dir():
                raise DocsDeltaError(
                    f"documentation directory is missing: {current_dir}"
                )
            current_needs = load_needs(current_dir)
            base_url, pr_url = _resolve_urls(args, github_pull_request)
            report = render_report(
                compare_needs(baseline_needs, current_needs),
                compare_html(baseline_dir, current_dir),
                base_url=base_url,
                pr_url=pr_url,
            )
            _write_report(output, report)
    except (DocsDeltaError, OSError) as exc:
        print(f"docs_delta: error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
