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
import os
from pathlib import Path
from typing import Any

import html_options
import sphinx_options
from sphinx.application import Sphinx


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
    app.config.html_context = html_options.return_html_context(app)
    app.config.html_theme_options = html_options.return_html_theme_options(app)

    # Setting HTML static path
    if r := os.getenv("RUNFILES_DIR"):
        if (Path(r) / "score_docs_as_code+").exists():
            # Docs-as-code used as a module with bazel 8
            module = "score_docs_as_code+"
        elif (Path(r) / "score_docs_as_code~").exists():
            # Docs-as-code used as a module with bazel 7
            module = "score_docs_as_code~"
        else:
            # Docs-as-code is the current module
            module = "_main"
        app.config.html_static_path.append(str(Path(r) / module / "src/assets"))

    app.add_css_file("css/score.css", priority=500)
    app.add_css_file("css/score_needs.css", priority=500)
    app.add_css_file("css/score_design.css", priority=500)
