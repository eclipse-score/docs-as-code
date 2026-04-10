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
load("@score_tooling//python_basics/score_pytest:py_pytest.bzl", "score_py_pytest")

exports_files([
    "pytest.ini",
    "main.py",
    "py_pytest.bzl",
])

score_py_pytest(
    name = "test_rules_are_working_correctly",
    srcs = glob(
        [
            "tests/*.py",
        ],
        allow_empty = True,
    ),
)

py_library(
    name = "attribute_plugin",
    srcs = ["attribute_plugin.py"],
    imports = ["."],
    visibility = ["//visibility:public"],
)
