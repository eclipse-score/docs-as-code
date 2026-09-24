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
# feature requirements and mounts two component bundles. One component has a
# requirement linked to the imported platform feature; the other is
# self-contained. Keeping both under the module's ``docs`` source tree
# exercises the distinction between a component that needs its parent bundle's
# external Needs and one that can be built independently.
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
    }, {
        "bundle": "//src/tests/docs_bzl/scenarios/reference_integration/modern_module/docs/components/unlinked_component:docs_bundle",
        "mount_at": "components/unlinked_component",
        "attach_to": "components",
    }],
)
