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
"""``score-report-pie``: the pie chart of the verification reports.

It counts its slices exactly like ``needpie`` (one Sphinx-Needs filter per
content line, evaluated once all Needs are resolved), but draws a compact chart
built for three charts per row: no legend and no slice labels, since the
reports explain the colours once per page, and large numbers in the slices.
``needpie`` itself stays untouched for every other chart.
"""

import hashlib
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any

from docutils import nodes
from docutils.parsers.rst import directives
from matplotlib import style
from matplotlib.figure import Figure
from matplotlib.text import Text
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

_FIGURE_INCHES = (5.0, 4.0)
# Inches kept free above the circle for the two-line title and below it.
_TITLE_INCHES, _BOTTOM_INCHES = 0.75, 0.15
_VALUE_FONT_SIZE = 14
_TITLE_FONT_SIZE = 13
# Slices below this share get no number, as their text would overlap.
_MIN_LABELLED_SHARE = 0.02
# Slices below this share get their number at half size to fit.
_SMALL_SLICE_SHARE = 0.05


logger = logging.getLogger(__name__)


class ReportPie(nodes.General, nodes.Element):
    pass


class ReportPieDirective(SphinxDirective):
    """Pie chart with one slice per content line, each a Sphinx-Needs filter.

    Alternatively ``:filter-func:`` names a function that fills the slice sizes,
    called exactly like ``needpie`` calls it.
    """

    has_content = True
    optional_arguments = 1
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
            raise self.error("score-report-pie takes filter lines or :filter-func:")
        if len(labels) != len(colors) or (
            not filter_func and len(filters) != len(labels)
        ):
            raise self.error(
                "score-report-pie needs one label and one colour per slice"
            )
        node = ReportPie(
            title=self.arguments[0] if self.arguments else "",
            filters=filters,
            filter_func=filter_func,
            labels=labels,
            colors=colors,
            target_id=f"score-report-pie-{self.env.docname}-"
            f"{self.env.new_serialno('score-report-pie')}",
        )
        self.set_source_info(node)
        return [node]


def _split(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


@contextmanager
def _report_pie_style() -> Iterator[None]:
    """Keep report chart styling and dimensions independent of preceding needpie charts."""
    with style.context(["default", {"savefig.bbox": "standard"}]):
        yield


def draw_report_pie(
    title: str, sizes: Sequence[float], colors: list[str], *, show_counts: bool = True
) -> Figure:
    """Draw nonzero slices, omitting counts when sizes are rounded percentages."""
    total = sum(sizes)
    height = _FIGURE_INCHES[1]
    figure = Figure(figsize=_FIGURE_INCHES)
    figure.subplots_adjust(
        left=0.02,
        right=0.98,
        top=1 - _TITLE_INCHES / height,
        bottom=_BOTTOM_INCHES / height,
    )
    axes = figure.add_subplot(aspect="equal")
    pie: Any = axes.pie(
        sizes,
        colors=colors,
        startangle=90,
        autopct=lambda pct: (
            f"{pct:.1f}%\n({round(pct * total / 100)})"
            if show_counts
            else f"{pct:.0f}%"
        ),
        textprops={"fontsize": _VALUE_FONT_SIZE, "fontweight": "bold"},
    )
    values: list[Text] = pie[2]
    for size, value in zip(sizes, values, strict=True):
        value.set_visible(size >= total * _MIN_LABELLED_SHARE)
        if size < total * _SMALL_SLICE_SHARE:
            value.set_fontsize(_VALUE_FONT_SIZE / 2)
    axes.set(xlim=(-1.05, 1.05), ylim=(-1.05, 1.05))
    axes.set_title(title, fontsize=_TITLE_FONT_SIZE, wrap=True)
    return figure


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


def _process_report_pies(app: Sphinx, doctree: nodes.document, docname: str) -> None:
    pies: list[nodes.Element] = list(doctree.findall(ReportPie))
    if not pies:
        return
    needs_config = NeedsSphinxConfig(app.config)
    need_list = SphinxNeedsData(app.env).get_needs_view().to_list_with_parts()
    for pie in pies:
        title: str = pie["title"]
        filters: list[str] = pie["filters"]
        labels: list[str] = pie["labels"]
        target_id: str = pie["target_id"]
        filter_func: str = pie["filter_func"]
        sizes: list[float]
        if filter_func:
            try:
                sizes = _call_filter_func(filter_func, need_list)
            except NeedsInvalidFilter as error:
                logger.warning(
                    "score-report-pie: %s", error, location=pie, type="score_report_pie"
                )
                pie.replace_self(nodes.paragraph(text=f"{title}: invalid filter"))
                continue
            if len(sizes) != len(labels):
                logger.warning(
                    "score-report-pie: %s returned %d values for %d labels",
                    filter_func,
                    len(sizes),
                    len(labels),
                    location=pie,
                    type="score_report_pie",
                )
                pie.replace_self(nodes.paragraph(text=f"{title}: invalid filter"))
                continue
        else:
            sizes = [
                float(
                    len(filter_needs_parts(need_list, needs_config, line, location=pie))
                )
                for line in filters
            ]
        counts = ", ".join(
            f"{label} {size:g}" for label, size in zip(labels, sizes, strict=True)
        )
        alt = f"{' '.join(title.split())}: {counts}"
        if not any(sizes):
            pie.replace_self(nodes.paragraph(text=f"{alt} (no Needs found)"))
            continue
        digest = hashlib.sha256(target_id.encode()).hexdigest()[:10]
        with _report_pie_style():
            image = save_matplotlib_figure(
                app,
                draw_report_pie(title, sizes, pie["colors"]),
                f"score_report_pie_{digest}",
                docname,
            )
        image["alt"] = alt
        image["classes"].append("score-report-pie")
        pie.replace_self(image)


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
    row = nodes.container(
        classes=[
            "sd-row",
            "sd-row-cols-1",
            "sd-row-cols-md-2",
            "sd-g-3",
            "score-pie-row",
        ]
    )
    for dimension, label in (("lines", "Line"), ("branches", "Branch")):
        metric = summary[dimension]
        column = nodes.container(classes=["sd-col"])
        percent = metric["percent"]
        title = f"{report['title']} {label} Coverage"
        if percent is None:
            column += nodes.paragraph(
                text=f"{label} coverage: "
                + ("no data." if metric["total"] is None else "not instrumented.")
            )
        else:
            # Sphinx caches images by filename even across forced writes of a
            # cached doctree. Include the displayed content so changed coverage
            # produces a fresh image and a fresh browser URL.
            digest = hashlib.sha256(
                f"{docname}-{title}-{percent}".encode()
            ).hexdigest()[:10]
            with _report_pie_style():
                image = save_matplotlib_figure(
                    app,
                    draw_report_pie(
                        title,
                        [percent, 100 - percent],
                        ["#37a12d", "#ca2828"],
                        show_counts=False,
                    ),
                    f"score_coverage_pie_{digest}",
                    docname,
                )
            image["alt"] = f"{title}: covered {percent}%, not covered {100 - percent}%"
            image["classes"].append("score-report-pie")
            column += image
        row += column
    block += row
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
    app.add_node(ReportPie)
    app.add_node(CoverageReport)
    app.add_directive("score-coverage-report", CoverageReportDirective)
    app.connect("doctree-resolved", _process_coverage_reports, priority=600)
    app.add_directive("score-report-pie", ReportPieDirective)
    # After Sphinx-Needs (default priority) has resolved all Need nodes.
    app.connect("doctree-resolved", _process_report_pies, priority=600)
