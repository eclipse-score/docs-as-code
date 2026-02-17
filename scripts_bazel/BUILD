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

load("@aspect_rules_py//py:defs.bzl", "py_binary")
load("@docs_as_code_hub_env//:requirements.bzl", "all_requirements")

filegroup(
    name = "sources",
    srcs = glob(["**/*.py"]),
    visibility = ["//visibility:public"],
)

py_binary(
    name = "generate_sourcelinks",
    srcs = ["generate_sourcelinks_cli.py"],
    main = "generate_sourcelinks_cli.py",
    visibility = ["//visibility:public"],
    deps = [
        "//src/extensions/score_source_code_linker",
    ] + all_requirements,
)

py_binary(
    name = "merge_sourcelinks",
    srcs = ["merge_sourcelinks.py"],
    main = "merge_sourcelinks.py",
    visibility = ["//visibility:public"],
)
