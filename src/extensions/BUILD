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

score_virtualenv(
    name = "process_venv",
    reqs = all_requirements,
    venv_name = ".venv_process",
)

py_library(
    name = "score_extensions",
    srcs = glob(
        ["**/*.py"],
        exclude = ["**/tests/**/*"],
    ),
    data = glob([
        "score_layout/assets/**",
        "score_metamodel/*.yaml",  # Needed to remove 'resolving of symlink' in score_metamodel.__init__
    ]),
    imports = ["."],
    visibility = ["//visibility:public"],
    deps = [
        "@rules_python//python/runfiles",
    ],
)

# Dedicated metamodel target only for pytest.
# It's required to define the imports for bazel pytest, so that python/pytest can
# import "from score_metamodel" without issues.
py_library(
    name = "score_metamodel",
    srcs = glob(
        ["score_metamodel/**/*.py"],
        exclude = ["**/tests/**/*"],
    ),
    imports = ["extensions"],
    visibility = ["//visibility:public"],
)

score_py_pytest(
    name = "score_metamodel_test",
    size = "small",
    srcs = glob(["score_metamodel/tests/**/*.py"]),
    visibility = ["//visibility:public"],
    deps = [":score_metamodel"] + all_requirements,
)

# ───────────────────────── Source code linker ────────────────────────
# For more information see documentation at score_source_code_linker/README.md
py_library(
    name = "score_source_code_linker",
    srcs = glob(
        ["score_source_code_linker/**/*.py"],
        exclude = ["score_source_code_linker/tests/*.py"],
    ),
    imports = ["."],
    visibility = ["//visibility:public"],
)

score_py_pytest(
    name = "score_source_code_linker_test",
    size = "small",
    srcs = glob(["score_source_code_linker/tests/**/*.py"]),
    deps = [
        ":score_source_code_linker",
    ] + all_requirements,
)

# Needed to make the file parser executeable and findable for the source_code_linker aspect
py_binary(
    name = "parsed_source_files_for_source_code_linker",
    srcs = ["score_source_code_linker/parse_source_files.py"],
    visibility = ["//visibility:public"],
)
