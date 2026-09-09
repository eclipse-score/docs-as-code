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

load("@docs_as_code_hub_env//:requirements.bzl", "all_requirements")
load("//:score_pytest.bzl", "score_pytest")

# docs.bzl passes this entry script as the source of each interactive binary.
# Exporting it allows docs() to declare those binaries in consumer packages.
exports_files(
    ["cli.py"],
    visibility = ["//visibility:public"],
)

# The parent source collection must cross this Bazel package boundary
# explicitly so source-code linking continues to include the CLI and tests.
filegroup(
    name = "all_sources",
    srcs = glob(["*.py"]),
    visibility = ["//visibility:public"],
)

score_pytest(
    name = "dirty_build_test",
    srcs = ["dirty_build_test.py", "cli.py"],
    deps = all_requirements + [
        "//src/extensions/score_mounts",
        "//src/helper_lib",
    ],
    pytest_config = "//:pyproject.toml",
)

# Exercise dispatch and the docs.bzl environment contract with the same
# entry script used by the interactive binaries. Its cli.py name also keeps
# it distinct from score_pytest's own main.py entry in the test sources.
score_pytest(
    name = "main_test",
    srcs = ["main_test.py", "cli.py"],
    deps = all_requirements + [
        "//src/extensions/score_mounts",
        "//src/helper_lib",
    ],
    pytest_config = "//:pyproject.toml",
)
