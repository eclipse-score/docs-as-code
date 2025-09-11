# *******************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
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

load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@score_tooling//:defs.bzl", "cli_helper", "copyright_checker")
load("//:docs.bzl", "docs")

package(default_visibility = ["//visibility:public"])

copyright_checker(
    name = "copyright",
    srcs = [
        "src",
        "//:BUILD",
        "//:MODULE.bazel",
    ],
    config = "@score_tooling//cr_checker/resources:config",
    template = "@score_tooling//cr_checker/resources:templates",
    visibility = ["//visibility:public"],
)

docs(
    data = [
        "@score_process//:needs_json",
    ],
    source_dir = "docs",
)

cli_helper(
    name = "cli-help",
    visibility = ["//visibility:public"],
)
