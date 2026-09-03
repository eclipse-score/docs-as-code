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

filegroup(
    name = "component_sources",
    srcs = ["implementation.py"],
)

# This component is a nested documentation package, like the feature bundles
# in the S-CORE integration. Its parent module owns the surrounding source
# tree and mounts this bundle at the component placement. The implementation
# file is supplied through ``code_targets`` to exercise source-link generation
# for a component that is propagated through the module bundle.
docs(
    project = "S-CORE Modern Component",
    project_url = "https://example.invalid/score-modern-component",
    source_dir = ".",
    external_needs = [
        "//src/tests/docs_bzl/scenarios/reference_integration/score_platform:needs_json",
    ],
    code_targets = [":component_sources"],
)
