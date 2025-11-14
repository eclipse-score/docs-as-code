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
load("@rules_pkg//pkg:mappings.bzl", "pkg_files", "strip_prefix")
load("@rules_pkg//pkg:tar.bzl", "pkg_tar")
load("@rules_python//sphinxdocs:sphinx.bzl", "sphinx_build_binary", "sphinx_docs")
load("@rules_python//sphinxdocs:sphinx_docs_library.bzl", "sphinx_docs_library")
load("@score_tooling//:defs.bzl", "score_virtualenv")

def _rewrite_needs_json_to_docs_sources(labels):
    """Replace '@repo//:needs_json' -> '@repo//:docs_sources' for every item."""
    out = []
    for x in labels:
        s = str(x)
        if s.endswith("//:needs_json"):
            out.append(s.replace("//:needs_json", "//:docs_sources"))
        else:
            out.append(s)
    return out

def docs(source_dir = "docs", data = [], deps = []):
    """
    Creates all targets related to documentation.
    By using this function, you'll get any and all updates for documentation targets in one place.
    """

    call_path = native.package_name()

    if call_path != "":
        fail("docs() must be called from the root package. Current package: " + call_path)

    deps = deps + all_requirements + [
        "@score_docs_as_code//src:plantuml_for_python",
        "@score_docs_as_code//src/extensions/score_sphinx_bundle:score_sphinx_bundle",
    ]

    sphinx_build_binary(
        name = "sphinx_build",
        visibility = ["//visibility:private"],
        data = data,
        deps = deps,
    )

    pkg_files(
        name = "docs_sources",
        srcs = native.glob([
            source_dir + "/**/*.png",
            source_dir + "/**/*.svg",
            source_dir + "/**/*.md",
            source_dir + "/**/*.rst",
            source_dir + "/**/*.html",
            source_dir + "/**/*.css",
            source_dir + "/**/*.puml",
            source_dir + "/**/*.need",
            source_dir + "/**/*.yaml",
            source_dir + "/**/*.json",
            source_dir + "/**/*.csv",
            source_dir + "/**/*.inc",
            "more_docs/**/*.rst",
        ], allow_empty = True),
        strip_prefix = strip_prefix.from_pkg(),  # avoid flattening of folders
        visibility = ["//visibility:public"],
    )

    data_with_docs_sources = _rewrite_needs_json_to_docs_sources(data)

    py_binary(
        name = "docs",
        tags = ["cli_help=Build documentation:\nbazel run //:docs"],
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
        name = "docs_combo_experimental",
        tags = ["cli_help=Build full documentation with all dependencies:\nbazel run //:docs_combo_experimental"],
        srcs = ["@score_docs_as_code//src:incremental.py"],
        data = data_with_docs_sources,
        deps = deps,
        env = {
            "SOURCE_DIRECTORY": source_dir,
            "DATA": str(data_with_docs_sources),
            "ACTION": "incremental",
        },
    )

    py_binary(
        name = "docs_check",
        tags = ["cli_help=Verify documentation:\nbazel run //:docs_check"],
        srcs = ["@score_docs_as_code//src:incremental.py"],
        data = data,
        deps = deps,
        env = {
            "SOURCE_DIRECTORY": source_dir,
            "DATA": str(data),
            "ACTION": "check",
        },
    )

    py_binary(
        name = "live_preview",
        tags = ["cli_help=Live preview documentation in the browser:\nbazel run //:live_preview"],
        srcs = ["@score_docs_as_code//src:incremental.py"],
        data = data,
        deps = deps,
        env = {
            "SOURCE_DIRECTORY": source_dir,
            "DATA": str(data),
            "ACTION": "live_preview",
        },
    )

    py_binary(
        name = "live_preview_combo_experimental",
        tags = ["cli_help=Live preview full documentation with all dependencies in the browser:\nbazel run //:live_preview_combo_experimental"],
        srcs = ["@score_docs_as_code//src:incremental.py"],
        data = data_with_docs_sources,
        deps = deps,
        env = {
            "SOURCE_DIRECTORY": source_dir,
            "DATA": str(data_with_docs_sources),
            "ACTION": "live_preview",
        },
    )

    score_virtualenv(
        name = "ide_support",
        tags = ["cli_help=Create virtual environment (.venv_docs) for documentation support:\nbazel run //:ide_support"],
        venv_name = ".venv_docs",
        reqs = deps,
        # Add dependencies to ide_support, so esbonio has access to them.
        data = data,
    )

    # Create sphinx_docs targets for different output formats
    formats = {"needs_json": "needs", "html": "html"}
    for target_name, format_type in formats.items():
        sphinx_docs(
            name = target_name,
            srcs = [":docs_sources"],
            config = ":" + source_dir + "/conf.py",
            extra_opts = [
                "-W",
                "--keep-going",
                "-T",  # show more details in case of errors
                "--jobs",
                "auto",
                "--define=external_needs_source=" + str(data),
            ],
            formats = [format_type],
            sphinx = ":sphinx_build",
            tools = data,
            visibility = ["//visibility:public"],
        )
