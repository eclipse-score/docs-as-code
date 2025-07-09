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
load("@aspect_rules_py//py:defs.bzl", "py_binary", "py_library")
load("@pip_process//:requirements.bzl", "all_requirements", "requirement")
load("@rules_pkg//pkg:mappings.bzl", "pkg_files")
load("@rules_pkg//pkg:tar.bzl", "pkg_tar")
load("@rules_python//python:pip.bzl", "compile_pip_requirements")
load("@rules_python//sphinxdocs:sphinx.bzl", "sphinx_build_binary")
load("@score_dash_license_checker//:dash.bzl", "dash_license_checker")
load("@score_python_basics//:defs.bzl", "score_virtualenv")

score_virtualenv(
    reqs = [
        "@score_docs_as_code//src:plantuml_for_python",
        "@score_docs_as_code//src/extensions:score_plantuml",
        "@score_docs_as_code//src/find_runfiles:find_runfiles",
        "@score_docs_as_code//src/extensions/score_draw_uml_funcs:score_draw_uml_funcs",
        "@score_docs_as_code//src/extensions/score_header_service:score_header_service",
        "@score_docs_as_code//src/extensions/score_layout:score_layout",
        "@score_docs_as_code//src/extensions/score_metamodel:score_metamodel",
        "@score_docs_as_code//src/extensions/score_source_code_linker:score_source_code_linker",
    ] + all_requirements,
)
# These are only exported because they're passed as files to the //docs.bzl
# macros, and thus must be visible to other packages. They should only be
# referenced by the //docs.bzl macros.

exports_files(
    [
        "requirements.txt",
        "incremental.py",
        "dummy.py",
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

# In order to update the requirements, change the `requirements.txt` file and run:
# `bazel run //docs:requirements`.
# This will update the `requirements_lock.txt` file.
# To upgrade all dependencies to their latest versions, run:
# `bazel run //docs:requirements -- --upgrade`.
compile_pip_requirements(
    name = "requirements",
    srcs = [
        "requirements.in",
        "@score_python_basics//:requirements.txt",
    ],
    requirements_txt = "requirements.txt",
    tags = [
        "manual",
    ],
)

filegroup(
    name = "html",
    srcs = [":docs"],
    output_group = "html",
)

pkg_files(
    name = "html_files",
    srcs = [":html"],
    strip_prefix = "html",
    #renames={"html": ""},
)

pkg_tar(
    name = "github-pages",
    srcs = [":html_files"],
)

# 'source_code_linker' needs all targets to be passed to it.
# This is a convenient gathering of all the 'python internal modules' to avoid writing them individiually
py_library(
    name = "docs_as_code_py_modules",
    srcs = [
        "@score_docs_as_code//src:plantuml_for_python",
        "@score_docs_as_code//src/extensions:score_plantuml",
        "@score_docs_as_code//src/extensions/score_draw_uml_funcs",
        "@score_docs_as_code//src/extensions/score_header_service",
        "@score_docs_as_code//src/extensions/score_layout",
        "@score_docs_as_code//src/extensions/score_metamodel",
        "@score_docs_as_code//src/extensions/score_source_code_linker",
        "@score_docs_as_code//src/find_runfiles",
    ],
    visibility = ["//visibility:public"],
)

filegroup(
    name = "docs_assets",
    srcs = glob([
        "assets/**/*",
    ]),
    visibility = ["//visibility:public"],
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
