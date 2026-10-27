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
"""Exercise coverage pies through the existing docs() reference integration."""

from collections.abc import Iterator
from html.parser import HTMLParser
from pathlib import Path

import pytest

from src.tests.docs_bzl.helpers import repo_root, run_scenario, staged_coverage_report


class _CoverageCharts(HTMLParser):
    """Read only coverage chart images from the rendered verification report."""

    def __init__(self, html: str, output: Path):
        super().__init__()
        self.charts: dict[str, Path] = {}
        self.output = output
        self.html = html
        self.feed(html)
        # Later builds replace the output directory; preserve each result now.
        self.svg_bytes = {
            title: path.read_bytes() for title, path in self.charts.items()
        }

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        source, title = attributes.get("src"), attributes.get("alt")
        if tag == "img" and source and title and "score_coverage_pie_" in source:
            assert title not in self.charts, f"Coverage chart rendered twice: {title}"
            self.charts[title] = self.output / source


@pytest.fixture(scope="module")
def report_builds() -> Iterator[dict[str, _CoverageCharts]]:
    """Build each coverage state once and share snapshots between the assertions."""
    fixture = (
        repo_root()
        / "src/tests/docs_bzl/scenarios/reference_integration/modern_module/coverage.info"
    )
    with staged_coverage_report(fixture) as report:
        original = report.read_bytes()
        baseline = _build_report()
        report.write_bytes(original.replace(b"DA:1,2", b"DA:1,900", 1))
        equivalent = _build_report()
        report.write_bytes(original.replace(b"DA:1,2", b"DA:1,0", 1))
        changed = _build_report()
        report.unlink()
        missing = _build_report()
        yield {
            "baseline": baseline,
            "equivalent": equivalent,
            "changed": changed,
            "missing": missing,
        }


def _build_report() -> _CoverageCharts:
    result = run_scenario("run", "reference_integration/modern_module", ":docs")
    return _CoverageCharts(
        (result.build_dir / "index.html").read_text(), result.build_dir
    )


_LINE_67 = "Modern linked component Line Coverage: covered 67%, not covered 33%"
_LINE_33 = "Modern linked component Line Coverage: covered 33%, not covered 67%"
_BRANCH = "Modern linked component Branch Coverage: covered 100%, not covered 0%"


@pytest.mark.bazel_slow
def test_module_report_renders_line_and_branch_coverage_pies(
    report_builds: dict[str, _CoverageCharts],
):
    """The real post-template uses the component's summary and reports partial measurements."""
    report = report_builds["baseline"]
    assert "2/6 selected source files" in report.html
    assert set(report.charts) == {_LINE_67, _BRANCH}
    line_svg = report.svg_bytes[_LINE_67]
    assert b"<!-- 67% -->" in line_svg
    assert b"<!-- 33% -->" in line_svg
    assert b"<!-- 100% -->" in report.svg_bytes[_BRANCH]


@pytest.mark.bazel_slow
def test_module_report_reuses_pies_for_equivalent_coverage(
    report_builds: dict[str, _CoverageCharts],
):
    """Different execution counters must preserve both chart URLs and SVG bytes."""
    before, after = report_builds["baseline"], report_builds["equivalent"]
    assert set(after.charts) == {_LINE_67, _BRANCH}
    assert after.charts == before.charts
    assert after.svg_bytes == before.svg_bytes


@pytest.mark.bazel_slow
def test_module_report_refreshes_line_pie_when_coverage_changes(
    report_builds: dict[str, _CoverageCharts],
):
    """A changed line result gets a fresh chart URL while unchanged branches keep theirs."""
    before, after = report_builds["baseline"], report_builds["changed"]
    assert set(after.charts) == {_LINE_33, _BRANCH}
    assert after.charts[_LINE_33] != before.charts[_LINE_67]
    assert b"<!-- 33% -->" in after.svg_bytes[_LINE_33]
    assert after.charts[_BRANCH] == before.charts[_BRANCH]


@pytest.mark.bazel_slow
def test_module_report_shows_missing_measurements_without_pies(
    report_builds: dict[str, _CoverageCharts],
):
    """An absent coverage artifact means unknown coverage, rather than 0% covered."""
    report = report_builds["missing"]
    assert "0/6 selected source files" in report.html
    assert "Line coverage: no data." in report.html
    assert "Branch coverage: no data." in report.html
    assert not report.charts


@pytest.mark.bazel_slow
def test_module_report_removes_pies_when_coverage_disappears(
    report_builds: dict[str, _CoverageCharts],
):
    """Rebuilding after artifact removal must remove previously rendered coverage pies."""
    before, after = report_builds["changed"], report_builds["missing"]
    assert set(before.charts) == {_LINE_33, _BRANCH}
    assert "0/6 selected source files" in after.html
    assert "Line coverage: no data." in after.html
    assert "Branch coverage: no data." in after.html
    assert not after.charts
