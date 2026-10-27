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

# Keep this consumer separate from the producers' source trees. That lets the
# runtime test load a public docs_bundle export and a needs_json_file from
# different packages without importing the same Need twice.
docs(
    source_dir = "docs",
    project = "External Needs Inputs",
    project_url = "https://example.invalid/external-needs-inputs",
    test_sources = ["src/tests/docs_bzl/scenarios/external_needs_inputs"],
    external_needs = [
        # A docs() label resolves to that producer's local Needs inventory.
        "//src/tests/docs_bzl/scenarios/reference_integration/score_platform:docs",
        # A docs_bundle() label resolves to its local Needs inventory.
        "//src/tests/docs_bzl/scenarios/external_needs_inputs/bundle:docs_bundle",
        # A direct inventory file label remains supported for non-bundle inputs.
        "//src/tests/docs_bzl/scenarios/subdirectory_bundle/producer:needs_json_file",
    ],
)
