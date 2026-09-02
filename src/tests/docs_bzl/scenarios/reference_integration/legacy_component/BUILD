# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

load("//:docs.bzl", "docs")

# A component documentation bundle mounted by the legacy module.
docs(
    project = "S-CORE Legacy Component",
    project_url = "https://example.invalid/score-legacy-component",
    source_dir = "docs",
    data = [
        "//src/tests/docs_bzl/scenarios/reference_integration/score_platform:needs_json",
    ],
)
