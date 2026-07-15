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
"""Minimal Sphinx configuration for standalone needs.json generation.

Copy or reference this file as your conf.py when using the needs_json() macro
from @score_docs_as_code//:needs.bzl.

You can also use this as a starting point and extend it with your own settings.
"""

project = "my_project"

extensions = [
    "score_sphinx_bundle",
]
