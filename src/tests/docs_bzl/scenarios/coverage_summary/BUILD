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

filegroup(name = "files", srcs = ["a.cc"])

# Each primary Need is declared in its bundle's own documentation. Selecting
# an external code target retains those implementation files' repository.
docs_bundle(
    name = "component",
    srcs = ["component/index.rst"],
    code_targets = [":files", "@bazel_tools//tools/cpp/runfiles:runfiles"],
    primary_need_id = "comp__files",
)

docs_bundle(name = "empty", srcs = ["empty/index.rst"], primary_need_id = "mod__empty")
docs_bundle(name = "unidentified", code_targets = [":files"])

# Propagate the component through an intermediate source-less aggregator.
docs_bundle(name = "left", bundles = [{"bundle": ":component", "mount_at": "code"}])

docs_bundle(
    name = "aggregate",
    bundles = [
        {"bundle": ":left", "mount_at": "first"},
        {"bundle": ":empty", "mount_at": "empty"},
        {"bundle": ":unidentified", "mount_at": "unidentified"},
    ],
)

# Two different bundles must not silently overwrite ownership for the same ID.
docs_bundle(name = "conflicting", srcs = ["conflicting/index.rst"], primary_need_id = "comp__files")
docs_bundle(
    name = "conflict",
    bundles = [
        {"bundle": ":component", "mount_at": "first"},
        {"bundle": ":conflicting", "mount_at": "second"},
    ],
)
