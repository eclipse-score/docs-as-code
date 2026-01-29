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
load("@score_tooling//:defs.bzl", "score_py_pytest")

filegroup(
    name = "sources",
    srcs = glob(
        ["*.py"],
    ),
)

filegroup(
    name = "tests",
    srcs = glob(
        [
            "tests/*.py",
            "tests/*.json",
        ],
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
    name = "score_source_code_linker",
    srcs = [":sources"],
    imports = ["."],
    visibility = ["//visibility:public"],
    deps = ["@score_docs_as_code//src/helper_lib"],
)

py_library(
    name = "source_code_linker_helpers",
    srcs = [
        "needlinks.py",
        "testlink.py",
        "xml_parser.py",
    ],
    imports = ["."],
    visibility = ["//visibility:public"],
)

score_py_pytest(
    name = "score_source_code_linker_test",
    size = "small",
    srcs = glob([
        "tests/*.py",
    ]),
    args = [
        "-s",
        "-vv",
    ],
    data = glob(["tests/*.json"]),
    imports = ["."],
    deps = [
        ":score_source_code_linker",
        "//src/extensions/score_metamodel",
    ],
)
