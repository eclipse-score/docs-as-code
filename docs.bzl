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

# Multiple approaches are available to build the same documentation output:
#
# 1. **Esbonio via IDE support (`ide_support` target)**:
#    - Listed first as it offers the least flexibility in implementation.
#    - Designed for live previews and quick iterations when editing documentation.
#    - Integrates with IDEs like VS Code but requires the Esbonio extension.
#    - Requires a virtual environment with consistent dependencies (see 2).
#
# 2. **Directly running Sphinx in the virtual environment**:
#    - As mentioned above, a virtual environment is required for running esbonio.
#    - Therefore, the same environment can be used to run Sphinx directly.
#    - Option 1: Run Sphinx manually via `.venv_docs/bin/python -m sphinx docs _build --jobs auto`.
#    - Option 2: Use the `incremental` target, which simplifies this process.
#    - Usable in CI pipelines to validate the virtual environment used by Esbonio.
#    - Ideal for quickly generating documentation during development.
#
# 3. **Bazel-based build (`docs` target)**:
#    - Runs the documentation build in a Bazel sandbox, ensuring clean, isolated builds.
#    - Less convenient for frequent local edits but ensures build reproducibility.
#
# **Consistency**:
# When modifying Sphinx extensions or configuration, ensure all three methods
# (Esbonio, incremental, and Bazel) work as expected to avoid discrepancies.
#
# For user-facing documentation, refer to `/README.md`.

load("@aspect_rules_py//py:defs.bzl", "py_binary", "py_library")
load("@pip_process//:requirements.bzl", "all_requirements", "requirement")
load("@rules_java//java:java_binary.bzl", "java_binary")
load("@rules_pkg//pkg:mappings.bzl", "pkg_files")
load("@rules_pkg//pkg:tar.bzl", "pkg_tar")
load("@rules_python//sphinxdocs:sphinx.bzl", "sphinx_build_binary", "sphinx_docs")
load("@rules_python//sphinxdocs:sphinx_docs_library.bzl", "sphinx_docs_library")
load("@score_python_basics//:defs.bzl", "score_virtualenv")

def docs(source_dir = "docs", data = [], deps = []):
    """
    Creates all targets related to documentation.
    By using this function, you'll get any and all updates for documentation targets in one place.
    """

    data = data + ["@score_docs_as_code//src:docs_assets"]

    deps = deps + all_requirements + [
        "@score_docs_as_code//src:plantuml_for_python",
        "@score_docs_as_code//src/extensions:score_plantuml",
        "@score_docs_as_code//src/find_runfiles:find_runfiles",
        "@score_docs_as_code//src/extensions/score_draw_uml_funcs:score_draw_uml_funcs",
        "@score_docs_as_code//src/extensions/score_header_service:score_header_service",
        "@score_docs_as_code//src/extensions/score_layout:score_layout",
        "@score_docs_as_code//src/extensions/score_metamodel:score_metamodel",
        "@score_docs_as_code//src/extensions/score_source_code_linker:score_source_code_linker",
    ]

    sphinx_build_binary(
        name = "sphinx_build",
        visibility = ["//visibility:private"],
        data = data,
        deps = deps,
    )

    py_binary(
        name = "docs",
        tags = ["cli_help=Build documentation [run]"],
        srcs = ["@score_docs_as_code//src:incremental.py"],
        data = data,
        deps = deps,
        env = {
            "SOURCE_DIRECTORY": source_dir,
            "DATA": str(data),
            "ACTION": "incremental",
        },
    )

    py_binary(
        name = "live_preview",
        tags = ["cli_help=Live preview documentation in the browser [run]"],
        srcs = ["@score_docs_as_code//src:incremental.py"],
        data = data,
        deps = deps,
        env = {
            "SOURCE_DIRECTORY": source_dir,
            "DATA": str(data),
            "ACTION": "live_preview",
        },
    )

    score_virtualenv(
        name = "ide_support",
        tags = ["cli_help=Create virtual environment (.venv_docs) for documentation support [run]"],
        venv_name = ".venv_docs",
        reqs = deps,
        # Add dependencies to ide_support, so esbonio has access to them.
        data = data,
    )

    # creates 'needs.json' build target
    sphinx_docs(
        name = "needs_json",
        srcs = native.glob([
            # TODO: we do not need images etc to generate the json file.
            "**/*.png",
            "**/*.svg",
            "**/*.md",
            "**/*.rst",
            "**/*.html",
            "**/*.css",
            "**/*.puml",
            "**/*.need",
            # Include the docs src itself
            # Note: we don't use py_library here to make it as close as possible to docs:incremental.
            "**/*.yaml",
            "**/*.json",
            "**/*.csv",
            "**/*.inc",
        ], exclude = ["**/tests/*"], allow_empty = True),
        config = ":" + source_dir + "/conf.py",
        extra_opts = [
            "-W",
            "--keep-going",
            "-T",  # show more details in case of errors
            "--jobs",
            "auto",
            "--define=external_needs_source=" + str(data),
        ],
        formats = ["needs"],
        sphinx = ":sphinx_build",
        tools = data,
        visibility = ["//visibility:public"],
    )
