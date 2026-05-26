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

"""
Easy streamlined way for S-CORE docs-as-code.
"""

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

load("@aspect_rules_py//py:defs.bzl", "py_binary", "py_venv")
load("@docs_as_code_hub_env//:requirements.bzl", "all_requirements")
load("@rules_python//sphinxdocs:sphinx.bzl", "sphinx_build_binary", "sphinx_docs")

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

def _rewrite_needs_json_to_sourcelinks(labels):
    """Replace '@repo//:needs_json' -> '@repo//:sourcelinks_json' for every item."""
    out = []
    for x in labels:
        s = str(x)
        if s.endswith("//:needs_json"):
            out.append(s.replace("//:needs_json", "//:sourcelinks_json"))
        #Items which do not end up with '//:needs_json' shall not be appended to 'out'.
        #They are treated separately and are not related to source code linking.
    return out

def _merge_sourcelinks(name, sourcelinks, known_good = None):
    """Merge multiple sourcelinks JSON files into a single file.

    Args:
        name: Name for the merged sourcelinks target
        sourcelinks: List of sourcelinks JSON file targets
    """

    extra_srcs = []
    known_good_arg = ""
    if known_good != None:
        extra_srcs = [known_good]
        known_good_arg = "--known_good $(location %s)" % known_good

    merge_sourcelinks_tool = Label("//scripts_bazel:merge_sourcelinks")

    native.genrule(
        name = name,
        srcs = sourcelinks + extra_srcs,
        outs = [name + ".json"],
        cmd = """
        $(location {merge_sourcelinks_tool}) \
            --output $@ \
            {known_good_arg} \
            $(SRCS)
        """.format(known_good_arg = known_good_arg, merge_sourcelinks_tool = merge_sourcelinks_tool),
        tools = [merge_sourcelinks_tool],
    )

def _missing_requirements(deps):
    """Add Python hub dependencies if they are missing."""
    found = []
    missing = []
    def _target_to_packagename(target):
        return str(target).split("/")[-1].split(":")[0]
    all_packages = [_target_to_packagename(pkg) for pkg in all_requirements]
    def _find(pkg):
        for dep in deps:
            dep_pkg = _target_to_packagename(dep)
            if dep_pkg == pkg:
                return True
        return False
    for pkg in all_packages:
        if _find(pkg):
            found.append(pkg)
        else:
            missing.append(pkg)
    if len(missing) == len(all_requirements):
        #print("All docs-as-code dependencies are missing, adding all of them.")
        return all_requirements
    if len(missing) == 0:
        #print("All docs-as-code dependencies are already included, no need to add any.")
        return []
    if len(found) > 0:
        msg = "Some docs-as-code dependencies are in deps: " + ", ".join(found) + \
              "\n   ... but others are missing: " + ", ".join(missing) + \
              "\nInconsistent deps for docs(): either include all dependencies or none of them."
        fail(msg)
    fail("This case should be unreachable?!")

def docs(source_dir = "docs", data = [], deps = [], scan_code = [], known_good = None, metamodel = None):
    """Creates all targets related to documentation.

    By using this function, you'll get any and all updates for documentation targets in one place.

    Args:
      source_dir: The source directory containing documentation files. Defaults to "docs".
      data: Additional data files to include in the documentation build.
      deps: Additional dependencies for the documentation build.
      scan_code: List of code targets to scan for source code links.
      known_good: Optional label to a "known good" JSON file for source links.
      metamodel: Optional label to a metamodel.yaml file. When set, the extension loads this
                 file instead of the default metamodel shipped with score_metamodel.
    """

    call_path = native.package_name()

    if call_path != "":
        fail("docs() must be called from the root package. Current package: " + call_path)

    metamodel_data = []
    metamodel_env = {}
    metamodel_opts = []
    if metamodel != None:
        metamodel_data = [metamodel]
        metamodel_env = {"SCORE_METAMODEL_YAML": "$(location " + str(metamodel) + ")"}
        metamodel_opts = ["--define=score_metamodel_yaml=$(location " + str(metamodel) + ")"]

    module_deps = deps
    deps = deps + _missing_requirements(deps)
    deps = deps + [
        Label("//src:plantuml_for_python"),
        Label("//src/extensions/score_sphinx_bundle:score_sphinx_bundle"),
    ]

    incremental_src = Label("//src:incremental.py")

    sphinx_build_binary(
        name = "sphinx_build",
        visibility = ["//visibility:private"],
        data = data + metamodel_data,
        deps = deps,
    )

    # If the source directory is the root (".") we must omit it, otherwise:
    # > invalid glob pattern './**/*.png': segment '.' not permitted
    if source_dir == ".":
        source_prefix = ""
    else:
        source_prefix = source_dir + "/"

    native.filegroup(
        name = "docs_sources",
        srcs = native.glob([
            source_prefix + "**/*.png",
            source_prefix + "**/*.svg",
            source_prefix + "**/*.md",
            source_prefix + "**/*.rst",
            source_prefix + "**/*.html",
            source_prefix + "**/*.css",
            source_prefix + "**/*.puml",
            source_prefix + "**/*.need",
            source_prefix + "**/*.yaml",
            source_prefix + "**/*.json",
            source_prefix + "**/*.csv",
            source_prefix + "**/*.inc",
        ], allow_empty = True),
        visibility = ["//visibility:public"],
    )

    _sourcelinks_json(name = "sourcelinks_json", srcs = scan_code)

    data_with_docs_sources = _rewrite_needs_json_to_docs_sources(data)
    additional_combo_sourcelinks = _rewrite_needs_json_to_sourcelinks(data)
    _merge_sourcelinks(name = "merged_sourcelinks", sourcelinks = [":sourcelinks_json"] + additional_combo_sourcelinks, known_good = known_good)
    docs_data = data + metamodel_data + [":sourcelinks_json"]
    combo_data = data_with_docs_sources + metamodel_data + [":merged_sourcelinks"]

    docs_env = {
        "SOURCE_DIRECTORY": source_dir,
        "DATA": str(data),
        "SCORE_SOURCELINKS": "$(location :sourcelinks_json)",
    } | metamodel_env
    docs_sources_env = {
        "SOURCE_DIRECTORY": source_dir,
        "DATA": str(data_with_docs_sources),
        "SCORE_SOURCELINKS": "$(location :merged_sourcelinks)",
    } | metamodel_env
    if known_good:
        known_good_str = str(known_good)
        docs_env["KNOWN_GOOD_JSON"] = "$(location " + known_good_str + ")"
        docs_sources_env["KNOWN_GOOD_JSON"] = "$(location " + known_good_str + ")"
        docs_data.append(known_good)
        combo_data.append(known_good)

    docs_env["ACTION"] = "incremental"

    py_binary(
        name = "docs",
        tags = ["cli_help=Build documentation:\nbazel run //:docs"],
        srcs = [incremental_src],
        data = docs_data,
        deps = deps,
        env = docs_env
    )

    docs_sources_env["ACTION"] = "incremental"
    py_binary(
        name = "docs_combo",
        tags = ["cli_help=Build full documentation with all dependencies:\nbazel run //:docs_combo"],
        srcs = [incremental_src],
        data = combo_data,
        deps = deps,
        env = docs_sources_env
    )

    native.alias(
        name = "docs_combo_experimental",
        actual = ":docs_combo",
        deprecation = "Target '//:docs_combo_experimental' is deprecated. Use '//:docs_combo' instead.",
    )

    docs_env["ACTION"] = "linkcheck"
    py_binary(
        name = "docs_link_check",
        tags = ["cli_help=Verify Links inside Documentation:\nbazel run //:link_check\n (Note: this could take a long time)"],
        srcs = [incremental_src],
        data = docs_data,
        deps = deps,
        env = docs_env
    )

    docs_env["ACTION"] = "check"
    py_binary(
        name = "docs_check",
        tags = ["cli_help=Verify documentation:\nbazel run //:docs_check"],
        srcs = [incremental_src],
        data = docs_data,
        deps = deps,
        env = docs_env
    )

    docs_env["ACTION"] = "live_preview"
    py_binary(
        name = "live_preview",
        tags = ["cli_help=Live preview documentation in the browser:\nbazel run //:live_preview"],
        srcs = [incremental_src],
        data = docs_data,
        deps = deps,
        env = docs_env
    )

    docs_sources_env["ACTION"] = "live_preview"
    py_binary(
        name = "live_preview_combo_experimental",
        tags = ["cli_help=Live preview full documentation with all dependencies in the browser:\nbazel run //:live_preview_combo_experimental"],
        srcs = [incremental_src],
        data = combo_data,
        deps = deps,
        env = docs_sources_env
    )

    py_venv(
        name = "ide_support",
        tags = ["cli_help=Create virtual environment (.venv_docs) for documentation support:\nbazel run //:ide_support"],
        venv_name = ".venv_docs",
        deps = deps,
        data = data,
        package_collisions = "warning",
    )

    sphinx_docs(
        name = "needs_json",
        srcs = [":docs_sources"],
        config = ":" + source_prefix + "conf.py",
        extra_opts = [
            "-W",
            "--keep-going",
            "-T",  # show more details in case of errors
            "--jobs",
            "auto",
            "--define=external_needs_source=" + str(data),
            "--define=score_sourcelinks_json=$(location :sourcelinks_json)",
            "--define=score_source_code_linker_plain_links=1",
        ],
        formats = ["needs"],
        sphinx = ":sphinx_build",
        tools = data + [":sourcelinks_json"],
        visibility = ["//visibility:public"],
        # Persistent workers cause stale symlinks after dependency version
        # changes, corrupting the Bazel cache.
        allow_persistent_workers = False,
    )

    native.alias(
        name = "traceability_gate",
        actual = Label("//scripts_bazel:traceability_gate"),
        tags = ["cli_help=Enforce traceability coverage thresholds:\nbazel run //:traceability_gate -- --metrics-json bazel-bin/needs_json/_build/needs/metrics.json"],
    )

def _sourcelinks_json(name, srcs):
    """
    Creates a target that generates a JSON file with source code links.

    See https://eclipse-score.github.io/docs-as-code/main/how-to/source_to_doc_links.html

    Args:
        name: Name of the target
        srcs: Source files to scan for traceability tags
    """
    output_file = name + ".json"

    generate_sourcelinks_tool = Label("//scripts_bazel:generate_sourcelinks")

    native.genrule(
        name = name,
        srcs = srcs,
        outs = [output_file],
        cmd = """
        $(location {generate_sourcelinks_tool}) \
            --output $@ \
            $(SRCS)
        """.format(generate_sourcelinks_tool = generate_sourcelinks_tool),
        tools = [generate_sourcelinks_tool],
        visibility = ["//visibility:public"],
    )
