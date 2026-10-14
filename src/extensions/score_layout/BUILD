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
load("@docs_as_code_hub_env//:requirements.bzl", "requirement")
load("@score_tools//score_pytest:pytest.bzl", "score_pytest")

filegroup(
    name = "sources",
    srcs = glob([
        "*.py",
        "assets/**/*",
    ]),
)

filegroup(
    name = "tests",
    srcs = glob(["tests/*.py"]),
)

filegroup(
    name = "all_sources",
    srcs = [
        ":sources",
        ":tests",
    ],
    visibility = ["//visibility:public"],
)

py_library(
    name = "score_layout",
    srcs = [":sources"],
    # Adding assets as src instead of data ensures they are included in the
    # library as they would normally be, and we do not need to go through bazel's
    # RUNFILES_DIR mechanism to access them. This makes the code much simpler.
    # And it makes the library far easier extractable from bazel into a normal
    # python package if we ever want to do that.
    imports = ["."],
    visibility = ["//visibility:public"],
    deps = [
        requirement("sphinx"),
        "//src/helper_lib",
    ],
)

score_pytest(
    name = "score_layout_tests",
    size = "small",
    srcs = glob(["tests/*.py"]),
    pytest_config = "//:pyproject.toml",
    deps = [":score_layout"],
)
