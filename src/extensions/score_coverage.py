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
"""Render prepared coverage summaries in Need metadata and verification reports."""

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.application import Sphinx
from sphinx.errors import SphinxError
from sphinx.util.docutils import SphinxDirective
from sphinx_needs.utils import save_matplotlib_figure

from src.extensions.score_sphinx_needs_templates.report_pie import (
    draw_report_pie,
    report_pie_style,
)


class CoverageReport(nodes.General, nodes.Element):
    """Placeholder resolved from the summary during HTML writing."""


class CoverageReportDirective(SphinxDirective):
    """Show aggregate coverage for the primary Need named by the argument."""

    required_arguments = 1
    option_spec = {"title": directives.unchanged_required}

    def run(self) -> Sequence[nodes.Node]:
        node = CoverageReport(
            need_id=self.arguments[0],
            title=self.options.get("title", self.arguments[0]),
            target_id=f"coverage-{self.env.docname}-{self.env.new_serialno('coverage')}",
        )
        self.set_source_info(node)
        return [node]


def _note_summary_dependency(app: Sphinx, doctree: nodes.document) -> None:
    # Metadata and report pages both depend on this external input. Recording
    # it while reading lets standalone incremental builds detect JSON changes.
    # Also track a configured path that is currently absent, so its appearance
    # is noticed on a subsequent build.
    if app.config.score_coverage_summary:
        app.env.note_dependency(app.config.score_coverage_summary)


def _coverage_report(
    app: Sphinx, report: CoverageReport, summary: dict[str, Any] | None, docname: str
) -> nodes.container:
    block = nodes.container(classes=["score-coverage-report"])
    if summary is None:
        block += nodes.paragraph(text="No coverage data available for this component.")
        return block
    files = summary["files"]
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
                text=f"{label} coverage: {_metric_text(metric['total'], percent)}."
            )
        else:
            digest = hashlib.sha256(
                f"{report['target_id']}-{dimension}".encode()
            ).hexdigest()[:10]
            with report_pie_style():
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


def _metric_text(total: int | None, percent: int | None) -> str:
    if total is None:
        return "no data"
    if percent is None:
        return "not instrumented"
    return f"{percent}%"


def _coverage_attribute(summary: dict[str, Any]) -> nodes.line:
    lines, branches, files = summary["lines"], summary["branches"], summary["files"]
    value = (
        f"lines {_metric_text(lines['total'], lines['percent'])} · "
        f"branches {_metric_text(branches['total'], branches['percent'])} · "
        f"files {files['measured']}/{files['total']}"
    )
    attribute = nodes.line(classes=["score-coverage"])
    attribute += nodes.inline(text="coverage: ", classes=["needs_label"])
    attribute += nodes.inline(text=value, classes=["needs_data"])
    return attribute


def _metadata_area(need: nodes.table) -> nodes.line_block | None:
    for block in need.findall(nodes.line_block):
        if not {"needs_meta", "needs_meta_left"}.intersection(block["classes"]):
            continue
        # A nested Need can have its own metadata. Only use the area belonging
        # to this table; a content-only layout should receive no extra output.
        parent = block.parent
        while parent is not None and not isinstance(parent, nodes.table):
            parent = parent.parent
        if parent is need:
            return block
    return None


def render_coverage(app: Sphinx, doctree: nodes.document, docname: str) -> None:
    """Add a display-only attribute after Sphinx-Needs has rendered its layouts."""
    path: str = app.config.score_coverage_summary
    reports = list(doctree.findall(CoverageReport))
    if app.builder.format != "html":
        for report in reports:
            report.replace_self([])
        return
    # Ordinary RST tables can reuse the CSS class; rendered Needs also have IDs.
    need_nodes = [
        table
        for table in doctree.findall(nodes.table)
        if "need" in table["classes"] and table["ids"]
    ]
    if not need_nodes and not reports:
        return
    data: dict[str, Any] = (
        cast(dict[str, Any], json.loads(Path(path).read_text(encoding="utf-8")))
        if path and Path(path).is_file()
        else {"version": 1, "coverage_summaries": []}
    )
    if data.get("version") != 1:
        raise SphinxError("Coverage summaries must have version 1")
    summaries = {
        entry["primary_need_id"]: entry for entry in data["coverage_summaries"]
    }
    for report in reports:
        need_id = str(report["need_id"]).split("[", 1)[0]
        report.replace_self(
            _coverage_report(app, report, summaries.get(need_id), docname)
        )
    for need in need_nodes:
        # Collection IDs can include a version qualifier; source ownership uses
        # the primary Need's unqualified ID, matching the bundle declaration.
        need_id = str(need["ids"][0]).split("[", 1)[0]
        summary = summaries.get(need_id)
        if summary is None or need.get("score_coverage_added"):
            continue
        metadata = _metadata_area(need)
        if metadata is not None:
            metadata += _coverage_attribute(summary)
            need["score_coverage_added"] = True


def setup(app: Sphinx) -> dict[str, object]:
    # The CLI prepares this input in the output directory before Sphinx starts.
    # Discovering it here keeps launchers compatible with projects that do not
    # enable coverage. Standalone Sphinx builds may configure a different path.
    summary = Path(app.outdir) / "coverage_summary.json"
    app.add_config_value(
        "score_coverage_summary",
        str(summary) if summary.is_file() else "",
        rebuild="env",
    )
    app.add_node(CoverageReport)
    app.add_directive("score-coverage-report", CoverageReportDirective)
    app.connect("doctree-read", _note_summary_dependency)
    # The default handler (priority 500) creates the metadata area. Reuse its
    # nodes and CSS classes without introducing fields into the Need data model.
    app.connect("doctree-resolved", render_coverage, priority=600)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
