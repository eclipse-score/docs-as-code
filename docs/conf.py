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

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Score Docs-as-Code"
project_url = "https://eclipse-score.github.io/docs-as-code/"
project_prefix = "DOCS_"
author = "S-CORE"
version = "0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx_design",
    "sphinx_needs",
    "myst_parser",
    "sphinxcontrib.plantuml",
    "score_plantuml",
    "score_metamodel",
    "score_draw_uml_funcs",
    "score_source_code_linker",
    "score_layout",
]

myst_enable_extensions = ["colon_fence"]

exclude_patterns = [
    # The following entries are not required when building the documentation via 'bazel
    # build //:docs', as that command runs in a sandboxed environment. However, when
    # building the documentation via 'bazel run //:docs' or esbonio, these
    # entries are required to prevent the build from failing.
    "bazel-*",
    ".venv*",
]

# Enable markdown rendering
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["templates"]


# Enable numref
numfig = True
# needs_builder_filter = ""
