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
"""Tests for generated HTML normalization and page comparison."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools import docs_delta


def test_normalize_html_ignores_generated_metadata_but_keeps_content_changes() -> None:
    old = (
        '<html data-build-timestamp="2026-09-01T10:00:00Z">\r\n'
        '<meta name="generator" content="Sphinx 8">\r\n'
        "<!-- generated at 10:00 -->\r\n"
        '<div id="SNCB-0123abcd"><a href="https://github.com/example/repo/blob/0123456789abcdef0123456789abcdef01234567/src/example.py#L12">source</a></div>\r\n'
        "<p>Documentation</p>  \r\n</html>"
    )
    new = (
        '<html data-build-timestamp="2026-09-02T10:00:00Z">\n'
        '<meta name="generator" content="Sphinx 8">\n'
        "<!-- generated at 11:00 -->\n"
        '<div id="SNCB-fedcba98"><a href="https://github.com/example/repo/blob/fedcba9876543210fedcba9876543210fedcba98/src/example.py#L12">source</a></div>\n'
        "<p>Documentation</p>\n</html>"
    )

    assert docs_delta.normalize_html(old) == docs_delta.normalize_html(new)
    assert docs_delta.normalize_html(
        new.replace("src/example.py", "src/changed.py")
    ) != docs_delta.normalize_html(old)
    assert docs_delta.normalize_html(new).replace(
        "Documentation", "Changed"
    ) != docs_delta.normalize_html(old)


def test_normalize_html_preserves_user_metadata_and_ordinary_comments() -> None:
    content = '<meta name="description" content="Docs"><!-- page note -->'

    assert docs_delta.normalize_html(content) == content


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


def test_compare_html_rejects_a_missing_directory(tmp_path: Path) -> None:
    with pytest.raises(
        docs_delta.DocsDeltaError, match="documentation directory is missing"
    ):
        docs_delta.compare_html(tmp_path / "missing", tmp_path / "current")
