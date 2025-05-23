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

load("@aspect_rules_py//py:defs.bzl", "py_library")
load("//:docs.bzl", "docs")

# Creates all documentation targets:
# - `docs:incremental` for building docs incrementally at runtime
# - `docs:live_preview` for live preview in the browser without an IDE
# - `docs:ide_support` for creating python virtualenv for IDE support
# - `docs:docs` for building documentation at build-time

docs(
    conf_dir = "examples/linking-both",
    docs_targets = [
        {
            "suffix": "latest",  # latest main branch documentation build
            "external_needs_info": [
                {
                    "base_url": "https://eclipse-score.github.io/score/main",
                    "json_url": "https://eclipse-score.github.io/score/main/needs.json",
                    "id_prefix": "score_",
                },
            ],
        },
        {
            "suffix": "release",  # The version imported from MODULE.bazel
            "target": ["@score_platform//docs:docs_needs"],
            "external_needs_info": [
                {
                    "base_url": "https://eclipse-score.github.io/score/main",
                    "json_path": "/score_platform~/docs/docs_needs/_build/needs/needs.json",
                    "id_prefix": "score_",
                },
            ],
        },
    ],
    source_dir = "examples/linking-both",
    source_files_to_scan_for_needs_links = [
        "//src:score_extension_files",
    ],
)
