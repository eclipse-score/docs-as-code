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

load("//:docs.bzl", "docs_bundle")

# These scenario BUILD files are used by literalinclude examples in the root
# documentation. Keep the payload with the scenarios that own the fixtures.
docs_bundle(
    name = "docs_literalinclude_data",
    data = [
        "//src/tests/docs_bzl/scenarios/data_files_runfiles:generated_data_build",
        "//src/tests/docs_bzl/scenarios/external_bundle:external_bundle_build",
        "//src/tests/docs_bzl/scenarios/nested_bundles:nested_bundle_build",
    ],
    visibility = ["//visibility:public"],
)
