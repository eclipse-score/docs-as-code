# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""``score-report-bars``: the status and coverage charts of the verification reports.

Every ``score-report-bar`` counts its segments exactly like ``needpie`` counts
slices (one Sphinx-Needs filter per content line, or a ``:filter-func:``,
evaluated once all Needs are resolved). All bars of one ``score-report-bars``
block are drawn into a single compact figure of 100 % stacked horizontal bars on
a shared axis, so that e.g. status and test coverage of one safety class read
as one diagram. The reports explain the colours once per page, so the figure
has no legend. ``needpie`` itself stays untouched for every other chart.
"""

import hashlib
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from docutils import nodes
from docutils.parsers.rst import directives
from matplotlib import style
from matplotlib.colors import to_rgb
from matplotlib.figure import Figure
from sphinx.application import Sphinx
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective
from sphinx_needs.config import NeedsSphinxConfig
from sphinx_needs.data import SphinxNeedsData
from sphinx_needs.exceptions import NeedsInvalidFilter
from sphinx_needs.filter_common import filter_needs_parts
from sphinx_needs.utils import (
    check_and_get_external_filter_func,
    save_matplotlib_figure,
)
from sphinx_needs.views import NeedsAndPartsListView

from src.extensions.score_coverage import (
    note_coverage_dependency,
    read_coverage_summaries,
)

_FIGURE_WIDTH = 8.0
# Inches for the bar names on the left and the totals on the right.
_LABEL_INCHES, _TOTAL_INCHES = 1.6, 0.55
_ROW_INCHES, _TOP_INCHES, _AXIS_INCHES = 0.4, 0.05, 0.3
# Bar thickness as a share of its row; the rest is the gap between bars.
_BAR_HEIGHT = 0.72
_FONT_SIZE = 10
_MUTED = "#6c757d"
# Narrowest segment (inches) that gets "count (percent)", resp. a bare number.
_FULL_TEXT_INCHES, _MIN_TEXT_INCHES = 0.8, 0.25
_MIN_PERCENT_INCHES = 0.4


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BarRow:
    """One stacked bar; ``note`` replaces the bar, e.g. for an invalid filter."""

    label: str
    sizes: Sequence[float]
    colors: Sequence[str]
    names: Sequence[str]
    note: str = ""


class ReportBars(nodes.General, nodes.Element):
    """All ``ReportBar`` children are drawn as one figure."""


class ReportBar(nodes.General, nodes.Element):
    pass


class ReportBarsDirective(SphinxDirective):
    """Group the nested ``score-report-bar`` directives into one figure.

    The optional argument only names the figure in its alt text.
    """

    has_content = True
    optional_arguments = 1
    final_argument_whitespace = True

    def run(self) -> Sequence[nodes.Node]:
        node = ReportBars(title=self.arguments[0] if self.arguments else "")
        self.set_source_info(node)
        self.state.nested_parse(self.content, self.content_offset, node)
        return [node]


class ReportBarDirective(SphinxDirective):
    """Stacked bar with one segment per content line, each a Sphinx-Needs filter.

    Alternatively ``:filter-func:`` names a function that fills the segment
    sizes, called exactly like ``needpie`` calls it.
    """

    has_content = True
    required_arguments = 1
    final_argument_whitespace = True
    option_spec = {
        "labels": directives.unchanged_required,
        "colors": directives.unchanged_required,
        "filter-func": directives.unchanged_required,
    }

    def run(self) -> Sequence[nodes.Node]:
        content: list[str] = list(self.content)
        filters = [line for line in content if line.strip()]
        labels = _split(self.options.get("labels", ""))
        colors = _split(self.options.get("colors", ""))
        filter_func = str(self.options.get("filter-func", ""))
        if filter_func and filters:
            raise self.error("score-report-bar takes filter lines or :filter-func:")
        if len(labels) != len(colors) or (
            not filter_func and len(filters) != len(labels)
        ):
            raise self.error(
                "score-report-bar needs one label and one colour per segment"
            )
        node = ReportBar(
            label=self.arguments[0],
            filters=filters,
            filter_func=filter_func,
            labels=labels,
            colors=colors,
        )
        self.set_source_info(node)
        return [node]


def _split(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


@contextmanager
def _report_chart_style() -> Iterator[None]:
    """Keep report chart styling and dimensions independent of preceding needpie charts."""
    with style.context(["default", {"savefig.bbox": "standard"}]):
        yield


def _segment_text(size: float, share: float, *, show_counts: bool) -> str:
    """Return the text that fits into a segment of ``share`` percent."""
    width = share / 100 * (_FIGURE_WIDTH - _LABEL_INCHES - _TOTAL_INCHES)
    if not show_counts:
        return f"{share:.0f}%" if width >= _MIN_PERCENT_INCHES else ""
    if width >= _FULL_TEXT_INCHES:
        return f"{size:g} ({share:.0f}%)"
    return f"{size:g}" if width >= _MIN_TEXT_INCHES else ""


def _text_color(color: str) -> str:
    red, green, blue = to_rgb(color)
    return "black" if 0.299 * red + 0.587 * green + 0.114 * blue > 0.6 else "white"


def draw_report_bars(rows: Sequence[BarRow], *, show_counts: bool = True) -> Figure:
    """Draw one 100 % stacked bar per row, omitting counts for percentage rows."""
    height = _TOP_INCHES + len(rows) * _ROW_INCHES + _AXIS_INCHES
    figure = Figure(figsize=(_FIGURE_WIDTH, height))
    figure.subplots_adjust(
        left=_LABEL_INCHES / _FIGURE_WIDTH,
        right=1 - _TOTAL_INCHES / _FIGURE_WIDTH,
        top=1 - _TOP_INCHES / height,
        bottom=_AXIS_INCHES / height,
    )
    axes = figure.add_subplot()
    for y, row in enumerate(rows):
        total = sum(row.sizes)
        if row.note or not total:
            axes.text(
                1,
                y,
                row.note or "no Needs found",
                va="center",
                color=_MUTED,
                style="italic",
                fontsize=_FONT_SIZE,
            )
            continue
        left = 0.0
        for size, color in zip(row.sizes, row.colors, strict=True):
            share = size / total * 100
            axes.barh(
                y, share, left=left, height=_BAR_HEIGHT, color=color, edgecolor="white"
            )
            text = _segment_text(size, share, show_counts=show_counts)
            if text:
                axes.text(
                    left + share / 2,
                    y,
                    text,
                    ha="center",
                    va="center",
                    fontsize=_FONT_SIZE,
                    fontweight="bold",
                    color=_text_color(color),
                )
            left += share
        if show_counts:
            axes.text(
                101, y, f"{total:g}", va="center", color=_MUTED, fontsize=_FONT_SIZE
            )
    axes.set_xlim(0, 100)
    axes.set_ylim(len(rows) - 0.5, -0.5)
    axes.set_yticks(range(len(rows)), [row.label for row in rows])
    axes.set_xticks(range(0, 101, 25), [f"{tick}%" for tick in range(0, 101, 25)])
    axes.tick_params(length=0, labelsize=_FONT_SIZE)
    axes.tick_params(axis="x", labelsize=_FONT_SIZE - 2, labelcolor=_MUTED)
    axes.grid(axis="x", color="#e0e0e0")
    axes.set_axisbelow(True)
    for spine in axes.spines.values():
        spine.set_visible(False)
    return figure


def _describe(row: BarRow, unit: str = "") -> str:
    if row.note:
        return f"{row.label}: {row.note}"
    counts = ", ".join(
        f"{name} {size:g}{unit}"
        for name, size in zip(row.names, row.sizes, strict=True)
    )
    return f"{row.label}: {counts}"


def _call_filter_func(signature: str, need_list: NeedsAndPartsListView) -> list[float]:
    """Call a ``needpie``-style filter function and return its slice sizes."""
    result = check_and_get_external_filter_func(signature)
    assert result is not None
    args = result.args.split(",") if result.args else []
    sizes: list[float] = []
    result.func(
        needs=need_list,
        results=sizes,
        **{f"arg{index + 1}": arg for index, arg in enumerate(args)},
    )
    return sizes


def _bar_row(
    bar: nodes.Element,
    need_list: NeedsAndPartsListView,
    needs_config: NeedsSphinxConfig,
) -> BarRow:
    label: str = bar["label"]
    labels: list[str] = bar["labels"]
    colors: list[str] = bar["colors"]
    filter_func: str = bar["filter_func"]
    if not filter_func:
        sizes = [
            float(len(filter_needs_parts(need_list, needs_config, line, location=bar)))
            for line in bar["filters"]
        ]
        return BarRow(label, sizes, colors, labels)
    invalid = BarRow(label, [], colors, labels, note="invalid filter")
    try:
        sizes = _call_filter_func(filter_func, need_list)
    except NeedsInvalidFilter as error:
        logger.warning(
            "score-report-bar: %s", error, location=bar, type="score_report_bars"
        )
        return invalid
    if len(sizes) != len(labels):
        logger.warning(
            "score-report-bar: %s returned %d values for %d labels",
            filter_func,
            len(sizes),
            len(labels),
            location=bar,
            type="score_report_bars",
        )
        return invalid
    return BarRow(label, sizes, colors, labels)


def _chart_image(
    app: Sphinx,
    docname: str,
    title: str,
    rows: Sequence[BarRow],
    *,
    show_counts: bool = True,
    prefix: str = "score_report_bars",
) -> nodes.image:
    unit = "" if show_counts else "%"
    alt = "; ".join(_describe(row, unit) for row in rows)
    if title:
        alt = f"{title} — {alt}"
    # Sphinx caches images by filename even across forced writes of a cached
    # doctree, so the name follows the displayed content.
    digest = hashlib.sha256(
        f"{docname}|{alt}|{[row.colors for row in rows]}".encode()
    ).hexdigest()[:10]
    with _report_chart_style():
        image = save_matplotlib_figure(
            app,
            draw_report_bars(rows, show_counts=show_counts),
            f"{prefix}_{digest}",
            docname,
        )
    image["alt"] = alt
    image["classes"].append("score-report-bars")
    return image


def _process_report_bars(app: Sphinx, doctree: nodes.document, docname: str) -> None:
    bars: list[nodes.Element] = list(doctree.findall(ReportBar))
    charts: list[nodes.Element] = [
        *doctree.findall(ReportBars),
        *(bar for bar in bars if not isinstance(bar.parent, ReportBars)),
    ]
    if not charts:
        return
    needs_config = NeedsSphinxConfig(app.config)
    need_list = SphinxNeedsData(app.env).get_needs_view().to_list_with_parts()
    for chart in charts:
        chart_bars: list[nodes.Element] = list(chart.findall(ReportBar))
        rows = [_bar_row(bar, need_list, needs_config) for bar in chart_bars]
        title = " ".join(str(chart.get("title", "")).split())
        if not any(sum(row.sizes) for row in rows):
            details = "; ".join(_describe(row) for row in rows)
            if title:
                details = f"{title} — {details}"
            chart.replace_self(nodes.paragraph(text=f"{details} (no Needs found)"))
            continue
        chart.replace_self(_chart_image(app, docname, title, rows))


class CoverageReport(nodes.General, nodes.Element):
    """Placeholder resolved from the summary during HTML writing."""


class CoverageReportDirective(SphinxDirective):
    """Show aggregate coverage for the primary Need named by the argument."""

    required_arguments = 1
    option_spec = {"title": directives.unchanged_required}

    def run(self) -> Sequence[nodes.Node]:
        note_coverage_dependency(self.env.app)
        node = CoverageReport(
            need_id=self.arguments[0],
            title=self.options.get("title", self.arguments[0]),
        )
        self.set_source_info(node)
        return [node]


def _coverage_report(
    app: Sphinx, report: CoverageReport, summary: dict[str, Any] | None, docname: str
) -> nodes.container:
    block = nodes.container(classes=["score-coverage-report"])
    if summary is None:
        block += nodes.paragraph(text="No coverage data available for this component.")
        return block
    files = summary["files"]
    if not files["total"]:
        block += nodes.paragraph(text="No source files selected for this component.")
        return block
    block += nodes.paragraph(
        text=f"Coverage measurements available for {files['measured']}/{files['total']} "
        "selected source files. Green: covered; red: not covered. "
        "Percentages describe the available measurements."
    )
    rows: list[BarRow] = []
    for dimension, label in (("lines", "Line"), ("branches", "Branch")):
        metric = summary[dimension]
        percent = metric["percent"]
        if percent is None:
            block += nodes.paragraph(
                text=f"{label} coverage: "
                + ("no data." if metric["total"] is None else "not instrumented.")
            )
        else:
            rows.append(
                BarRow(
                    f"{label} Coverage",
                    [percent, 100 - percent],
                    ["#37a12d", "#ca2828"],
                    ["covered", "not covered"],
                )
            )
    if rows:
        block += _chart_image(
            app,
            docname,
            f"{report['title']} Coverage",
            rows,
            show_counts=False,
            prefix="score_coverage_bars",
        )
    return block


def _process_coverage_reports(
    app: Sphinx, doctree: nodes.document, docname: str
) -> None:
    reports = list(doctree.findall(CoverageReport))
    if not reports:
        return
    if app.builder.format != "html":
        for report in reports:
            report.replace_self([])
        return
    summaries = read_coverage_summaries(app)
    for report in reports:
        need_id = str(report["need_id"]).split("[", 1)[0]
        report.replace_self(
            _coverage_report(app, report, summaries.get(need_id), docname)
        )


def setup(app: Sphinx) -> None:
    app.add_node(ReportBars)
    app.add_node(ReportBar)
    app.add_node(CoverageReport)
    app.add_directive("score-coverage-report", CoverageReportDirective)
    app.connect("doctree-resolved", _process_coverage_reports, priority=600)
    app.add_directive("score-report-bars", ReportBarsDirective)
    app.add_directive("score-report-bar", ReportBarDirective)
    # After Sphinx-Needs (default priority) has resolved all Need nodes.
    app.connect("doctree-resolved", _process_report_bars, priority=600)
