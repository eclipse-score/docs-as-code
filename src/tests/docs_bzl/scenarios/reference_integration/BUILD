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

# The reference integration combines platform feature requirements and two
# software modules into one documentation site, just like the real S-CORE
# integration. Each module's bundle contains its component documentation.
# The component packages live below the module's ``docs`` source directory,
# matching the feature-package layout used by the real S-CORE integration.
#
# One module and its component use the older ``docs(data = [...])`` API; the
# other module and component use ``external_needs``. The integration mounts
# both module bundles, exercising both paths through the complete hierarchy.
#
# test_sources scopes the test-code-linker to this (test-less) package, avoiding
# the workspace-wide bazel-testlogs scan during the html build.
docs(
    project = "S-CORE Reference Integration",
    project_url = "https://example.invalid/score-reference-integration",
    source_dir = "docs",
    external_needs = ["//src/tests/docs_bzl/scenarios/reference_integration/score_platform:needs_json"],
    test_sources = ["src/tests/docs_bzl/scenarios/reference_integration"],
    bundles = [
        {
            "bundle": "//src/tests/docs_bzl/scenarios/reference_integration/legacy_module:docs_bundle",
            "mount_at": "modules/legacy_module",
            "attach_to": "modules",
        },
        {
            "bundle": "//src/tests/docs_bzl/scenarios/reference_integration/modern_module:docs_bundle",
            "mount_at": "modules/modern_module",
            "attach_to": "modules",
        },
    ],
)
