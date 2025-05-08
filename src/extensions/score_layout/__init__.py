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
from typing import Any

from sphinx.application import Sphinx
import os
from pathlib import Path
import html_options
import sphinx_options


def setup(app: Sphinx) -> dict[str, str | bool]:
    app.connect("config-inited", update_config)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def update_config(app: Sphinx, _config: Any):
    app.config.needs_layouts = sphinx_options.needs_layouts
    app.config.needs_global_options = sphinx_options.needs_global_options
    app.config.html_theme = html_options.html_theme
    app.config.html_context = html_options.html_context
    app.config.html_theme_options = html_options.return_html_theme_options(app)

    # Setting HTML static path
    # For now this seems the only place this is used / needed.
    # In the future it might be a good idea to make this available in other places, maybe via the 'find_runfiles' lib
    if r := os.getenv("RUNFILES_DIR"):
        dirs = [str(x) for x in Path(r).glob("*score_docs_as_code~")]
        if dirs:
            # Happens if 'score_docs_as_code' is used as Module
            p = str(r) + "/score_docs_as_code~/src/assets"
        else:
            # Only happens in 'score_docs_as_code' repository
            p = str(r) + "/_main/src/assets"
        app.config.html_static_path = app.config.html_static_path + [p]

    app.add_css_file("css/score.css", priority=500)
    app.add_css_file("css/score_needs.css", priority=500)
    app.add_css_file("css/score_design.css", priority=500)
