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

# This fixture represents an S-CORE software module using the legacy API:
#
#   score_platform:needs_json
#       -> legacy_module: docs(data = [score_platform:needs_json])
#       -> legacy_module:docs_bundle
#       -> reference integration mounts that bundle
#
# The legacy ``docs(data = [...])`` form remains in use by module repositories.
# The reference integration is essential because it assembles the module's
# documentation bundle with the rest of the platform documentation. The
# module itself assembles its component documentation below ``components/``.
# The component package is physically below this module's ``docs`` source tree,
# so the module's primary Sphinx walk must leave ownership to the child mount.
docs(
    project = "S-CORE Legacy Module",
    project_url = "https://example.invalid/score-legacy-module",
    source_dir = "docs",
    test_sources = ["src/tests/docs_bzl/scenarios/reference_integration"],
    data = [
        "//src/tests/docs_bzl/scenarios/reference_integration/score_platform:needs_json",
        "@score_process_description//:needs_json",
    ],
    bundles = [{
        "bundle": "//src/tests/docs_bzl/scenarios/reference_integration/legacy_module/docs/components/component:docs_bundle",
        "mount_at": "components/component",
        "attach_to": "components",
    }],
)
