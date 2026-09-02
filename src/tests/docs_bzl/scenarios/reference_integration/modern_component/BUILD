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

# This component uses the current ``external_needs`` API and is mounted by the
# modern module.
docs(
    project = "S-CORE Modern Component",
    project_url = "https://example.invalid/score-modern-component",
    source_dir = "docs",
    external_needs = [
        "//src/tests/docs_bzl/scenarios/reference_integration/score_platform:needs_json",
    ],
)
