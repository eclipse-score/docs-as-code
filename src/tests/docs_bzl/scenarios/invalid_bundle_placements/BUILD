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
    source_dir = "child",
    entry_doc = "a",
)

docs_bundle(
    name = "wrapper_x",
    source_dir = "_empty",
    bundles = [
        {"bundle": ":child", "mount_at": "x"},
    ],
)

docs_bundle(
    name = "wrapper_y",
    source_dir = "_empty",
    bundles = [
        {"bundle": ":child", "mount_at": "y"},
    ],
)

# These wrappers have the same final document location, but disagree about
# metadata that the manifest can represent only once.
docs_bundle(
    name = "attach_to_a",
    source_dir = "_empty",
    bundles = [
        {"bundle": ":child", "mount_at": "same", "attach_to": "a/index"},
    ],
)

docs_bundle(
    name = "attach_to_b",
    source_dir = "_empty",
    bundles = [
        {"bundle": ":child", "mount_at": "same", "attach_to": "b/index"},
    ],
)

# The child reaches the final bundle at two different locations, so analysis
# must stop before Sphinx would receive two copies of the same pages.
docs_bundle(
    name = "bad",
    source_dir = "_empty",
    bundles = [
        {"bundle": ":wrapper_x", "mount_at": "root"},
        {"bundle": ":wrapper_y", "mount_at": "root"},
    ],
    # Tagged manual so `bazel build //...` never expands to it;
    # the test builds it explicitly and asserts the analysis error.
    tags = ["manual"],
)

docs_bundle(
    name = "bad_attach_to",
    source_dir = "_empty",
    bundles = [
        {"bundle": ":attach_to_a", "mount_at": "root"},
        {"bundle": ":attach_to_b", "mount_at": "root"},
    ],
    tags = ["manual"],
)

# Upward hierarchy edges are ordinary Bazel dependencies and must remain
# acyclic. This target is intentionally invalid and is built only by the
# corresponding negative test.
docs_bundle(
    name = "cycle_a",
    upward_bundles = [":cycle_b"],
    tags = ["manual"],
)

docs_bundle(
    name = "cycle_b",
    upward_bundles = [":cycle_a"],
    tags = ["manual"],
)
