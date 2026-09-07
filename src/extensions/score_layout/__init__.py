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
import logging
import os
from pathlib import Path
from typing import Any, cast

import html_options
import sphinx_options
from sphinx.application import Sphinx

from src.helper_lib import config_setdefault

logger = logging.getLogger(__name__)

# TEMP UNTIL UPSTREAM FIX - BEGIN
# Bug ref: https://github.com/useblocks/sphinx-needs/issues/1913
# Sphinx-Needs discovers these files with ``Path.glob``.  The filesystem
# does not define the order returned by that operation, while Sphinx preserves
# registration order for stylesheets with the same priority.  Keep the CSS
# cascade stable across Bazel runfiles, local virtual environments, and CI.
_NEEDS_COMMON_CSS_ORDER = (
    "sphinx-needs/common_css/needstable.css",
    "sphinx-needs/common_css/need_core.css",
    "sphinx-needs/common_css/need_style.css",
    "sphinx-needs/common_css/need_toggle.css",
    "sphinx-needs/common_css/need_links.css",
)
_NEEDS_COMMON_CSS_POSITION = {
    filename: position for position, filename in enumerate(_NEEDS_COMMON_CSS_ORDER)
}
# TEMP UNTIL UPSTREAM FIX - END


def setup(app: Sphinx) -> dict[str, str | bool]:
    logger.debug("score_layout setup called")

    app.connect("config-inited", update_config)
    app.connect("html-page-context", normalize_needs_css_order)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def update_config(app: Sphinx, _config: Any):
    logger.debug("score_layout update_config called")

    # Merge: user's entries take precedence over our defaults
    app.config.needs_layouts = {
        **sphinx_options.needs_layouts,
        **app.config.needs_layouts,
    }
    config_setdefault(
        app.config, "needs_default_layout", sphinx_options.needs_default_layout
    )
    config_setdefault(app.config, "html_theme", html_options.html_theme)
    app.config.html_context = {
        **html_options.return_html_context(app),
        **app.config.html_context,
    }
    app.config.html_theme_options = {
        **html_options.return_html_theme_options(app),
        **app.config.html_theme_options,
    }

    logger.debug(f"score_layout __file__: {__file__}")

    score_layout_path = Path(__file__).parent.resolve()
    logger.debug(f"score_layout_path: {score_layout_path}")

    app.config.html_static_path.append(str(score_layout_path / "assets"))

    puml = score_layout_path / "assets" / "puml-theme-score.puml"
    app.config.needs_flow_configs.setdefault("score_config", f"!include {puml}")

    app.add_css_file("css/score.css", priority=500)
    app.add_css_file("css/score_needs.css", priority=500)
    app.add_css_file("css/score_design.css", priority=500)


# TEMP UNTIL UPSTREAM FIX - BEGIN
# Bug ref: https://github.com/useblocks/sphinx-needs/issues/1913
def normalize_needs_css_order(
    _app: Sphinx,
    _pagename: str,
    _templatename: str,
    context: dict[str, Any],
    _doctree: Any,
) -> None:
    """Make Sphinx-Needs common stylesheets deterministic before rendering."""
    css_files = context.get("css_files")
    if not isinstance(css_files, list):
        return
    css_files = cast(list[Any], css_files)

    common_css = [
        (index, css_file)
        for index, css_file in enumerate(css_files)
        if _css_filename(css_file) in _NEEDS_COMMON_CSS_POSITION
    ]
    if len(common_css) < 2:
        return

    positions = [index for index, _ in common_css]
    ordered_common_css = sorted(
        (css_file for _, css_file in common_css),
        key=lambda css_file: _NEEDS_COMMON_CSS_POSITION[_css_filename(css_file)],
    )
    normalized_css_files = list(css_files)
    for index, css_file in zip(positions, ordered_common_css, strict=True):
        normalized_css_files[index] = css_file
    context["css_files"] = normalized_css_files


def _css_filename(css_file: Any) -> str:
    """Return a stylesheet's path in the form used by Sphinx-Needs."""
    filename = str(os.fspath(getattr(css_file, "filename", css_file)))
    return Path(filename).as_posix().removeprefix("_static/")


# TEMP UNTIL UPSTREAM FIX - END
