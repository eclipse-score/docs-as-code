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
"""Render coverage inside matching Needs using the normal Sphinx layout."""

import json
import os
import re
import time
from html import unescape
from pathlib import Path

import pytest
from sphinx.testing.util import SphinxTestApp


@pytest.mark.parametrize(
    ("total", "percent", "measured", "expected"),
    [
        (3, 67, 2, "lines 67%"),
        (1, 0, 2, "lines 0%"),
        (0, None, 2, "lines not instrumented"),
        (None, None, 0, "lines no data"),
    ],
)
@pytest.mark.parametrize("configure_summary", [False, True])
def test_summary_is_rendered_only_inside_the_matching_need(
    tmp_path: Path,
    total: int | None,
    percent: int | None,
    measured: int,
    expected: str,
    configure_summary: bool,
) -> None:
    """Discovered and configured summaries preserve Need selection and metric states."""
    # SphinxTestApp places HTML below <builddir>/html.
    output = tmp_path / "_build/html"
    output.mkdir(parents=True)
    summary = (
        tmp_path / "coverage.json"
        if configure_summary
        else output / "coverage_summary.json"
    )
    summary.write_text(
        json.dumps(
            {
                "version": 1,
                "coverage_summaries": [
                    {
                        "primary_need_id": "REQ_1",
                        "files": {"total": 6, "measured": measured},
                        "lines": {"total": total, "percent": percent},
                        "branches": {"total": 0 if measured else None, "percent": None},
                    }
                ],
            }
        )
    )
    if configure_summary:
        # An explicit path must take precedence over automatic discovery.
        (output / "coverage_summary.json").write_text("not the configured input")
    summary_config = (
        f"score_coverage_summary = {str(summary)!r}\n" if configure_summary else ""
    )
    (tmp_path / "conf.py").write_text(
        'extensions = ["sphinx_needs", "score_coverage"]\n'
        'master_doc = "index"\n' + summary_config
    )
    (tmp_path / "index.rst").write_text(
        "Example\n=======\n\n.. req:: Selected\n   :id: REQ_1\n\n   Original content.\n\n"
        ".. req:: Unselected\n   :id: REQ_2\n\n"
        ".. list-table::\n   :class: need\n\n   * - Ordinary table\n"
    )
    app = SphinxTestApp(
        srcdir=tmp_path, builddir=tmp_path / "_build", buildername="html", freshenv=True
    )
    try:
        for _ in range(2):
            # Repeated write events must keep one coverage attribute per matching Need.
            app.build(force_all=True)
            html = (app.outdir / "index.html").read_text()
            selected, unselected = html.split('id="REQ_1"', 1)[1].split('id="REQ_2"', 1)
            metadata, content = re.split(
                r'<tr class="[^"]*\bcontent\b[^"]*">', selected, maxsplit=1
            )
            assert metadata.count("score-coverage") == 1
            assert "score-coverage" not in content
            assert "Original content." in content
            assert "score-coverage" not in unselected
            text = " ".join(unescape(re.sub(r"<[^>]+>", " ", selected)).split())
            assert expected in text
            assert f"files {measured}/6" in text
        assert not app.warning.getvalue()
    finally:
        app.cleanup()


def test_unconfigured_coverage_leaves_needs_unchanged(tmp_path: Path) -> None:
    """Needs exports and documentation checks work without a summary input."""
    (tmp_path / "conf.py").write_text(
        'extensions = ["sphinx_needs", "score_coverage"]\nmaster_doc = "index"\n'
    )
    (tmp_path / "index.rst").write_text(
        "Example\n=======\n\n.. req:: Selected\n   :id: REQ_1\n"
    )
    app = SphinxTestApp(
        srcdir=tmp_path, builddir=tmp_path / "_build", buildername="html", freshenv=True
    )
    try:
        app.build(force_all=True)
        assert "score-coverage" not in (app.outdir / "index.html").read_text()
        assert not app.warning.getvalue()
    finally:
        app.cleanup()


def test_content_only_layout_keeps_coverage_out_of_the_content(tmp_path: Path) -> None:
    """A layout without metadata must not receive an attribute in its prose."""
    summary = tmp_path / "coverage.json"
    summary.write_text(
        json.dumps(
            {
                "version": 1,
                "coverage_summaries": [
                    {
                        "primary_need_id": "REQ_1",
                        "files": {"total": 1, "measured": 1},
                        "lines": {"total": 1, "percent": 100},
                        "branches": {"total": 0, "percent": None},
                    }
                ],
            }
        )
    )
    (tmp_path / "conf.py").write_text(
        'extensions = ["sphinx_needs", "score_coverage"]\nmaster_doc = "index"\n'
        'needs_layouts = {"focus": {"grid": "content", "layout": {}}}\n'
        'needs_default_layout = "focus"\n'
        f"score_coverage_summary = {str(summary)!r}\n"
    )
    (tmp_path / "index.rst").write_text(
        "Example\n=======\n\n.. req:: Selected\n   :id: REQ_1\n\n   Original content.\n"
    )
    app = SphinxTestApp(
        srcdir=tmp_path, builddir=tmp_path / "_build", buildername="html", freshenv=True
    )
    try:
        app.build(force_all=True)
        html = (app.outdir / "index.html").read_text()
        assert "Original content." in html
        assert "score-coverage" not in html
        assert not app.warning.getvalue()
    finally:
        app.cleanup()


def _write_report_project(tmp_path: Path, *, template: bool = False) -> Path:
    """Use the real report template when checking the cross-document Need graph."""
    summary = tmp_path / "coverage.json"
    (tmp_path / "conf.py").write_text(
        'extensions = ["sphinx_needs", "sphinx_design", '
        '"score_sphinx_needs_templates"]\n'
        'master_doc = "index"\n'
        'needs_id_regex = r"^[a-zA-Z0-9_]+$"\n'
        f"score_coverage_summary = {str(summary)!r}\n"
        'needs_types = [dict(directive=t, title=t, prefix=t + "__", '
        'color="#ffffff", style="node") for t in ("req", "mod", "comp", "mod_ver_report")]\n'
        'needs_fields = {name: {"schema": {"type": "string"}, "default": ""} for name in ["safety", "security", "applies_to_module_version", "testlink"]}\n'
        'needs_links = {t: dict(incoming=t + " back", outgoing=t) '
        'for t in ("includes", "belongs_to", "satisfied_by", "realizes", '
        '"fully_verifies", "partially_verifies", "derived_from")}\n'
    )
    if template:
        (tmp_path / "index.rst").write_text(
            "Report\n======\n\n.. toctree::\n\n   components\n\n"
            ".. mod_ver_report:: Example report\n   :id: report__example\n"
            "   :belongs_to: mod__example\n"
            "   :post_template: module_verification_report\n"
        )
        workproducts = (
            "requirements_inspect",
            "sw_arch_verification",
            "sw_implementation_inspection",
            "sw_component_dfa",
            "sw_component_fmea",
        )
        (tmp_path / "components.rst").write_text(
            "Components\n==========\n\n.. mod:: Module\n   :id: mod__example\n"
            "   :includes: comp__example\n\n"
            ".. comp:: Example component\n   :id: comp__example\n"
            "   :safety: QM\n   :security: NO\n\n"
            + "\n\n".join(
                f".. req:: {name}\n   :id: wp__{name}" for name in workproducts
            )
            + "\n"
        )
    else:
        (tmp_path / "index.rst").write_text(
            "Report\n======\n\n.. req:: Component\n   :id: comp__example\n\n"
            ".. score-coverage-report:: comp__example\n   :title: Example component\n\n"
            ".. score-coverage-report:: comp__unselected\n   :title: Unselected\n"
        )
    return summary


def _write_report_summary(
    path: Path, *, total: int | None = 3, percent: int | None = 67, measured: int = 2
) -> None:
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "coverage_summaries": [
                    {
                        "primary_need_id": "comp__example",
                        "files": {"total": 6, "measured": measured},
                        "lines": {"total": total, "percent": percent},
                        "branches": {
                            "total": total,
                            "percent": 100 if percent is not None else None,
                        },
                    }
                ],
            }
        )
    )


@pytest.mark.parametrize(
    ("total", "percent", "measured", "state"),
    [
        (3, 67, 2, "covered 67%"),
        (3, 0, 2, "covered 0%"),
        (0, None, 2, "not instrumented"),
        (None, None, 0, "no data"),
    ],
)
def test_report_pies_use_summary_percentages_and_preserve_unavailable_states(
    tmp_path: Path, total: int | None, percent: int | None, measured: int, state: str
) -> None:
    summary = _write_report_project(tmp_path)
    _write_report_summary(summary, total=total, percent=percent, measured=measured)
    app = SphinxTestApp(srcdir=tmp_path, builddir=tmp_path / "_build", freshenv=True)
    try:
        app.build()
        html = (app.outdir / "index.html").read_text()
        assert state in html
        assert f"{measured}/6 selected source files" in html
        assert "No coverage data available for this component." in html
        images = list((app.outdir / "_images").glob("score_coverage_pie_*.svg"))
        assert len(images) == (2 if percent is not None else 0)
        if percent is not None:
            # Percentage slices must never acquire fabricated source-item counts.
            svg = "\n".join(image.read_text() for image in images)
            assert f"{percent}%" in svg
            assert f"({percent})" not in svg
        assert not app.warning.getvalue()
    finally:
        app.cleanup()


def test_summary_changes_alone_refresh_report_pies_and_need_metadata(
    tmp_path: Path,
) -> None:
    """An incremental build must notice summary appearance, edits and removal."""
    summary = _write_report_project(tmp_path)
    app = SphinxTestApp(srcdir=tmp_path, builddir=tmp_path / "_build", freshenv=True)
    try:
        app.build()
        assert "No coverage data available" in (app.outdir / "index.html").read_text()
        for percent in (67, 33):
            _write_report_summary(summary, percent=percent)
            # Sphinx compares dependency mtimes to the last document read time.
            # Advance only the input timestamp, without sleeping or editing RST.
            modified = time.time() + 2
            os.utime(summary, (modified, modified))
            app.build()
            html = (app.outdir / "index.html").read_text()
            assert f"covered {percent}%" in html
            assert f"lines {percent}%" in html
        summary.unlink()
        app.build()
        html = (app.outdir / "index.html").read_text()
        assert "No coverage data available" in html
        assert 'score-coverage"' not in html
        assert not app.warning.getvalue()
    finally:
        app.cleanup()


@pytest.mark.parametrize("parallel", [1, 2])
def test_module_report_resolves_component_coverage_after_need_collection(
    tmp_path: Path, parallel: int
) -> None:
    """The real post-template can find coverage for a component in another document."""
    summary = _write_report_project(tmp_path, template=True)
    _write_report_summary(summary)
    app = SphinxTestApp(
        srcdir=tmp_path, builddir=tmp_path / "_build", freshenv=True, parallel=parallel
    )
    try:
        app.build()
        html = (app.outdir / "index.html").read_text()
        assert "Example component Line Coverage: covered 67%, not covered 33%" in html
        assert "Example component Branch Coverage: covered 100%, not covered 0%" in html
        assert "2/6 selected source files" in html
        assert not app.warning.getvalue()
    finally:
        app.cleanup()


@pytest.mark.parametrize("builder", ["needs", "linkcheck"])
def test_report_checks_do_not_read_coverage_inputs(
    tmp_path: Path, builder: str
) -> None:
    """Coverage belongs to HTML rendering; exports and checks ignore even invalid JSON."""
    summary = _write_report_project(tmp_path, template=True)
    summary.write_text("not JSON")
    app = SphinxTestApp(
        srcdir=tmp_path,
        builddir=tmp_path / "_build",
        buildername=builder,
        freshenv=True,
    )
    try:
        app.build()
        assert not app.warning.getvalue()
        assert not list(app.outdir.rglob("score_coverage_pie_*"))
    finally:
        app.cleanup()
