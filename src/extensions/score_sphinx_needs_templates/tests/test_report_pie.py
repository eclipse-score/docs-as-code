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
"""Tests for the ``score-report-bars`` charts of the verification reports."""

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest
from docutils import nodes
from matplotlib.figure import Figure
from score_pytest.attribute_plugin import add_test_properties
from score_sphinx_needs_templates import report_pie
from score_sphinx_needs_templates.report_pie import BarRow, draw_report_bars
from sphinx.application import Sphinx
from sphinx.testing.util import SphinxTestApp


def _texts(figure: Figure) -> list[tuple[str, str]]:
    return [
        (text.get_text(), str(text.get_color()))
        for text in figure.axes[0].texts
        if text.get_text()
    ]


@pytest.mark.parametrize(
    ("sizes", "expected"),
    [
        # 3 of 28 is 11%: room for the count, but not for the percentage.
        ([3, 25, 0], [("3", "white"), ("25 (89%)", "black"), ("28", "#6c757d")]),
        # 1 of 61 is 1.6%: too narrow for any number; 0 is never numbered.
        ([1, 60, 0], [("60 (98%)", "black"), ("61", "#6c757d")]),
    ],
)
def test_draw_report_bars_sizes_segment_numbers_by_width(
    sizes: list[int], expected: list[tuple[str, str]]
) -> None:
    """Numbers only where they fit; dark text on the light yellow segment."""
    figure = draw_report_bars(
        [BarRow("Status", sizes, ["#37a12d", "#f5c518", "#ca2828"], ["a", "b", "c"])]
    )
    axes = figure.axes[0]

    assert figure.get_size_inches()[0] == 4.8
    assert axes.get_legend() is None
    assert _texts(figure) == expected
    assert [label.get_text() for label in axes.get_yticklabels()] == ["Status"]


def test_draw_report_bars_puts_all_rows_on_one_shared_axis() -> None:
    """More bars make the figure taller, never narrower, so charts line up."""
    row = BarRow("Status", [1, 1], ["g", "r"], ["a", "b"])
    empty = BarRow("Test Coverage", [0, 0], ["g", "r"], ["a", "b"])
    invalid = BarRow("Reference Coverage", [], ["g", "r"], ["a", "b"], "invalid filter")

    two = draw_report_bars([row, empty])
    three = draw_report_bars([row, empty, invalid])

    assert len(three.axes) == 1
    assert two.get_size_inches()[0] == three.get_size_inches()[0]
    assert two.get_size_inches()[1] < three.get_size_inches()[1]
    assert [label.get_text() for label in three.axes[0].get_yticklabels()] == [
        "Status",
        "Test\nCoverage",
        "Reference\nCoverage",
    ]
    texts = [text for text, _ in _texts(three)]
    assert "no Needs found" in texts
    assert "invalid filter" in texts


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_report_bars_count_filters_and_leave_needpie_untouched(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Segments are counted per filter line; all bars of a block are one image."""
    monkeypatch.setenv("BUILD_WORKSPACE_DIRECTORY", str(tmp_path))
    (tmp_path / "conf.py").write_text(
        'extensions = ["sphinx_needs", "score_sphinx_needs_templates"]\n'
        'master_doc = "index"\n',
        encoding="utf-8",
    )
    (tmp_path / "index.rst").write_text(
        """
Report
======

.. req:: First open
   :id: REQ_001
   :status: open

.. req:: Second open
   :id: REQ_002
   :status: open

.. req:: Closed
   :id: REQ_003
   :status: closed

.. score-report-bars:: Comp Requirements (QM)

   .. score-report-bar:: Status
      :labels: open, closed
      :colors: #37a12d, #ca2828

      type == "req" and status == "open"
      type == "req" and status == "closed"

   .. score-report-bar:: Closed only
      :labels: closed
      :colors: #ca2828

      type == "req" and status == "closed"

.. needpie:: Plain chart
   :labels: open, closed

   type == "req" and status == "open"
   type == "req" and status == "closed"
""",
        encoding="utf-8",
    )

    app = SphinxTestApp(
        srcdir=tmp_path,
        outdir=tmp_path / "_build",
        buildername="html",
        freshenv=True,
    )
    try:
        app.build(force_all=True)
        html = (app.outdir / "index.html").read_text(encoding="utf-8")
        images = app.outdir / "_images"
        report_svgs = list(images.glob("score_report_bars_*.svg"))
        needpie_svgs = list(images.glob("need_pie_*.svg"))
        report_svg = report_svgs[0].read_text(encoding="utf-8")
        needpie_svg = needpie_svgs[0].read_text(encoding="utf-8")
    finally:
        app.cleanup()

    assert len(report_svgs) == len(needpie_svgs) == 1
    assert re.search(
        r'<img alt="Comp Requirements \(QM\) — Status: open 2, closed 1; '
        r'Closed only: closed 1" class="score-report-bars"',
        html,
    )
    assert 'width="345.6pt"' in report_svg
    # The generic needpie keeps Sphinx-Needs' own 8x4 inch layout.
    assert 'width="576pt" height="288pt"' in needpie_svg


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_report_bar_counts_through_filter_func(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``:filter-func:`` receives the Needs and its arguments like in ``needpie``."""
    monkeypatch.setenv("BUILD_WORKSPACE_DIRECTORY", str(tmp_path))
    monkeypatch.syspath_prepend(str(tmp_path))
    (tmp_path / "pie_counts.py").write_text(
        "def by_status(needs, results, arg1, arg2):\n"
        "    for status in (arg1, arg2):\n"
        '        results.append(sum(n["status"] == status for n in needs))\n',
        encoding="utf-8",
    )
    (tmp_path / "conf.py").write_text(
        'extensions = ["sphinx_needs", "score_sphinx_needs_templates"]\n'
        'master_doc = "index"\n',
        encoding="utf-8",
    )
    (tmp_path / "index.rst").write_text(
        """
Report
======

.. req:: Open
   :id: REQ_001
   :status: open

.. req:: Closed
   :id: REQ_002
   :status: closed

.. req:: Also closed
   :id: REQ_003
   :status: closed

.. score-report-bar:: Status
   :labels: open, closed
   :colors: #37a12d, #ca2828
   :filter-func: pie_counts.by_status(open,closed)
""",
        encoding="utf-8",
    )

    app = SphinxTestApp(
        srcdir=tmp_path,
        outdir=tmp_path / "_build",
        buildername="html",
        freshenv=True,
    )
    try:
        app.build(force_all=True)
        html = (app.outdir / "index.html").read_text(encoding="utf-8")
    finally:
        app.cleanup()

    # A bar outside of a ``score-report-bars`` block is a figure of its own.
    assert 'alt="Status: open 1, closed 2"' in html


@pytest.mark.parametrize("percent", [0, 1, 67, 99, 100])
def test_coverage_bar_labels_never_invent_hit_counts(percent: int) -> None:
    """Rounded percentages describe segment sizes, not exact source-item counts."""
    figure = draw_report_bars(
        [BarRow("Line", [percent, 100 - percent], ["g", "r"], ["a", "b"])],
        show_counts=False,
    )
    labels = [text for text, _ in _texts(figure)]
    # Segments too narrow for a number stay blank; there is no total either.
    assert labels == [f"{share}%" for share in (percent, 100 - percent) if share >= 12]


@pytest.fixture
def render_coverage_report(
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[[dict[str, Any] | None], nodes.container]:
    """Render Docutils nodes directly; image persistence does not need Sphinx here."""

    def save_figure(
        app: Sphinx, figure: Figure, basename: str, docname: str
    ) -> nodes.image:
        return nodes.image(uri=f"{basename}.svg")

    monkeypatch.setattr(report_pie, "save_matplotlib_figure", save_figure)

    def render(summary: dict[str, Any] | None) -> nodes.container:
        return vars(report_pie)["_coverage_report"](
            cast(Sphinx, None),
            report_pie.CoverageReport(title="Example component"),
            summary,
            "report",
        )

    return render


def _summary(
    *,
    total: int | None = 3,
    percent: int | None = 67,
    measured: int = 2,
    selected: int = 6,
) -> dict[str, Any]:
    return {
        "files": {"total": selected, "measured": measured},
        "lines": {"total": total, "percent": percent},
        "branches": {
            "total": 2 if measured else None,
            "percent": 100 if measured else None,
        },
    }


@pytest.mark.parametrize(
    ("summary", "expected", "alt"),
    [
        (None, "No coverage data available for this component.", None),
        (
            _summary(selected=0, measured=0),
            "No source files selected for this component.",
            None,
        ),
        (
            _summary(total=None, percent=None, measured=0),
            "Line coverage: no data.",
            None,
        ),
        (
            _summary(total=0, percent=None),
            "Line coverage: not instrumented.",
            "Branch Coverage: covered 100%, not covered 0%",
        ),
        (
            _summary(percent=0),
            "Coverage measurements available for 2/6 selected source files.",
            "Line Coverage: covered 0%, not covered 100%; "
            "Branch Coverage: covered 100%, not covered 0%",
        ),
    ],
)
def test_coverage_report_preserves_availability_and_independent_dimensions(
    render_coverage_report: Callable[[dict[str, Any] | None], nodes.container],
    summary: dict[str, Any] | None,
    expected: str,
    alt: str | None,
) -> None:
    """Unavailable lines must not hide valid branch coverage, or turn into a 0% bar."""
    report = render_coverage_report(summary)
    assert expected in report.astext()
    images: list[nodes.image] = list(report.findall(nodes.image))
    assert [image["alt"] for image in images] == (
        [] if alt is None else [f"Example component Coverage — {alt}"]
    )


def test_coverage_chart_urls_follow_displayed_values(
    render_coverage_report: Callable[[dict[str, Any] | None], nodes.container],
) -> None:
    """Sphinx and browsers cache images by URL, so changed segments need a new one."""
    before = list(render_coverage_report(_summary()).findall(nodes.image))
    equivalent = list(render_coverage_report(_summary()).findall(nodes.image))
    after = list(render_coverage_report(_summary(percent=33)).findall(nodes.image))
    assert before[0]["alt"].startswith(
        "Example component Coverage — Line Coverage: covered 67%, not covered 33%;"
    )
    assert after[0]["alt"].startswith(
        "Example component Coverage — Line Coverage: covered 33%, not covered 67%;"
    )
    assert before[0]["uri"] == equivalent[0]["uri"]
    assert before[0]["uri"] != after[0]["uri"]
