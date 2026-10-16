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

filegroup(
    name = "component_sources",
    srcs = ["implementation.py"],
)

# The component owns its implementation and local supporting library. Public
# headers may be declared through filegroups in either component. Dependency
# membership is determined by target package, independently of header location.
cc_library(
    name = "implementation",
    srcs = ["implementation.cc"],
    hdrs = [":public_headers"],
    textual_hdrs = [":generated_config"],
    # The sibling dependency itself uses our local support library. Component
    # membership follows labels even when the dependency path leaves the package.
    deps = [
        "//src/tests/docs_bzl/scenarios/reference_integration/modern_module/docs/components/unlinked_component:implementation",
        "@bazel_tools//tools/cpp:malloc",
    ],
)

filegroup(
    name = "public_headers",
    srcs = [
        ":local_headers",
        "//src/tests/docs_bzl/scenarios/reference_integration/modern_module/docs/components/unlinked_component:public_headers",
    ],
)

filegroup(
    name = "local_headers",
    srcs = ["api.h"],
)

# The library consumes the generated header through textual_hdrs, which
# identifies it as code even without a conventional C++ filename suffix.
genrule(
    name = "generated_config",
    srcs = ["api.h"],
    outs = ["generated/config.def"],
    cmd = "cp $< $@",
)

exports_files(["api.h"])

# This component is a nested documentation package, like the feature bundles
# in the S-CORE integration. Its parent module owns the surrounding source
# tree and mounts this bundle at the component placement. The implementation
# file is supplied through ``code_targets`` to exercise source-link generation
# for a component that is propagated through the module bundle.
#
# The component intentionally does not import the platform Needs itself. Its
# requirement links to the platform feature, so the component Needs target is
# valid only when the parent module supplies that external Needs.
docs_bundle(
    # Deliberately keep the Bazel target name independent from the Need ID.
    # The component Need is selected explicitly even though this page contains
    # feature, component, requirement, and tool Needs.
    name = "docs_bundle",
    source_dir = ".",
    code_targets = [
        ":component_sources",
        ":implementation",
    ],
    primary_need_id = "comp__modern_component",
    visibility = ["//visibility:public"],
)

# This independent bundle deliberately selects a sibling's header-only API.
# Its own files remain selected, but its sibling implementation dependency does
# not become ours. The local support library behind that dependency is eligible.
docs_bundle(
    name = "selected_sibling_api",
    code_targets = ["//src/tests/docs_bzl/scenarios/reference_integration/modern_module/docs/components/unlinked_component:api"],
    visibility = ["//visibility:private"],
)
