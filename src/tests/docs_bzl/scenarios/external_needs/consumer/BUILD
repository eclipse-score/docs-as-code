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

# The explicit ``external_needs`` entry covers the current API for importing a
# producer's needs into the host documentation, so the :need: link in
# index.rst can resolve.
#
# The mounted legacy_consumer covers a different, older API path. The complete
# scenario is producer:needs_json -> legacy_consumer:docs(data = [...]) ->
# legacy_consumer:docs_bundle -> this consumer's bundle mount. The legacy
# invocation is valid, but it carries the generated TreeArtifact into its
# public docs_bundle. Mounting that bundle here forces the mounts manifest and
# runtime resolver to process the directory-valued data entry, reproducing the
# integration failure.
#
# test_sources scopes the test-code-linker to this (test-less) package, avoiding
# the workspace-wide bazel-testlogs scan during the html build.
docs(
    source_dir = "docs",
    external_needs = ["//src/tests/docs_bzl/scenarios/external_needs/producer:needs_json"],
    test_sources = ["src/tests/docs_bzl/scenarios/external_needs/consumer"],
    bundles = [{
        "bundle": "//src/tests/docs_bzl/scenarios/external_needs/legacy_consumer:docs_bundle",
        "mount_at": "legacy",
    }],
)
