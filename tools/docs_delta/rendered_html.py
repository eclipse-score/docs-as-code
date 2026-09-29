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
"""Normalization and comparison of rendered HTML pages."""

from __future__ import annotations

import re
from pathlib import Path

from .comparison import DocsDeltaError, PageChange, PageComparison

_META_TAG = re.compile(r"<meta\b[^>]*>", re.IGNORECASE)
_META_ATTRIBUTE = re.compile(
    r"(?:name|property|itemprop)\s*=\s*([\"'])(.*?)\1", re.IGNORECASE
)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.IGNORECASE | re.DOTALL)
_VOLATILE_ATTRIBUTE = re.compile(
    r"\s+data-(?:build|generated|timestamp|last-modified)(?:-[\w-]+)?\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)",
    re.IGNORECASE,
)
# PR documentation builds run on GitHub's synthetic merge commit, while the
# published baseline was built from the base commit. Keep source paths and line
# numbers comparable, but ignore the revision segment in generated blob links.
_GITHUB_BLOB_COMMIT = re.compile(r"(?<=/blob/)[0-9a-f]{40}(?=/)", re.IGNORECASE)
# Sphinx-Needs derives these wrapper IDs from rendered content, including the
# source-link revision above. Need IDs and visible content remain compared.
_NEED_CONTAINER_ID = re.compile(r"\bSNCB-[0-9a-f]{8}\b", re.IGNORECASE)
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


def _html_metadata_name(tag: str) -> str | None:
    for match in _META_ATTRIBUTE.finditer(tag):
        name = match.group(2).lower()
        if name in _VOLATILE_META_NAMES:
            return name
    return None


def normalize_html(content: str) -> str:
    """Remove known build-to-build noise while preserving page changes.

    The rules are intentionally narrow. Build dates, generated attributes,
    GitHub source revision hashes, and Sphinx-Needs wrapper IDs vary between
    otherwise identical builds. Visible text, links, element structure, and
    other attributes remain significant so a real rendered change is reported.
    Keep each rule tied to a known source of nondeterminism; broad HTML cleanup
    could hide a user-facing regression.
    """

    # Normalize line endings first so the later line cleanup behaves the same
    # for artifacts produced on different operating systems.
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")

    def remove_meta(match: re.Match[str]) -> str:
        return "" if _html_metadata_name(match.group(0)) else match.group(0)

    # Only discard metadata tags whose name is on the explicit volatile list;
    # unrelated meta tags can affect consumers and remain part of the diff.
    normalized = _META_TAG.sub(remove_meta, normalized)

    def remove_comment(match: re.Match[str]) -> str:
        return "" if _VOLATILE_COMMENT_WORDS.search(match.group(0)) else match.group(0)

    # Generated comments are noisy, but ordinary HTML comments can document
    # page structure and therefore stay comparison-visible.
    normalized = _HTML_COMMENT.sub(remove_comment, normalized)
    normalized = _VOLATILE_ATTRIBUTE.sub("", normalized)
    normalized = _GITHUB_BLOB_COMMIT.sub("<source-commit>", normalized)
    normalized = _NEED_CONTAINER_ID.sub("SNCB-<generated>", normalized)
    # Trailing whitespace and blank padding do not change rendered pages.
    normalized = "\n".join(line.rstrip() for line in normalized.splitlines())
    return normalized.strip()


def _html_files(directory: Path) -> dict[str, str]:
    """Read and normalize every HTML page below ``directory``.

    POSIX separators make paths stable across operating systems and suitable
    for URLs in the report. Sorting traversal also avoids filesystem-order
    leaking into the report's comparison order.
    """

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
    """Compare pages by relative path and normalized rendered content."""

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
