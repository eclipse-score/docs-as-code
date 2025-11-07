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

project = "Score Docs-as-Code"
project_url = "https://eclipse-score.github.io/docs-as-code/"
version = "0.1"

extensions = [
    # TODO remove plantuml here once docs-as-code is updated to sphinx-needs 6
    "sphinxcontrib.plantuml",
    "score_sphinx_bundle",
]
