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
from types import SimpleNamespace
from typing import cast

import pytest
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx.testing.util import SphinxTestApp

from src.extensions import score_coverage


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


def test_summary_changes_invalidate_consumers_without_bundle_file_dependencies(
    tmp_path: Path,
) -> None:
    """A build-wide summary must refresh consumers without escaping mounted bundle roots."""
    summary = tmp_path / "coverage.json"
    env = cast(
        BuildEnvironment,
        SimpleNamespace(
            docname="consumer",
            metadata={"consumer": {}, "prose": {}},
            dependencies={},
        ),
    )
    app = cast(
        Sphinx,
        SimpleNamespace(
            builder=SimpleNamespace(format="html"),
            config=SimpleNamespace(score_coverage_summary=str(summary)),
            env=env,
        ),
    )
    outdated = vars(score_coverage)["_outdated_coverage_docs"]
    score_coverage.note_coverage_dependency(app)
    assert outdated(app, env, set(), set(), set()) == []
    summary.write_text("first result")
    assert outdated(app, env, set(), set(), set()) == ["consumer"]
    score_coverage.note_coverage_dependency(app)
    summary.write_text("first result")
    assert outdated(app, env, set(), set(), set()) == []
    summary.write_text("changed result")
    assert outdated(app, env, set(), set(), set()) == ["consumer"]
    assert outdated(app, env, set(), set(), {"consumer"}) == []
    score_coverage.note_coverage_dependency(app)
    summary.unlink()
    assert outdated(app, env, set(), set(), set()) == ["consumer"]
    assert env.metadata["prose"] == {}
    assert env.dependencies == {}


@pytest.mark.parametrize("builder", ["needs", "linkcheck"])
def test_documentation_checks_ignore_summary_changes(builder: str) -> None:
    """Export and check builders neither track nor open coverage inputs."""
    env = cast(BuildEnvironment, SimpleNamespace(metadata={}))
    # No configuration or file access is available on this test double.
    app = cast(
        Sphinx, SimpleNamespace(builder=SimpleNamespace(format=builder), env=env)
    )
    score_coverage.note_coverage_dependency(app)
    assert (
        vars(score_coverage)["_outdated_coverage_docs"](app, env, set(), set(), set())
        == []
    )
    assert env.metadata == {}
