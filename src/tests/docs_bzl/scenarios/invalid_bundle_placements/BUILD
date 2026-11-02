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

docs_bundle(
    name = "child",
    entry_doc = "a",
    source_dir = "child",
)

docs_bundle(
    name = "wrapper_x",
    bundles = [
        {
            "bundle": ":child",
            "mount_at": "x",
        },
    ],
    source_dir = "_empty",
)

docs_bundle(
    name = "wrapper_y",
    bundles = [
        {
            "bundle": ":child",
            "mount_at": "y",
        },
    ],
    source_dir = "_empty",
)

# These wrappers have the same final document location, but disagree about
# metadata that the manifest can represent only once.
docs_bundle(
    name = "attach_to_a",
    bundles = [
        {
            "bundle": ":child",
            "mount_at": "same",
            "attach_to": "a/index",
        },
    ],
    source_dir = "_empty",
)

docs_bundle(
    name = "attach_to_b",
    bundles = [
        {
            "bundle": ":child",
            "mount_at": "same",
            "attach_to": "b/index",
        },
    ],
    source_dir = "_empty",
)

# The child reaches the final bundle at two different locations, so analysis
# must stop before Sphinx would receive two copies of the same pages.
docs_bundle(
    name = "bad",
    bundles = [
        {
            "bundle": ":wrapper_x",
            "mount_at": "root",
        },
        {
            "bundle": ":wrapper_y",
            "mount_at": "root",
        },
    ],
    source_dir = "_empty",
    # Tagged manual so `bazel build //...` never expands to it;
    # the test builds it explicitly and asserts the analysis error.
    tags = ["manual"],
)

docs_bundle(
    name = "bad_attach_to",
    bundles = [
        {
            "bundle": ":attach_to_a",
            "mount_at": "root",
        },
        {
            "bundle": ":attach_to_b",
            "mount_at": "root",
        },
    ],
    source_dir = "_empty",
    tags = ["manual"],
)
