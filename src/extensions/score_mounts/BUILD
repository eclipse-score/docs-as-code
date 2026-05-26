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

load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@docs_as_code_hub_env//:requirements.bzl", "requirement")
load("//:score_pytest.bzl", "score_pytest")

filegroup(
    name = "sources",
    srcs = glob(["*.py"]),
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
    name = "score_mounts",
    srcs = [":sources"],
    imports = ["."],
    visibility = ["//visibility:public"],
    deps = [
        requirement("sphinx"),
        requirement("sphinx-mounts"),
        requirement("tomli-w"),
        "//src/helper_lib",
    ],
)

score_pytest(
    name = "score_mounts_tests",
    size = "small",
    srcs = glob(["tests/*.py"]),
    deps = [":score_mounts"],
    pytest_config = "//:pyproject.toml",
)
