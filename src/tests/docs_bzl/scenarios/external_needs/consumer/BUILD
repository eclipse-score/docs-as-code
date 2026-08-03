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

# Mounts the same-repo producer's needs.json so the :need: link in index.rst can
# resolve. test_sources scopes the test-code-linker to this (test-less) package,
# avoiding the workspace-wide bazel-testlogs scan during the html build.
docs(
    source_dir = "docs",
    external_needs = ["//src/tests/docs_bzl/scenarios/external_needs/producer:needs_json"],
    test_sources = ["src/tests/docs_bzl/scenarios/external_needs/consumer"],
)
