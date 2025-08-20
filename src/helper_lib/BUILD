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

py_library(
    name = "helper_lib",
    srcs = [
        "__init__.py",
        "additional_functions.py",
    ],
    imports = ["."],
    visibility = ["//visibility:public"],
    deps = ["@score_docs_as_code//src/extensions/score_source_code_linker:source_code_linker_helpers"],
)

score_py_pytest(
    name = "helper_lib_tests",
    size = "small",
    srcs = ["test_helper_lib.py"],
    deps = [
        ":helper_lib",
    ] + all_requirements,
)
