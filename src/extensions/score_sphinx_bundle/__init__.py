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

from src.helper_lib import config_setdefault

# Note: order matters!
# Extensions are loaded in this order.
# e.g. plantuml MUST be loaded before sphinx-needs
score_extensions = [
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
    "needs_config_writer",
    "score_sync_toml",
]


def setup(app: Sphinx) -> dict[str, object]:
    config_setdefault(app.config, "html_copy_source", False)
    config_setdefault(app.config, "html_show_sourcelink", False)

    # Global settings
    # Note: the "sub-extensions" also set their own config values

    # Same as current VS Code extension
    config_setdefault(app.config, "mermaid_version", "11.6.0")

    # The following entries are not required when building the documentation via
    # 'bazel build //:docs', as that command runs in a sandboxed environment.
    # However, when building the documentation via 'bazel run //:docs' or esbonio,
    # these entries are required to prevent the build from failing.
    app.config.exclude_patterns += ["bazel-*", ".venv*"]

    # Enable markdown rendering
    app.config.source_suffix.setdefault(".rst", "restructuredtext")
    app.config.source_suffix.setdefault(".md", "markdown")

    if "templates" not in app.config.templates_path:
        app.config.templates_path += ["templates"]

    config_setdefault(app.config, "numfig", True)
    config_setdefault(app.config, "author", "S-CORE")

    # Load the actual extensions list
    for e in score_extensions:
        app.setup_extension(e)

    # enable "..."-syntax in markdown — must come after myst_parser is loaded above
    if isinstance(app.config.myst_enable_extensions, list):
        app.config.myst_enable_extensions.append("colon_fence")
    elif isinstance(app.config.myst_enable_extensions, set):
        app.config.myst_enable_extensions.add("colon_fence")
    else:
        print(
            "Unexpected type for myst_enable_extensions: %s",
            type(app.config.myst_enable_extensions),
        )

    return {
        "version": "3.0.0",
        # Keep this in sync with the score_docs_as_code version in MODULE.bazel
        "env_version": 300,  # 3.0.0
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
