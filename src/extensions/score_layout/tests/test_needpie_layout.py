# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Tests for the pie chart re-layout applied to Sphinx-Needs figures."""

from typing import Any

import matplotlib
import sphinx_needs.directives.needbar
import sphinx_needs.directives.needpie

matplotlib.use("Agg")

import matplotlib.pyplot  # noqa: E402

from src.extensions.score_layout.needpie_layout import (  # noqa: E402
    _FIGURE_SIZE_INCHES,
    _move_legend_below_pie,
    patch_needpie_layout,
    save_needpie_figure,
)


def _pie_beside_legend() -> tuple[Any, Any]:
    """Build a figure shaped the way Sphinx-Needs leaves a needpie chart."""
    figure, axes = matplotlib.pyplot.subplots(
        figsize=(8, 4), subplot_kw={"aspect": "equal"}
    )
    wedges, _texts = axes.pie([3, 1])
    axes.legend(
        wedges,
        ["valid", "invalid"],
        title="legend",
        loc="center left",
        bbox_to_anchor=(0.8, 0, 0.5, 1),
    )
    return figure, axes


def test_patch_targets_needpie_only() -> None:
    """``needbar`` charts have their own proportions and must stay untouched."""
    needbar_before = sphinx_needs.directives.needbar.save_matplotlib_figure

    patch_needpie_layout()

    assert sphinx_needs.directives.needpie.save_matplotlib_figure is save_needpie_figure
    assert sphinx_needs.directives.needbar.save_matplotlib_figure is needbar_before


def test_legend_moves_below_the_pie() -> None:
    """Freeing the space beside the pie is what lets the circle grow."""
    figure, axes = _pie_beside_legend()
    figure.canvas.draw()
    assert axes.get_legend().get_window_extent().y1 > axes.get_window_extent().y0

    _move_legend_below_pie(axes)
    figure.set_size_inches(*_FIGURE_SIZE_INCHES)
    figure.canvas.draw()

    assert axes.get_legend().get_window_extent().y1 < axes.get_window_extent().y0
    matplotlib.pyplot.close(figure)


def test_chart_without_legend_is_only_resized() -> None:
    """``:legend:`` is optional, so a missing legend must not raise."""
    figure, axes = matplotlib.pyplot.subplots(
        figsize=(8, 4), subplot_kw={"aspect": "equal"}
    )
    axes.pie([1, 1])

    _move_legend_below_pie(axes)

    assert axes.get_legend() is None
    matplotlib.pyplot.close(figure)
