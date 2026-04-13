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
from pathlib import Path
from typing import Any

import html_options
import sphinx_options
from sphinx.application import Sphinx

from src.helper_lib import config_setdefault

logger = logging.getLogger(__name__)


def setup(app: Sphinx) -> dict[str, str | bool]:
    logger.debug("score_layout setup called")

    app.connect("config-inited", update_config)
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
