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

filegroup(
    name = "all_sources",
    srcs = ["__init__.py"],
    visibility = ["//visibility:public"],
)

py_library(
    name = "score_sphinx_bundle",
    srcs = [":all_sources"],
    visibility = ["//visibility:public"],
    deps = all_requirements + [
        "@score_docs_as_code//src/extensions:score_plantuml",
        "@score_docs_as_code//src/extensions/score_draw_uml_funcs",
        "@score_docs_as_code//src/extensions/score_header_service",
        "@score_docs_as_code//src/extensions/score_layout",
        "@score_docs_as_code//src/extensions/score_metamodel",
        "@score_docs_as_code//src/extensions/score_source_code_linker",
        "@score_docs_as_code//src/extensions/score_sync_toml",
        "@score_docs_as_code//src/helper_lib",
    ],
)
