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

load("@score_cr_checker//:cr_checker.bzl", "copyright_checker")
load("@score_cli_helper//:cli_helper.bzl", "cli_helper")

package(default_visibility = ["//visibility:public"])

copyright_checker(
    name = "copyright",
    srcs = [
        "examples",
        "src",
        "//:BUILD",
        "//:MODULE.bazel",
    ],
    config = "@score_cr_checker//resources:config",
    template = "@score_cr_checker//resources:templates",
    visibility = ["//visibility:public"],
)

exports_files([
    "MODULE.bazel",
    "BUILD",
])

cli_helper(
    name = "cli-help",
    visibility = ["//visibility:public"],
)
