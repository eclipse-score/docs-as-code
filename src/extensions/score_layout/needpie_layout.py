# *******************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
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
"""Re-layout Sphinx-Needs pie charts so they survive narrow columns.

Sphinx-Needs hardcodes ``figsize=(8, 4)`` and anchors the legend to the right of
the pie, which leaves the circle filling only ~40% of the image width. Three
charts side by side shrink it past readability. Neither value is reachable from
the directive, so the finished figure is re-laid out just before it is written.
"""

from typing import Any

import sphinx_needs.directives.needpie
from docutils import nodes
from sphinx.application import Sphinx
from sphinx_needs.utils import save_matplotlib_figure

# A square figure with the legend underneath grows the circle to ~80% of the
# image width, while the tight bounding box keeps the image barely wider than
# its title.
_FIGURE_SIZE_INCHES = (6, 6)
_LEGEND_FONT_SIZE = 9


def _move_legend_below_pie(axes: Any) -> None:
    legend = axes.get_legend()
    if legend is None:
        return
    # ``Axes.legend`` replaces the current legend, so the old one needs no removal.
    # The "legend" heading is dropped: it costs height and carries no information.
    axes.legend(
        list(legend.legend_handles),
        [text.get_text() for text in legend.get_texts()],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.02),
        ncol=1,
        frameon=False,
        borderaxespad=0,
        handlelength=1.2,
        fontsize=_LEGEND_FONT_SIZE,
    )


def save_needpie_figure(
    app: Sphinx, figure: Any, basename: str, fromdocname: str
) -> nodes.image:
    """Drop-in for ``save_matplotlib_figure`` that restyles the figure first."""
    if figure.axes:
        _move_legend_below_pie(figure.axes[0])
        figure.set_size_inches(*_FIGURE_SIZE_INCHES)
    return save_matplotlib_figure(app, figure, basename, fromdocname)


def patch_needpie_layout() -> None:
    """Patch only the ``needpie`` module, leaving ``needbar`` charts untouched."""
    sphinx_needs.directives.needpie.save_matplotlib_figure = save_needpie_figure
