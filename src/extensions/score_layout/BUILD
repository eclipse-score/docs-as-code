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
load("@pip_process//:requirements.bzl", "requirement")

filegroup(
    name = "all_sources",
    srcs = glob([
        "*.py",
        "assets/**/*",
    ]),
    visibility = ["//visibility:public"],
)

py_library(
    name = "score_layout",
    srcs = [":all_sources"],
    # Adding assets as src instead of data ensures they are included in the
    # library as they would normally be, and we do not need to go through bazel's
    # RUNFILES_DIR mechanism to access them. This makes the code much simpler.
    # And it makes the library far easier extractable from bazel into a normal
    # python package if we ever want to do that.
    imports = ["."],
    visibility = ["//visibility:public"],
    deps = [requirement("sphinx")],
)
