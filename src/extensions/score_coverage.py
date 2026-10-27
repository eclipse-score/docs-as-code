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
"""Show compact coverage values in the existing Need metadata area."""

import json
from pathlib import Path
from typing import Any, cast

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.errors import SphinxError


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
    # Ordinary RST tables can reuse the CSS class; rendered Needs also have IDs.
    need_nodes = [
        table
        for table in doctree.findall(nodes.table)
        if "need" in table["classes"] and table["ids"]
    ]
    if not path or not need_nodes:
        return
    data = cast(dict[str, Any], json.loads(Path(path).read_text(encoding="utf-8")))
    if data.get("version") != 1:
        raise SphinxError("Coverage summaries must have version 1")
    summaries = {
        entry["primary_need_id"]: entry for entry in data["coverage_summaries"]
    }
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
    # The default handler (priority 500) creates the metadata area. Reuse its
    # nodes and CSS classes without introducing fields into the Need data model.
    app.connect("doctree-resolved", render_coverage, priority=600)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
