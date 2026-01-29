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
load("@pip_process//:requirements.bzl", "all_requirements")
load("@score_tooling//:defs.bzl", "score_py_pytest")

filegroup(
    name = "sources",
    srcs = glob(
        [
            "*.py",
            "*.yaml",
            "*.json",
            "checks/*.py",
        ],
    ),
)

filegroup(
    name = "tests",
    srcs = glob(
        ["tests/*.py"],
    ),
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
    name = "score_metamodel",
    srcs = [":sources"],
    imports = ["."],
    visibility = ["//visibility:public"],
    # TODO: Figure out if all requirements are needed or if we can break it down a bit
    deps = all_requirements + ["@score_docs_as_code//src/helper_lib"],
)

score_py_pytest(
    name = "score_metamodel_tests",
    size = "small",
    srcs = glob(["tests/*.py"]),
    # All requirements already in the library so no need to have it double
    data = glob(
        [
            "tests/**/*.rst",
            "tests/**/*.yaml",
        ],
    ) + ["tests/rst/conf.py"],
    deps = [":score_metamodel"],
)
