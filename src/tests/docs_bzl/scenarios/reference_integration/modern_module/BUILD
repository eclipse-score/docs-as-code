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

# This module uses the current ``external_needs`` API to import platform
# feature requirements and mounts its component documentation. The component
# package is nested below this module's ``docs`` source tree, so both the
# module's primary walk and its parent bundle mount must exclude that child.
docs(
    project = "S-CORE Modern Module",
    project_url = "https://example.invalid/score-modern-module",
    source_dir = "docs",
    test_sources = ["src/tests/docs_bzl/scenarios/reference_integration"],
    external_needs = [
        "//src/tests/docs_bzl/scenarios/reference_integration/score_platform:needs_json",
        "@score_process_description//:needs_json",
    ],
    bundles = [{
        "bundle": "//src/tests/docs_bzl/scenarios/reference_integration/modern_module/docs/components/component:docs_bundle",
        "mount_at": "components/component",
        "attach_to": "components",
    }],
)
