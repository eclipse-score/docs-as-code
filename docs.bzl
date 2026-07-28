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
load("@sphinxdocs//sphinxdocs:sphinx.bzl", "sphinx_build_binary", "sphinx_docs")
load(
    "@score_docs_as_code//:bzl/basics.bzl",
    "glob_doc_sources",
    "join_path",
)
load(
    "@score_docs_as_code//:bzl/bundle_rules.bzl",
    "create_bundle",
    "merge_bundle_sourcelinks",
)
load(
    "@score_docs_as_code//:bzl/mount_rules.bzl",
    "create_mounts_manifest",
)

def docs_bundle(name, source_dir = None, bundles = [], scan_code = [], visibility = None, **kwargs):
    """A docs bundle, optionally composed of others.

    Args:
      name: target name.
      source_dir: optional directory holding this bundle's own doc sources. It is
        globbed like `docs()` (same file kinds) and the contents are stored after
        stripping the `source_dir` prefix. Leave it unset for a pure aggregator.
      bundles: nested bundles to compose, each a dict
        {
            "bundle": <docs_bundle label>,
            "mount_at": <where it shall me mounted>,
            "attach_to": <optional index where the bundle shall be attached, defaults to the mount_at parent's index>
        }.
      scan_code: Source-code targets to scan for source-code links owned by this
                 bundle.
      visibility: Target visibility.
      **kwargs: Additional attributes forwarded to the underlying rule.
    """

    srcs = glob_doc_sources(source_dir) if source_dir != None else []
    sourcelinks = []
    if scan_code:
        sourcelinks_name = name + "_sourcelinks_json"
        _sourcelinks_json(name = sourcelinks_name, srcs = scan_code)
        sourcelinks = [":" + sourcelinks_name]

    # Store the source directory relative to the workspace so bundle consumers
    # can locate the original files without copying them.
    pkg = native.package_name()
    strip_prefix = join_path(pkg, source_dir) if source_dir != None else ""

    # The helper validates child declarations and creates the internal target.
    create_bundle(
        name = name,
        srcs = srcs,
        sourcelinks = sourcelinks,
        strip_prefix = strip_prefix,
        bundles = bundles,
        visibility = visibility,
        **kwargs
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

def docs(
        source_dir = "docs",
        data = [],
        deps = [],
        scan_code = [],
        test_sources = [],
        known_good = None,
        metamodel = None,
        bundles = [],
    ):
    """Creates all targets related to documentation.

    By using this function, you'll get any and all updates for documentation targets in one place.

    Args:
      source_dir: The source directory containing documentation files. Defaults to "docs".
      data: Additional data files to include in the documentation build.
      deps: Additional dependencies for the documentation build.
      scan_code: List of code targets to scan for source code links.
      test_sources: Optional list of repo-relative directory paths which will be used to filter testcases for documentation generation.
                    When empty (default), all testcases found in `bazel-testlogs` will be used.
      known_good: Optional label to a "known good" JSON file for source links.
      metamodel: Optional label to a metamodel.yaml file. When set, the extension loads this
                 file instead of the default metamodel shipped with score_metamodel.
      bundles: List of placement dicts describing documentation bundles to overlay
              into this documentation's source tree. Each entry is a dict
                {
                    "bundle": <docs_bundle label>,
                    "mount_at": <where it shall me mounted>,
                    "attach_to": <optional, file where the bundle shall be attached, defaults to the parent section's index>,
                    "entry_doc": <optional, docname of the bundle's own index, defaults to 'index'>,
                }.
              Note: a bundle label may also point at another module's auto-exposed
              bundle, e.g. "@score_process//:docs_bundle".
    """

    source_config = ":" + ("" if source_dir == "." else source_dir + "/") + "conf.py"

    # Convention in this macro: an optional Bazel label is named ``*_label``
    # but represented as a 0/1 list. This lets it be appended directly to
    # list-valued attributes such as ``data`` and ``tools``.
    metamodel_label = [metamodel] if metamodel else []

    mounts_manifest_label = []
    if bundles:
        create_mounts_manifest(
            name = "_mounts_manifest",
            bundle = create_bundle(
                name = "_docs_mounts",
                bundles = bundles,
                visibility = ["//visibility:private"],
            ),
        )
        mounts_manifest_label = [":_mounts_manifest"]
    deps = deps + _missing_requirements(deps)
    deps = deps + [
        Label("//src:plantuml_for_python"),
        Label("//src/extensions/score_sphinx_bundle:score_sphinx_bundle"),
    ]

    incremental_src = Label("//src:incremental.py")

    sphinx_build_binary(
        name = "sphinx_build",
        visibility = ["//visibility:private"],
        data = data + metamodel_label + [":docs_bundle"],
        deps = deps,
    )

    known_good_label = [known_good] if known_good else []
    # The public bundle carries both the complete source tree and the
    # transitive source-code links of every nested bundle.
    docs_bundle(
        name = "docs_bundle",
        source_dir = source_dir,
        bundles = bundles,
        scan_code = scan_code,
        visibility = ["//visibility:public"],
    )
    merge_bundle_sourcelinks(
        name = "sourcelinks_json",
        bundle = ":docs_bundle",
        known_good = known_good,
    )

    docs_data = data + metamodel_label + [":sourcelinks_json", ":docs_bundle"] + mounts_manifest_label

    docs_env = {
        "SOURCE_DIRECTORY": source_dir,
        "PACKAGE_DIR": native.package_name(),
        "TEST_SOURCES": str(test_sources),
        "DATA": str(data),
        # `bazel run` starts from a runfiles tree, so this logical path is
        # resolved by score_mounts through ``RUNFILES_DIR``.
        "MOUNTS_MANIFEST": "$(rlocationpath :_mounts_manifest)" if bundles else "",
        "SCORE_SOURCELINKS": "$(location :sourcelinks_json)",
    }
    if metamodel:
        # The interactive ``py_binary`` targets run from a runfiles tree.
        # incremental.py resolves this logical path through ``RUNFILES_DIR``.
        docs_env["SCORE_METAMODEL_YAML"] = "$(rlocationpath " + str(metamodel) + ")"
    if known_good_label:
        known_good_str = str(known_good_label[0])
        docs_env["KNOWN_GOOD_JSON"] = "$(location " + known_good_str + ")"
        docs_data += known_good_label

    docs_env["ACTION"] = "incremental"

    py_binary(
        name = "docs",
        tags = ["cli_help=Build documentation:\nbazel run //:docs"],
        srcs = [incremental_src],
        data = docs_data,
        deps = deps,
        env = docs_env
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
        srcs = [":docs_bundle"],
        config = source_config,
        extra_opts = [
            "-W",
            "--keep-going",
            "-T",  # show more details in case of errors
            "--jobs",
            "auto",
            "--define=external_needs_source=" + str(data),
            # ``sphinx_docs`` is a sandboxed build action, so it needs the
            # action-input path rather than the runfiles-relative spelling.
            "--define=mounts_manifest=" + ("$(location :_mounts_manifest)" if bundles else ""),
            "--define=score_sourcelinks_json=$(location :sourcelinks_json)",
            "--define=score_source_code_linker_plain_links=1",
        ] + (["--define=score_metamodel_yaml=$(location " + str(metamodel) + ")"] if metamodel else []),
        formats = ["needs"],
        sphinx = ":sphinx_build",
        tools = data + metamodel_label + [":sourcelinks_json", ":docs_bundle"] + mounts_manifest_label,
        visibility = ["//visibility:public"],
        # Persistent workers cause stale symlinks after dependency version
        # changes, corrupting the Bazel cache.
        allow_persistent_workers = False,
    )

    native.genrule(
        name = "metrics_json",
        srcs = [":needs_json"],
        outs = ["metrics.json"],
        cmd = "cp $(location :needs_json)/metrics.json $@",
        visibility = ["//visibility:public"],
    )

    native.alias(
        name = "traceability_gate",
        actual = Label("//scripts_bazel:traceability_gate"),
        tags = ["cli_help=Enforce traceability coverage thresholds:\nbazel run //:traceability_gate -- --metrics-json $(location //:metrics_json)"],
    )

def _sourcelinks_json(name, srcs):
    """
    Creates a target that generates a JSON file with source code links.

    See https://eclipse-score.github.io/docs-as-code/main/how-to/source_to_doc_links.html

    Args:
      name: Name of the target.
      srcs: Source files to scan for traceability tags.
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
