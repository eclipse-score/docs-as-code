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
"""Tests for the ``score-report-pie`` directive of the verification reports."""

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest
from docutils import nodes
from matplotlib.figure import Figure
from score_pytest.attribute_plugin import add_test_properties
from score_sphinx_needs_templates import report_pie
from score_sphinx_needs_templates.report_pie import draw_report_pie
from sphinx.application import Sphinx
from sphinx.testing.util import SphinxTestApp


@pytest.mark.parametrize(
    ("sizes", "expected"),
    [
        # 1 of 31 is 3.2%: still numbered, at half size.
        ([1, 30, 0], [("3.2%\n(1)", 7), ("96.8%\n(30)", 14)]),
        # 1 of 61 is 1.6%: too small for any number; 0 is never numbered.
        ([1, 60, 0], [("98.4%\n(60)", 14)]),
    ],
)
def test_draw_report_pie_sizes_slice_numbers_by_share(
    sizes: list[int], expected: list[tuple[str, float]]
) -> None:
    figure = draw_report_pie("Comp Requirements\nStatus (QM)", sizes, ["g", "y", "r"])
    axes = figure.axes[0]

    visible = [t for t in axes.texts if t.get_visible() and t.get_text()]

    assert tuple(figure.get_size_inches()) == (5, 4)
    assert axes.get_legend() is None
    assert [(t.get_text(), t.get_fontsize()) for t in visible] == expected
    assert axes.get_title() == "Comp Requirements\nStatus (QM)"


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_report_pie_counts_filters_and_leaves_needpie_untouched(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Slices are counted per filter line; a plain needpie keeps its own layout."""
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

.. score-report-pie:: Comp Requirements
   Status (QM)
   :labels: open, closed
   :colors: #37a12d, #ca2828

   type == "req" and status == "open"
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
        report_svgs = list(images.glob("score_report_pie_*.svg"))
        needpie_svgs = list(images.glob("need_pie_*.svg"))
        report_svg = report_svgs[0].read_text(encoding="utf-8")
        needpie_svg = needpie_svgs[0].read_text(encoding="utf-8")
    finally:
        app.cleanup()

    assert len(report_svgs) == len(needpie_svgs) == 1
    assert re.search(
        r'<img alt="Comp Requirements Status \(QM\): open 2, closed 1" '
        r'class="score-report-pie"',
        html,
    )
    assert 'width="360pt"' in report_svg
    # The generic needpie keeps Sphinx-Needs' own 8x4 inch layout.
    assert 'width="576pt"' in needpie_svg


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_report_pie_counts_through_filter_func(
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

.. score-report-pie:: Comp Requirements
   Status (QM)
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

    assert 'alt="Comp Requirements Status (QM): open 1, closed 2"' in html


@pytest.mark.parametrize("percent", [0, 1, 67, 99, 100])
def test_coverage_pie_labels_never_invent_hit_counts(percent: int) -> None:
    """Rounded percentages describe slice sizes, not exact source-item counts."""
    figure = draw_report_pie(
        "Line coverage", [percent, 100 - percent], ["g", "r"], show_counts=False
    )
    labels = [text.get_text() for text in figure.axes[0].texts if text.get_text()]
    assert labels == [f"{percent}%", f"{100 - percent}%"]
    assert figure.axes[0].get_title() == "Line coverage"


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
    ("summary", "expected", "image_count"),
    [
        (None, "No coverage data available for this component.", 0),
        (
            _summary(selected=0, measured=0),
            "No source files selected for this component.",
            0,
        ),
        (_summary(total=None, percent=None, measured=0), "Line coverage: no data.", 0),
        (_summary(total=0, percent=None), "Line coverage: not instrumented.", 1),
        (
            _summary(percent=0),
            "Coverage measurements available for 2/6 selected source files.",
            2,
        ),
    ],
)
def test_coverage_report_preserves_availability_and_independent_dimensions(
    render_coverage_report: Callable[[dict[str, Any] | None], nodes.container],
    summary: dict[str, Any] | None,
    expected: str,
    image_count: int,
) -> None:
    """Unavailable lines must not hide valid branch coverage, or turn into a 0% pie."""
    report = render_coverage_report(summary)
    assert expected in report.astext()
    images = list(report.findall(nodes.image))
    assert len(images) == image_count
    if images:
        assert (
            images[-1]["alt"]
            == "Example component Branch Coverage: covered 100%, not covered 0%"
        )
    if image_count == 2:
        assert (
            images[0]["alt"]
            == "Example component Line Coverage: covered 0%, not covered 100%"
        )


def test_coverage_chart_urls_follow_displayed_values(
    render_coverage_report: Callable[[dict[str, Any] | None], nodes.container],
) -> None:
    """Sphinx and browsers cache images by URL, so changed slices need a new one."""
    before = list(render_coverage_report(_summary()).findall(nodes.image))
    equivalent = list(render_coverage_report(_summary()).findall(nodes.image))
    after = list(render_coverage_report(_summary(percent=33)).findall(nodes.image))
    assert (
        before[0]["alt"]
        == "Example component Line Coverage: covered 67%, not covered 33%"
    )
    assert (
        after[0]["alt"]
        == "Example component Line Coverage: covered 33%, not covered 67%"
    )
    assert before[0]["uri"] == equivalent[0]["uri"]
    assert before[0]["uri"] != after[0]["uri"]
    assert before[1]["uri"] == after[1]["uri"]
