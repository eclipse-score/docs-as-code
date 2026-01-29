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
from sphinx.application import Sphinx

# Note: order matters!
# Extensions are loaded in this order.
# e.g. plantuml MUST be loaded before sphinx-needs
score_extensions = [
    # needs_config_writer must be loaded before score_metamodel
    # due to conflict in priorities.
    "needs_config_writer",
    "score_sync_toml",
    "sphinxcontrib.plantuml",
    "score_plantuml",
    "sphinx_needs",
    "score_metamodel",
    "sphinx_design",
    "myst_parser",
    "score_source_code_linker",
    "score_draw_uml_funcs",
    "score_layout",
    "sphinx_collections",
    "sphinxcontrib.mermaid",
]


def setup(app: Sphinx) -> dict[str, object]:
    app.config.html_copy_source = False
    app.config.html_show_sourcelink = False

    # Global settings
    # Note: the "sub-extensions" also set their own config values

    # Same as current VS Code extension
    app.config.mermaid_version = "11.6.0"

    # enable "..."-syntax in markdown
    app.config.myst_enable_extensions = ["colon_fence"]

    app.config.exclude_patterns = [
        # The following entries are not required when building the documentation via
        # 'bazel build //:docs', as that command runs in a sandboxed environment.
        # However, when building the documentation via 'bazel run //:docs' or esbonio,
        # these entries are required to prevent the build from failing.
        "bazel-*",
        ".venv*",
    ]

    # Enable markdown rendering
    app.config.source_suffix = {
        ".rst": "restructuredtext",
        ".md": "markdown",
    }

    app.config.templates_path = ["templates"]

    app.config.numfig = True

    app.config.author = "S-CORE"

    # Load the actual extensions list
    for e in score_extensions:
        app.setup_extension(e)

    return {
        "version": "0.1",
        # Keep this in sync with the score_docs_as_code version in MODULE.bazel
        "env_version": 200,  # 2.0.0
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
