# *******************************************************************************
# Copyright (c) 2024 Contributors to the Eclipse Foundation
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

import logging

# from tooling.docs_assets_lib import get_path as asset_path
# from tooling.find_runfiles import get_runfiles_dir
# from tooling.score_extensions.find_runfiles import get_runfiles_dir
# import tooling.score_extensions

# sys.path extension for local files is needed, because the conf.py file is not
# executed, but imported by Sphinx
# sys.path.insert(0, ".")

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "SCORE Process"
author = "Score"
version = "0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

logger = logging.getLogger("process-docs")
logger.warning("Loading S-CORE conf.py")

extensions = [
    "sphinx_design",
    "sphinx_needs",
    "sphinxcontrib.plantuml",
    "score_plantuml",
    "score_metamodel",
    "score_draw_uml_funcs",
    "score_source_code_linker",
    "score_layout",
]
logger.warning("After loading extensions")

exclude_patterns = [
    # The following entries are not required when building the documentation
    # via 'bazel build //docs:docs', as that command runs in a sandboxed environment.
    # However, when building the documentation via 'sphinx-build' or esbonio,
    # these entries are required to prevent the build from failing.
    "bazel-*",
    ".venv_docs",
]

templates_path = ["templates"]

# Enable numref
numfig = True


# -- sphinx-needs configuration --------------------------------------------
# Setting the needs layouts
needs_global_options = {"collapse": True}
needs_string_links = {
    "source_code_linker": {
        "regex": r"(?P<value>[^,]+)",
        "link_url": "{{value}}",
        "link_name": "Source Code Link",
        "options": ["source_code_link"],
    },
}

# TODO: Fixing this in all builds
html_static_path = ["../tooling/assets"]

logger.warning("After loading S-CORE conf.py")
