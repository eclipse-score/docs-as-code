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
load("@docs_as_code_hub_env//:requirements.bzl", "all_requirements")
load("//:score_pytest.bzl", "score_pytest")

filegroup(
    name = "all_sources",
    srcs = glob(["*.py"]),
    visibility = ["//visibility:public"],
)

py_library(
    name = "helper_lib",
    srcs = [":all_sources"],
    imports = ["."],
    visibility = ["//visibility:public"],
    deps = [
        "@rules_python//python/runfiles",
    ] + all_requirements,
)

score_pytest(
    name = "helper_lib_tests",
    size = "small",
    srcs = ["test_helper_lib.py"],
    deps = [
        ":helper_lib",
    ] + all_requirements,
    pytest_config = "//:pyproject.toml",
)
