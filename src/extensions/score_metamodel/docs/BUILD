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

load("//:docs.bzl", "docs_bundle")
load("@aspect_rules_py//py:defs.bzl", "py_binary")
load("@docs_as_code_hub_env//:requirements.bzl", "all_requirements")

genrule(
    name = "generate_metamodel_rst",
    srcs = [
        "//src/extensions/score_metamodel:metamodel_yaml",
    ],
    outs = [
        "generated/index.rst",
        "generated/metamodel_classes.mmd",
    ],
    cmd = "$(location :generate_metamodel_rst_bin) --rst-output $(location generated/index.rst) --mmd-output $(location generated/metamodel_classes.mmd) $(location //src/extensions/score_metamodel:metamodel_yaml)",
    tools = [":generate_metamodel_rst_bin"],
    visibility = ["//visibility:private"],
)

py_binary(
    name = "generate_metamodel_rst_bin",
    srcs = ["generate_metamodel_rst.py"],
    main = "generate_metamodel_rst.py",
    deps = all_requirements,
    visibility = ["//visibility:public"], # public to be reuseable for other metamodels
)

docs_bundle(
    name = "metamodel",
    # The generated RST and Mermaid outputs form one explicit source tree.
    srcs = [":generate_metamodel_rst"],
    entry_doc = "index",
    visibility = ["//visibility:public"],
)
