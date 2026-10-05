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

# Keep this package dedicated to the deprecated data-input diagnostic. No
# other test builds its targets, so the package-loading message can be checked
# without depending on Bazel printing it again for an already-loaded package.
docs(
    source_dir = "docs",
    project = "Deprecated Needs Data Input",
    project_url = "https://example.invalid/deprecated-needs-data-input",
    data = [
        "//src/tests/docs_bzl/scenarios/reference_integration/score_platform:needs_json_file",
    ],
)
