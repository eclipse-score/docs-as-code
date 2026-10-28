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
"""Tests for Markdown report content, links, and file output."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools import docs_delta
from tools.docs_delta import report as report_module
from tools.tests.docs_delta_test_support import need


def test_modified_need_reports_all_changed_fields_and_one_sided_links() -> None:
    result = docs_delta.render_report(
        docs_delta.NeedComparison(
            added=(docs_delta.NeedChange("added", None, need("new/page", "Added")),),
            removed=(
                docs_delta.NeedChange("removed", need("old/page", "Removed"), None),
            ),
            modified=(
                docs_delta.NeedChange(
                    "changed",
                    need("old/page", "Old", tags=["old"], extra="before"),
                    need("new/page", "New", tags=["new"], extra="after"),
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
        need("page", "Old", details=large_old),
        need("page", "New", details=large_new),
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


def test_detail_threshold_is_independent_for_needs_and_pages() -> None:
    needs = docs_delta.NeedComparison(
        added=tuple(
            docs_delta.NeedChange(str(index), None, need("page", str(index)))
            for index in range(16)
        ),
        removed=(),
        modified=(),
        unchanged_count=0,
    )
    pages = docs_delta.PageComparison(
        added=tuple(docs_delta.PageChange(f"page-{index}.html") for index in range(16)),
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

    assert "16 entries changed; field details omitted." in report
    assert "<summary>Page changes (16)</summary>" in report
    assert "`page-0.html`" in report
    assert "- `0`" in report


def test_large_modified_need_section_keeps_ids_but_hides_field_values() -> None:
    changes = tuple(
        docs_delta.NeedChange(
            f"REQ-{index:02}",
            need("page", "Old title", details=f"old secret {index}"),
            need("page", "New title", details=f"new secret {index}"),
        )
        for index in range(16)
    )

    result = docs_delta.render_report(
        docs_delta.NeedComparison((), (), changes, 0),
        docs_delta.PageComparison((), (), (), 0),
        base_url="https://docs.example/main",
        pr_url="https://docs.example/pr/1",
    )

    assert "<summary>Need changes (16)</summary>" in result
    assert "16 entries changed; field details omitted." in result
    assert "`REQ-00`" in result and "`REQ-15`" in result
    assert "old secret" not in result
    assert "new secret" not in result


def test_need_links_encode_path_segments_and_anchors() -> None:
    url = docs_delta.need_link(
        "https://docs.example/main/",
        "REQ #1",
        {"docname": "nested/a guide"},
    )

    assert url == "https://docs.example/main/nested/a%20guide.html#REQ%20%231"


def test_report_write_failure_preserves_previous_output_and_cleans_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "delta.md"
    output.write_text("previous report", encoding="utf-8")

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr(report_module.os, "replace", fail_replace)

    with pytest.raises(OSError, match="simulated replace failure"):
        report_module.write_report(output, "new report")

    assert output.read_text(encoding="utf-8") == "previous report"
    assert list(tmp_path.glob(".delta.md.*.tmp")) == []
