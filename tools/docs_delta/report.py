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
"""Markdown formatting for documentation delta reports."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol
from urllib.parse import quote

from .comparison import MISSING, NeedChange, NeedComparison
from .rendered_html import PageChange, PageComparison

DETAIL_LIMIT = 15
MAX_RENDERED_VALUE_LENGTH = 600


class NeedFormatter(Protocol):
    """Format a Need change for a Markdown report section."""

    def __call__(
        self,
        change: NeedChange,
        *,
        base_url: str,
        pr_url: str,
        include_diff: bool = False,
    ) -> list[str]: ...


class PageFormatter(Protocol):
    """Format a rendered page change for a Markdown report section."""

    def __call__(
        self,
        change: PageChange,
        *,
        base_url: str,
        pr_url: str,
        kind: str,
    ) -> str: ...


def _url_with_path(base_url: str, relative_path: str, anchor: str | None = None) -> str:
    """Append an encoded documentation path and optional fragment to a URL.

    Encode path segments independently: slashes in a page path remain
    separators, while characters inside each segment cannot alter the URL
    structure.
    """
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
    """Build the page URL for a Need, returning ``None`` if it has no docname."""
    docname = need.get("docname")
    if not isinstance(docname, str) or not docname.strip():
        return None
    rendered_name = docname.strip("/")
    if not rendered_name.endswith(".html"):
        rendered_name += ".html"
    return _url_with_path(base_url, rendered_name)


def need_link(base_url: str, need_id: str, need: Mapping[str, object]) -> str | None:
    """Link directly to a Need anchor when its exported page is known."""
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
    """Render one JSON field value compactly and safely for Markdown inline code."""
    if value is MISSING:
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
    """Render one Need row, with old/new links and optional field details."""
    need = change.current or change.baseline
    assert need is not None
    links = []
    old_link = (
        need_link(base_url, change.need_id, change.baseline)
        if change.baseline
        else None
    )
    new_link = (
        need_link(pr_url, change.need_id, change.current) if change.current else None
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
                f"  - `{field}`: {_format_value(change.baseline.get(field, MISSING))} "
                f"→ {_format_value(change.current.get(field, MISSING))}"
            )
    return result


def _format_page_entry(
    change: PageChange, *, base_url: str, pr_url: str, kind: str
) -> str:
    """Render a page row with links appropriate to its change category."""
    old = _url_with_path(base_url, change.path) if kind != "added" else None
    new = _url_with_path(pr_url, change.path) if kind != "removed" else None
    links = []
    if old:
        links.append(_markdown_link("old", old))
    if new:
        links.append(_markdown_link("new", new))
    return f"- `{change.path}` ({' / '.join(links)})"


def _need_section(
    lines: list[str],
    title: str,
    entries: Sequence[NeedChange],
    formatter: NeedFormatter,
    *,
    base_url: str,
    pr_url: str,
    kind: str = "",
) -> None:
    """Append a Need section, suppressing field-by-field detail for large groups.

    The entries themselves are retained so reviewers can still see which Needs
    changed. Modified-field values are the part that can make a large comment
    unwieldy, so those are omitted once the group exceeds ``DETAIL_LIMIT``.
    """
    if not entries:
        return
    lines.extend([f"### {title} ({len(entries)})", ""])
    include_field_diff = kind == "modified" and len(entries) <= DETAIL_LIMIT
    if len(entries) > DETAIL_LIMIT:
        lines.extend([f"{len(entries)} entries changed; field details omitted.", ""])
    for entry in entries:
        lines.extend(
            formatter(
                entry,
                base_url=base_url,
                pr_url=pr_url,
                include_diff=include_field_diff,
            )
        )
    lines.append("")


def _page_section(
    lines: list[str],
    title: str,
    entries: Sequence[PageChange],
    formatter: PageFormatter,
    *,
    base_url: str,
    pr_url: str,
    kind: str,
) -> None:
    """Append a page section; every entry remains directly reviewable."""
    if not entries:
        return
    lines.extend([f"### {title} ({len(entries)})", ""])
    for entry in entries:
        lines.append(formatter(entry, base_url=base_url, pr_url=pr_url, kind=kind))
    lines.append("")


def render_report(
    needs: NeedComparison,
    pages: PageComparison,
    *,
    base_url: str,
    pr_url: str,
) -> str:
    """Render a deterministic, link-rich Markdown summary of both comparisons.

    Small change sets are expanded for immediate review. Larger sets are
    wrapped in GitHub's collapsible-details markup so the comment stays
    scannable while preserving every changed path or Need in the report.
    """

    lines = [
        "# Documentation delta",
        "",
        "Documentation preview for this pull request: "
        f"{_markdown_link('open preview', pr_url)} · "
        f"Baseline: {_markdown_link('open baseline', base_url)}",
        "",
        "## Summary",
        "",
        f"- Needs: {len(needs.added)} added, {len(needs.removed)} removed, "
        f"{len(needs.modified)} modified, {needs.unchanged_count} unchanged",
        f"- Rendered pages: {len(pages.added)} added, {len(pages.removed)} removed, "
        f"{len(pages.modified)} modified, {pages.unchanged_count} unchanged",
    ]

    need_change_count = len(needs.added) + len(needs.removed) + len(needs.modified)
    if need_change_count:
        need_lines: list[str] = []
        _need_section(
            need_lines,
            "Added",
            needs.added,
            _format_need_entry,
            base_url=base_url,
            pr_url=pr_url,
            kind="added",
        )
        _need_section(
            need_lines,
            "Removed",
            needs.removed,
            _format_need_entry,
            base_url=base_url,
            pr_url=pr_url,
            kind="removed",
        )
        _need_section(
            need_lines,
            "Modified",
            needs.modified,
            _format_need_entry,
            base_url=base_url,
            pr_url=pr_url,
            kind="modified",
        )
        if need_change_count > DETAIL_LIMIT:
            lines.extend(
                [
                    "",
                    "<details>",
                    f"<summary>Need changes ({need_change_count})</summary>",
                    "",
                    *need_lines,
                    "</details>",
                ]
            )
        else:
            lines.extend(["", "## Need changes", "", *need_lines])

    page_change_count = len(pages.added) + len(pages.removed) + len(pages.modified)
    if page_change_count:
        page_lines: list[str] = []
        _page_section(
            page_lines,
            "Added",
            pages.added,
            _format_page_entry,
            base_url=base_url,
            pr_url=pr_url,
            kind="added",
        )
        _page_section(
            page_lines,
            "Removed",
            pages.removed,
            _format_page_entry,
            base_url=base_url,
            pr_url=pr_url,
            kind="removed",
        )
        _page_section(
            page_lines,
            "Modified",
            pages.modified,
            _format_page_entry,
            base_url=base_url,
            pr_url=pr_url,
            kind="modified",
        )
        if page_change_count > DETAIL_LIMIT:
            # Keep the complete page list available, but collapsed by default
            # so a broad Sphinx rebuild does not bury the useful summary.
            lines.extend(
                [
                    "",
                    "<details>",
                    f"<summary>Page changes ({page_change_count})</summary>",
                    "",
                    *page_lines,
                    "</details>",
                ]
            )
        else:
            lines.extend(["", "## Page changes", "", *page_lines])
    return "\n".join(lines).rstrip() + "\n"


def unavailable_report(reason: str) -> str:
    """Render the successful, explicit report used when baseline is unavailable."""

    return (
        "# Documentation delta\n\n"
        "## Delta unavailable\n\n"
        f"The documentation baseline is unavailable: {reason}\n"
    )


def write_report(path: Path, content: str) -> None:
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
