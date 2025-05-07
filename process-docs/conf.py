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


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "docs-as-code"
author = "Score"
version = "0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

logger = logging.getLogger("process-docs")
logger.debug("Loading docs-as-code conf.py")


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

logger.debug("After loading extensions")

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


logger.debug("After loading S-CORE conf.py")
