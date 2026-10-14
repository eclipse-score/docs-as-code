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

docs(
    data = ["supporting-example.txt"],
    project = "Basic Test",
    project_url = "https://github.com/eclipse-score/docs-as-code",
    source_dir = "docs",
    test_sources = ["src/tests/docs_bzl/scenarios/basic_docs"],
)

# This explicitly selected target lives outside the bundle package. The two
# filegroups below exercise source discovery through a nested filegroup chain,
# including a source file owned by this sibling package.
cc_library(
    name = "nested_bundles_outside_library",
    srcs = [
        "outside_component.cc",
        "//src/tests/docs_bzl/scenarios/nested_bundles:child/example.cc",
    ],
    hdrs = ["//src/tests/docs_bzl/scenarios/nested_bundles:child/example_api.h"],
    visibility = ["//visibility:public"],
    deps = ["@bazel_tools//tools/cpp:malloc"],
)

# This sibling-package dependency points back into the bundle package. When it
# is reached as a dependency, traversal must stop at this target and must not
# resume at branch_only_library.
cc_library(
    name = "nested_bundles_sibling_bridge",
    srcs = ["outside_component.cc"],
    visibility = ["//visibility:public"],
    deps = ["//src/tests/docs_bzl/scenarios/nested_bundles:branch_only_library"],
)

filegroup(
    name = "nested_bundles_source_files_inner",
    srcs = ["outside_component.cc"],
    visibility = ["//visibility:public"],
)

filegroup(
    name = "nested_bundles_source_files",
    srcs = [":nested_bundles_source_files_inner"],
    visibility = ["//visibility:public"],
)

filegroup(
    name = "nested_bundles_header_files_inner",
    srcs = ["outside_component.h"],
    visibility = ["//visibility:public"],
)

filegroup(
    name = "nested_bundles_header_files",
    srcs = [":nested_bundles_header_files_inner"],
    visibility = ["//visibility:public"],
)

filegroup(
    name = "nested_bundles_outside_inner",
    srcs = [":nested_bundles_outside_library"],
    visibility = ["//visibility:public"],
)

filegroup(
    name = "nested_bundles_outside_gateway",
    srcs = [":nested_bundles_outside_inner"],
    visibility = ["//visibility:public"],
)
