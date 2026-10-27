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
import re
from html import unescape
from pathlib import Path

import pytest
from sphinx.testing.util import SphinxTestApp


def test_metamodel_registers_coverage_without_the_extension_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Individual SCORE extensions accept the CLI override, including with -W."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BUILD_WORKSPACE_DIRECTORY", str(tmp_path))
    summary = tmp_path / "coverage.json"
    summary.write_text(json.dumps({"version": 1, "coverage_summaries": []}))
    (tmp_path / "conf.py").write_text(
        'extensions = ["sphinx_needs", "score_metamodel"]\nmaster_doc = "index"\n'
        'project_url = "https://example.invalid/coverage"\n'
        'external_needs_source = "[]"\n'
    )
    (tmp_path / "index.rst").write_text("Example\n=======\n")
    app = SphinxTestApp(
        srcdir=tmp_path,
        outdir=tmp_path / "_build",
        buildername="html",
        freshenv=True,
        warningiserror=True,
        confoverrides={"score_coverage_summary": str(summary)},
    )
    try:
        app.build()
        assert "score_coverage" in app.extensions
        assert app.config.score_coverage_summary == str(summary)
        assert not app.warning.getvalue()
        assert app.statuscode == 0
    finally:
        app.cleanup()


@pytest.mark.parametrize(
    ("total", "percent", "measured", "expected"),
    [
        (3, 67, 2, "lines 67%"),
        (1, 0, 2, "lines 0%"),
        (0, None, 2, "lines not instrumented"),
        (None, None, 0, "lines no data"),
    ],
)
def test_summary_is_rendered_only_inside_the_matching_need(
    tmp_path: Path,
    total: int | None,
    percent: int | None,
    measured: int,
    expected: str,
) -> None:
    """Need IDs select the attribute; zero, missing data and no instrumentation differ."""
    summary = tmp_path / "coverage.json"
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
    (tmp_path / "conf.py").write_text(
        'extensions = ["sphinx_needs", "score_coverage"]\n'
        'master_doc = "index"\n'
        f"score_coverage_summary = {str(summary)!r}\n"
    )
    (tmp_path / "index.rst").write_text(
        "Example\n=======\n\n.. req:: Selected\n   :id: REQ_1\n\n   Original content.\n\n"
        ".. req:: Unselected\n   :id: REQ_2\n\n"
        ".. list-table::\n   :class: need\n\n   * - Ordinary table\n"
    )
    app = SphinxTestApp(
        srcdir=tmp_path, outdir=tmp_path / "_build", buildername="html", freshenv=True
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
        srcdir=tmp_path, outdir=tmp_path / "_build", buildername="html", freshenv=True
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
        srcdir=tmp_path, outdir=tmp_path / "_build", buildername="html", freshenv=True
    )
    try:
        app.build(force_all=True)
        html = (app.outdir / "index.html").read_text()
        assert "Original content." in html
        assert "score-coverage" not in html
        assert not app.warning.getvalue()
    finally:
        app.cleanup()
