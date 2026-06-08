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

extensions = [
    "sphinx_needs",
    "score_metamodel",
]

needs_external_needs = [
    {
        "base_url": "https://eclipse-score.github.io/process_description/main/",
        "json_path": "needs.json",
    }
]

# We add these suppress_warnings here to ease the load of the warnings
# In the future we might want to check if ANY warnings comes in the document
# And then ensure that we error, as this could also be parsing errors etc.
suppress_warnings = ["app.add_directive", "app.add_node", "app.add_role"]
