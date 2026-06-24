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
    deps= [ "//src/extensions/score_source_code_linker"],
    main = "merge_sourcelinks.py",
    visibility = ["//visibility:public"],
)

py_binary(
    name = "traceability_gate",
    srcs = ["traceability_gate.py"],
    main = "traceability_gate.py",
    visibility = ["//visibility:public"],
    deps = [],
)

py_binary(
    name = "filter_needs_json",
    srcs = ["filter_needs_json.py"],
    main = "filter_needs_json.py",
    visibility = ["//visibility:public"],
    deps = [],
)

py_binary(
    name = "sphinx_needs_to_md",
    srcs = ["sphinx_needs_to_md.py"],
    main = "sphinx_needs_to_md.py",
    visibility = ["//visibility:public"],
    deps = [],
)

py_binary(
    name = "sphinx_needs_to_trlc",
    srcs = ["sphinx_needs_to_trlc.py"],
    main = "sphinx_needs_to_trlc.py",
    visibility = ["//visibility:public"],
    deps = [],
)
