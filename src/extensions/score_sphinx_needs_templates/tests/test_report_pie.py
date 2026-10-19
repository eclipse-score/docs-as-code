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
from pathlib import Path

import pytest
from score_pytest.attribute_plugin import add_test_properties
from score_sphinx_needs_templates.report_pie import draw_report_pie
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
