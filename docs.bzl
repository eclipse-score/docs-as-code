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
load("@score_docs_as_code//src/extensions/score_source_code_linker:collect_source_files.bzl", "parse_source_files_for_needs_links")
load("@score_python_basics//:defs.bzl", "score_virtualenv")

sphinx_requirements = all_requirements + [
    "@score_docs_as_code//src:plantuml_for_python",
    "@score_docs_as_code//src/extensions:score_plantuml",
    "@score_docs_as_code//src/find_runfiles:find_runfiles",
    "@score_docs_as_code//src/extensions/score_draw_uml_funcs:score_draw_uml_funcs",
    "@score_docs_as_code//src/extensions/score_header_service:score_header_service",
    "@score_docs_as_code//src/extensions/score_layout:score_layout",
    "@score_docs_as_code//src/extensions/score_metamodel:score_metamodel",
    "@score_docs_as_code//src/extensions/score_source_code_linker:score_source_code_linker",
]

def docs(source_files_to_scan_for_needs_links = None, source_dir = "docs", conf_dir = "docs", build_dir_for_incremental = "_build", docs_targets = []):
    """
    Creates all targets related to documentation.
    By using this function, you'll get any and all updates for documentation targets in one place.
    Current restrictions:
    * only callable from 'docs/BUILD'
    """

    # Parse source files for needs links
    # This needs to be created to generate a target, otherwise it won't execute as dependency for other macros
    parse_source_files_for_needs_links(
        name = "score_source_code_parser",
        srcs_and_deps = source_files_to_scan_for_needs_links if source_files_to_scan_for_needs_links else [],
    )

    # We are iterating over all provided 'targets' in order to allow for automatic generation of them without
    # needing to modify the underlying 'docs.bzl' file.
    for target in docs_targets:
        suffix = "_" + target["suffix"] if target["suffix"] else ""
        external_needs_deps = target.get("target", [])
        external_needs_def = target.get("external_needs_info", [])

        sphinx_build_binary(
            name = "sphinx_build" + suffix,
            visibility = ["//visibility:public"],
            data = ["@score_docs_as_code//src:docs_assets", "@score_docs_as_code//src:score_extension_files"] + external_needs_deps,
            deps = sphinx_requirements,
        )
        _incremental(
            incremental_name = "incremental" + suffix,
            live_name = "live_preview" + suffix,
            conf_dir = conf_dir,
            source_dir = source_dir,
            build_dir = build_dir_for_incremental,
            external_needs_deps = external_needs_deps,
            external_needs_def = external_needs_def,
        )
        _docs(
            name = "docs" + suffix,
            suffix = suffix,
            format = "html",
            external_needs_deps = external_needs_deps,
            external_needs_def = external_needs_def,
        )
        _docs(
            name = "docs_needs" + suffix,
            suffix = suffix,
            format = "needs",
            external_needs_deps = external_needs_deps,
            external_needs_def = external_needs_def,
        )

    # Virtual python environment for working on the documentation (esbonio).
    # incl. python support when working on conf.py and sphinx extensions.
    # creates :ide_support target for virtualenv
    _ide_support()

    # creates 'needs.json' build target

def _incremental(incremental_name = "incremental", live_name = "live_preview", source_dir = "docs", conf_dir = "docs", build_dir = "_build", extra_dependencies = list(), external_needs_deps = list(), external_needs_def = None):
    """
    A target for building docs incrementally at runtime, incl live preview.
    Args:
        source_code_linker: The source code linker target to be used for linking source code to documentation.
        source_code_links: The output from the source code linker.
        source_dir: Directory containing the source files for documentation.
        conf_dir: Directory containing the Sphinx configuration.
        build_dir: Directory to output the built documentation.
        extra_dependencies: Additional dependencies besides the centrally maintained "sphinx_requirements".
    """

    dependencies = sphinx_requirements + extra_dependencies + ["@rules_python//python/runfiles"]

    py_binary(
        name = incremental_name,
        srcs = ["@score_docs_as_code//src:incremental.py"],
        deps = dependencies,
        # TODO: Figure out if we need all dependencies as data here or not.
        data = [":score_source_code_parser", "@score_docs_as_code//src:plantuml", "@score_docs_as_code//src:docs_assets"] + dependencies + external_needs_deps,
        env = {
            "SOURCE_DIRECTORY": source_dir,
            "CONF_DIRECTORY": conf_dir,
            "BUILD_DIRECTORY": build_dir,
            "EXTERNAL_NEEDS_INFO": json.encode(external_needs_def),
            "ACTION": "incremental",
        },
    )

    py_binary(
        name = live_name,
        srcs = ["@score_docs_as_code//src:incremental.py"],
        deps = dependencies,
        data = ["@score_docs_as_code//src:plantuml", "@score_docs_as_code//src:docs_assets"] + dependencies + external_needs_deps,
        env = {
            "SOURCE_DIRECTORY": source_dir,
            "CONF_DIRECTORY": conf_dir,
            "BUILD_DIRECTORY": build_dir,
            "EXTERNAL_NEEDS_INFO": json.encode(external_needs_def),
            "ACTION": "live_preview",
        },
    )

def _ide_support():
    score_virtualenv(
        name = "ide_support",
        venv_name = ".venv_docs",
        reqs = sphinx_requirements,
    )

def _docs(name = "docs", suffix = "", format = "html", external_needs_deps = list(), external_needs_def = list()):
    ext_needs_arg = "--define=external_needs_source=" + json.encode(external_needs_def)

    # Clean suffix used in all generated target names
    target_suffix = "" if name == "docs" else "_" + name[len("docs"):]

    sphinx_docs(
        name = name,
        srcs = native.glob([
            "**/*.png",
            "**/*.svg",
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
        ], exclude = ["**/tests/*"]),
        config = ":conf.py",
        extra_opts = [
            "-W",
            "--keep-going",
        ] + [ext_needs_arg],
        formats = [
            format,
        ],
        sphinx = ":sphinx_build" + suffix,
        tags = [
            "manual",
        ],
        tools = [
            ":score_source_code_parser",
            "@score_docs_as_code//src:plantuml",
            "@score_docs_as_code//src:docs_assets",
        ] + external_needs_deps,
        visibility = ["//visibility:public"],
    )

    native.filegroup(
        name = "assets" + target_suffix,
        srcs = native.glob(["_assets/**"]),
        visibility = ["//visibility:public"],
    )

    native.filegroup(
        name = "html" + target_suffix,
        srcs = [":" + name],
        visibility = ["//visibility:public"],
    )

    pkg_files(
        name = "html_files" + target_suffix,
        srcs = [":html" + target_suffix],
    )

    pkg_tar(
        name = "github_pages" + target_suffix,
        srcs = [":html_files" + target_suffix],
    )
