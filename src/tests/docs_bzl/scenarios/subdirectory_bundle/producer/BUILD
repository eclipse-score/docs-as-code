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

# The embedded bundle lives in a subdirectory package alongside the docs source.
# The parent docs() must mount it explicitly because it is a separate package.
docs(
    source_dir = "docs",
    project = "Subdirectory Bundle Producer",
    project_url = "https://example.invalid/subdirectory-bundle-producer",
    test_sources = ["src/tests/docs_bzl/scenarios/subdirectory_bundle/producer"],
    bundles = [{
        "bundle": "//src/tests/docs_bzl/scenarios/subdirectory_bundle/producer/embedded:docs_bundle",
        "mount_at": "embedded",
    }],
)
