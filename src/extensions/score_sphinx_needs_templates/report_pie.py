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
from sphinx.util.docutils import SphinxDirective
from sphinx_needs.config import NeedsSphinxConfig
from sphinx_needs.data import SphinxNeedsData
from sphinx_needs.filter_common import filter_needs_parts
from sphinx_needs.utils import save_matplotlib_figure

_FIGURE_INCHES = (5.0, 4.0)
# Inches kept free above the circle for the two-line title and below it.
_TITLE_INCHES, _BOTTOM_INCHES = 0.75, 0.15
_VALUE_FONT_SIZE = 14
_TITLE_FONT_SIZE = 13
# Slices below this share get no number, as their text would overlap.
_MIN_LABELLED_SHARE = 0.05


class ReportPie(nodes.General, nodes.Element):
    pass


class ReportPieDirective(SphinxDirective):
    """Pie chart with one slice per content line, each a Sphinx-Needs filter."""

    has_content = True
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {
        "labels": directives.unchanged_required,
        "colors": directives.unchanged_required,
    }

    def run(self) -> Sequence[nodes.Node]:
        content: list[str] = list(self.content)
        filters = [line for line in content if line.strip()]
        labels = _split(self.options.get("labels", ""))
        colors = _split(self.options.get("colors", ""))
        if not (len(filters) == len(labels) == len(colors)):
            raise self.error(
                "score-report-pie needs one label and one colour per filter line"
            )
        node = ReportPie(
            title=self.arguments[0] if self.arguments else "",
            filters=filters,
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
    """Pin the matplotlib settings, which other charts may have changed globally."""
    with style.context(["default", {"savefig.bbox": "standard"}]):
        yield


def draw_report_pie(title: str, sizes: list[int], colors: list[str]) -> Figure:
    """Draw the chart; ``sizes`` must contain at least one non-zero value."""
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
        autopct=lambda pct: f"{pct:.1f}%\n({round(pct * total / 100)})",
        textprops={"fontsize": _VALUE_FONT_SIZE, "fontweight": "bold"},
    )
    values: list[Text] = pie[2]
    for size, value in zip(sizes, values, strict=True):
        value.set_visible(size >= total * _MIN_LABELLED_SHARE)
    axes.set(xlim=(-1.05, 1.05), ylim=(-1.05, 1.05))
    axes.set_title(title, fontsize=_TITLE_FONT_SIZE, wrap=True)
    return figure


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
        sizes = [
            len(filter_needs_parts(need_list, needs_config, line, location=pie))
            for line in filters
        ]
        counts = ", ".join(
            f"{label} {size}" for label, size in zip(labels, sizes, strict=True)
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


def setup(app: Sphinx) -> None:
    app.add_node(ReportPie)
    app.add_directive("score-report-pie", ReportPieDirective)
    # After Sphinx-Needs (default priority) has resolved all Need nodes.
    app.connect("doctree-resolved", _process_report_pies, priority=600)
