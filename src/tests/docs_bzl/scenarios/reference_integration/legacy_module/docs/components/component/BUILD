# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
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

load("//:docs.bzl", "docs")

filegroup(
    name = "component_sources",
    srcs = ["implementation.py"],
)

# Keep the component as a complete documentation producer while placing its
# Bazel package below the module's source directory. This mirrors the feature
# package layout used by the S-CORE integration and exercises package-aware
# source ownership at runtime. The implementation file is deliberately
# supplied through ``code_targets`` so its traceability annotation exercises
# the source-link generation path used by real component targets.
docs(
    project = "S-CORE Legacy Component",
    project_url = "https://example.invalid/score-legacy-component",
    source_dir = ".",
    data = [
        "//src/tests/docs_bzl/scenarios/reference_integration/score_platform:needs_json",
    ],
    code_targets = [":component_sources"],
)
