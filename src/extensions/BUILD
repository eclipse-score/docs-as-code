# *******************************************************************************
# Copyright (c) 2024 Contributors to the Eclipse Foundation
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

load("@aspect_rules_py//py:defs.bzl", "py_binary", "py_library")
load("@pip_process//:requirements.bzl", "all_requirements")
load("@score_python_basics//:defs.bzl", "score_py_pytest", "score_virtualenv")

# TODO: This probably can be deleted
score_virtualenv(
    name = "process_venv",
    reqs = all_requirements,
    venv_name = ".venv_process",
)

# convenient target that gathers all targets
py_library(
    name = "score_extensions",
    visibility = ["//visibility:public"],
    deps = [
        "//src/extensions/score_draw_uml_funcs:score_draw_uml_funcs",
        "//src/extensions/score_header_service:score_header_service",
        "//src/extensions/score_layout:score_layout",
        "//src/extensions/score_metamodel:score_metamodel",
        "//src/extensions/score_source_code_linker:score_source_code_linker",
        "@rules_python//python/runfiles",
    ],
)

