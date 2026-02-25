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

load("@aspect_rules_lint//format:defs.bzl", "format_multirun", "format_test")
load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@rules_java//java:java_binary.bzl", "java_binary")
load("@rules_python//python:pip.bzl", "compile_pip_requirements")
load("@score_tooling//:defs.bzl", "dash_license_checker")

# These are only exported because they're passed as files to the //docs.bzl
# macros, and thus must be visible to other packages. They should only be
# referenced by the //docs.bzl macros.

exports_files(
    [
        "requirements.txt",
        "incremental.py",
        "dummy.py",
        "generate_sourcelinks_cli.py",
    ],
    visibility = ["//visibility:public"],
)

filegroup(
    name = "all_sources",
    srcs = glob(
        ["*.py"],
    ) + [
        "//src/extensions/score_draw_uml_funcs:all_sources",
        "//src/extensions/score_header_service:all_sources",
        "//src/extensions/score_layout:all_sources",
        "//src/extensions/score_metamodel:all_sources",
        "//src/extensions/score_source_code_linker:all_sources",
        "//src/extensions/score_sphinx_bundle:all_sources",
        "//src/extensions/score_sync_toml:all_sources",
        "//src/helper_lib:all_sources",
    ],
    visibility = ["//visibility:public"],
)

java_binary(
    name = "plantuml",
    jvm_flags = ["-Djava.awt.headless=true"],
    main_class = "net.sourceforge.plantuml.Run",
    visibility = ["//visibility:public"],
    runtime_deps = [
        "@plantuml//jar",
    ],
)

# This makes it possible for py_venv to depend on plantuml.
# Note: py_venv can only depend on py_library.
# TODO: This can be removed with the next
# upgrade of `aspect_rules_py` since the py_venv rule now supports a data field
py_library(
    name = "plantuml_for_python",
    srcs = ["@score_docs_as_code//src:dummy.py"],
    data = ["@score_docs_as_code//src:plantuml"],
    visibility = ["//visibility:public"],
)

# In order to update the requirements, change the `requirements.in` file and run:
# `bazel run //src:requirements.update`.
# This will update the `requirements.txt` file.
# To upgrade all dependencies to their latest versions, run:
# `bazel run //src:requirements.update -- --upgrade`.
compile_pip_requirements(
    name = "requirements",
    srcs = [
        "requirements.in",
        "@score_tooling//python_basics:requirements.txt",
    ],
    requirements_txt = "requirements.txt",
    tags = [
        "manual",
    ],
)

# Running this executes the `collect_source_files.bzl` aspect.
# Collects all source files from specified targets in 'deps', and makes them available for parsing for the source_code_linker

# Needed for Dash tool to check python dependency licenses.
filegroup(
    name = "requirements_lock",
    srcs = [
        "requirements.txt",
    ],
    visibility = ["//visibility:public"],
)

dash_license_checker(
    src = ":requirements_lock",
    file_type = "requirements",
    visibility = ["//visibility:public"],
)

format_multirun(
    name = "format.fix",
    python = "@aspect_rules_lint//format:ruff",
    starlark = "@buildifier_prebuilt//:buildifier",
    visibility = [
        "//visibility:public",
    ],
    yaml = "@aspect_rules_lint//format:yamlfmt",
)

format_test(
    name = "format.check",
    no_sandbox = True,
    python = "@aspect_rules_lint//format:ruff",
    starlark = "@buildifier_prebuilt//:buildifier",
    tags = ["manual"],
    visibility = [
        "//visibility:public",
    ],
    workspace = "//:MODULE.bazel",
    yaml = "@aspect_rules_lint//format:yamlfmt",
)
