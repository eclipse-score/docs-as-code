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

# Consume the producer's complete public docs bundle. This exercises the
# transitive bundle assembled by producer/docs(), including its subdirectory
# bundle, without adding the producer's needs_json separately.
docs(
    source_dir = "docs",
    project = "Subdirectory Bundle Consumer",
    project_url = "https://example.invalid/subdirectory-bundle-consumer",
    test_sources = ["src/tests/docs_bzl/scenarios/subdirectory_bundle/consumer"],
    bundles = [{
        "bundle": "//src/tests/docs_bzl/scenarios/subdirectory_bundle/producer:docs_bundle",
        "mount_at": "producer",
    }],
)
