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

# Example for docs/how-to/bundles/examples.rst ("Nest bundles"). The project's
# own documentation mounts :parent, and the nested_bundles end-to-end scenario
# in src/tests/end_to_end tests the same targets.

load("@aspect_rules_py//py:defs.bzl", "py_binary")
load("//:docs.bzl", "docs_bundle")

package(default_visibility = ["//visibility:public"])

docs_bundle(
    name = "child",
    code_targets = [
        ":example_binary",
        ":example_executable",
        ":nested_filegroup_sources",
    ],
    entry_doc = "landing",
    source_dir = "child",
)

filegroup(
    name = "filegroup_sources",
    srcs = ["child/filegroup_source.py"],
)

filegroup(
    name = "nested_filegroup_sources",
    srcs = [":filegroup_sources"],
)

filegroup(
    name = "generated_doc_output",
    srcs = ["generated/generated_output.txt"],
    visibility = ["//visibility:private"],
)

py_binary(
    name = "example_binary",
    srcs = ["child/example.py"],
    main = "child/example.py",
)

cc_library(
    name = "example_library",
    srcs = ["child/example.cc"],
)

cc_binary(
    name = "example_executable",
    srcs = ["child/example_main.cc"],
    deps = [":example_library"],
)

docs_bundle(
    name = "parent",
    bundles = [{
        "bundle": ":child",
        "mount_at": "child",
    }],
    data = [":generated_doc_output"],
    source_dir = "parent",
)
