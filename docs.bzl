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
load(
    "@score_docs_as_code//:bzl/basics.bzl",
    "glob_doc_sources",
    "join_path",
)
load(
    "@score_docs_as_code//:bzl/bundle_rules.bzl",
    "bundle_source_files",
    "create_bundle",
    "external_docs_runfiles",
    "generate_code_target_sourcelinks",
    "merge_bundle_sourcelinks",
)
load(
    "@score_docs_as_code//:bzl/mount_rules.bzl",
    "create_mounts_manifest",
)
load(
    "@sphinxdocs//sphinxdocs:sphinx.bzl",
    "sphinx_build_binary",
    "sphinx_docs",
)
load("@sphinxdocs//sphinxdocs:sphinx_docs_library.bzl", "sphinx_docs_library")

def _module_name_without_prefix():
    """Return the current Bazel module name without its first prefix."""
    module_name = native.module_name()
    if not module_name:
        return ""
    return module_name.split("_", 1)[-1]

def _generated_conf_impl(ctx):
    output = ctx.actions.declare_file(ctx.attr.output_path)
    ctx.actions.expand_template(
        template = ctx.file.template,
        output = output,
        substitutions = {
            "{PROJECT}": repr(ctx.attr.project),
            "{PROJECT_URL}": repr(ctx.attr.project_url),
            "{REQUIRED_IN_ID}": repr([ctx.attr.required_in_id]) if ctx.attr.required_in_id else "[]",
        },
    )
    return [DefaultInfo(files = depset([output]))]

_generated_conf = rule(
    implementation = _generated_conf_impl,
    attrs = {
        "project": attr.string(mandatory = True),
        "project_url": attr.string(mandatory = True),
        "required_in_id": attr.string(mandatory = True),
        "output_path": attr.string(mandatory = True),
        "template": attr.label(
            allow_single_file = True,
            default = Label("@score_docs_as_code//:default_conf.py.tpl"),
        ),
    },
)

def docs_bundle(name, source_dir = None, data = [], entry_doc = "index", bundles = [], scan_code = [], code_targets = [], visibility = None, **kwargs):
    """A docs bundle, optionally composed of others.

    Args:
      name: target name.
      source_dir: optional directory holding this bundle's own doc sources. It is
        globbed like `docs()` (same file kinds) and the contents are stored after
        stripping the `source_dir` prefix. Leave it unset for a pure aggregator.
      data: Files owned by this bundle that are not discovered as documentation
        sources. This includes generated RST, literalinclude inputs, and assets
        that belong at the bundle's eventual mount location. Omitting
        ``source_dir`` creates a bundle containing only these files.
      entry_doc: bundle-relative docname attached when this bundle is mounted.
        Defaults to `index`.
      bundles: nested bundles to compose, each a dict
        {
            "bundle": <docs_bundle label>,
            "mount_at": <where it shall me mounted>,
            "attach_to": <optional document to attach the bundle to; for a bundle root it defaults to the mount_at parent's index>
        }.
      scan_code: Deprecated. Explicit source files or filegroups to scan for
                 source-code links. Use `code_targets` for implementation targets.
      code_targets: Implementation targets or filegroups to scan for source-code
                    links. Implementation target source files and their dependencies
                    are collected recursively; filegroups expand to their files.
      visibility: Target visibility.
      **kwargs: Additional attributes forwarded to the underlying rule.
    """

    srcs = glob_doc_sources(source_dir) if source_dir != None else []
    sourcelinks = []
    if scan_code:
        print("WARNING: docs_bundle(%s) uses deprecated scan_code; use code_targets instead." % name)
        sourcelinks_name = name + "_sourcelinks_json"
        _sourcelinks_json(name = sourcelinks_name, srcs = scan_code)
        sourcelinks = [":" + sourcelinks_name]
    if code_targets:
        code_targets_sourcelinks = generate_code_target_sourcelinks(
            name = name + "_code_targets_sourcelinks_json",
            code_targets = code_targets,
        )
        sourcelinks.append(code_targets_sourcelinks)

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
        entry_doc = entry_doc,
        bundles = bundles,
        data = data,
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
        project = None,
        project_url = None,
        data = [],
        deps = [],
        external_needs = [],
        scan_code = [],
        code_targets = [],
        test_sources = [],
        known_good = None,
        metamodel = None,
        bundles = []):
    """Creates all targets related to documentation.

    By using this function, you'll get any and all updates for documentation targets in one place.

    Args:
      source_dir: The source directory containing documentation files. Defaults to "docs".
      project: optional project name, prefer setting this here if you can avoid having a conf.py
      project_url: Optional project URL, prefer setting this here if you can avoid having a conf.py
      data: Additional files owned by this project's root ``:docs_bundle``.
        This is shorthand for declaring the files in that root bundle; mounted
        child content belongs in the child ``docs_bundle(data = [...])``.
      deps: Additional dependencies for the documentation build.
      external_needs: List of external needs targets to include in the documentation build.
      scan_code: Deprecated. Explicit source files or filegroups to scan for source
                 code links. Use `code_targets` for implementation targets.
      code_targets: Implementation targets or filegroups to scan for source code
                    links. Implementation targets are scanned recursively; filegroups
                    expand to their files.
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
                }.
              Note: a bundle label may also point at another module's auto-exposed
              bundle, e.g. "@score_process_description//:docs_bundle".

    ``docs(data = [...])`` owns files in the root ``:docs_bundle``. A child
    bundle uses the same ``data`` attribute and may omit ``source_dir`` when it
    contains only generated or supporting files.
    """
    # HINT: keep documentation sync docs/reference/bazel_macros.rst

    config_file_path = join_path(source_dir, "conf.py")
    sphinx_config = ":" + config_file_path
    config_is_generated = len(native.glob([config_file_path], allow_empty = True)) == 0

    if config_is_generated:
        if not project or not project_url:
            fail("docs(): no " + config_file_path + " found; provide both project and project_url to docs().")

        # Generate the config at the source-root location expected by
        # sphinx_docs: that rule treats the config file's directory as the
        # Sphinx source directory.
        _generated_conf(
            name = "_docs_generated_config",
            project = project,
            project_url = project_url,
            required_in_id = _module_name_without_prefix(),
            output_path = config_file_path,
        )
        sphinx_config = ":_docs_generated_config"

    # Convention in this macro: an optional Bazel label is named ``*_label``
    # but represented as a 0/1 list. This lets it be appended directly to
    # list-valued attributes such as ``data`` and ``tools``.
    metamodel_label = [metamodel] if metamodel else []

    root_bundle_data_for_sphinx = []
    if data:
        # The bundle provider records ownership and propagation. Sphinx uses
        # its standard library provider to map the same files into the
        # sandboxed source tree while preserving workspace-relative paths for
        # literalinclude.
        sphinx_docs_library(
            name = "_root_bundle_data_for_sphinx",
            srcs = data,
            # rules_sphinxdocs treats an empty strip_prefix as the package
            # path. An unmatched prefix preserves the workspace-relative paths
            # used by this macro's direct documentation sources.
            strip_prefix = "__root_bundle_data__",
        )
        root_bundle_data_for_sphinx = [":_root_bundle_data_for_sphinx"]

    mounts_manifest_label = []
    if bundles:
        mounts_bundle = create_bundle(
            name = "_docs_mounts",
            bundles = bundles,
            visibility = ["//visibility:private"],
        )

        mounts_manifest_label = [
            create_mounts_manifest(
                name = "_mounts_manifest",
                bundle = mounts_bundle,
            ),
        ]

    deps = deps + _missing_requirements(deps)
    deps = deps + [
        Label("//src:plantuml_for_python"),
        Label("//src/extensions/score_sphinx_bundle:score_sphinx_bundle"),
    ]

    incremental_src = Label("//src:incremental.py")

    sphinx_build_binary(
        name = "sphinx_build",
        visibility = ["//visibility:private"],
        data = data + external_needs + metamodel_label + [":docs_bundle"],
        deps = deps,
        tags = ["manual"]
    )

    known_good_label = [known_good] if known_good else []

    # The public bundle carries both the complete source tree and the
    # transitive source-code links of every nested bundle.
    docs_bundle(
        name = "docs_bundle",
        source_dir = source_dir,
        data = data,
        entry_doc = "index",
        bundles = bundles,
        scan_code = scan_code,
        code_targets = code_targets,
        visibility = ["//visibility:public"],
        tags = ["manual"]
    )
    sphinx_sources = bundle_source_files(
        name = "_docs_sphinx_sources",
        bundle = ":docs_bundle",
        visibility = ["//visibility:private"],
    )
    merge_bundle_sourcelinks(
        name = "sourcelinks_json",
        bundle = ":docs_bundle",
        known_good = known_good,
    )

    external_docs_runfiles(
        name = "_external_docs_runfiles",
        bundle = ":docs_bundle",
        visibility = ["//visibility:private"],
    )

    # ``bazel run`` reads local documentation from the workspace, so including
    # the complete bundle in runfiles would duplicate those sources. External
    # bundles do need runfiles, so keep only those sources.
    docs_data = (
        data + external_needs + metamodel_label +
        [":sourcelinks_json", ":_external_docs_runfiles"] +
        mounts_manifest_label
    )
    if config_is_generated:
        # A source configuration is read from the workspace; only the
        # generated configuration must be present in the runfiles tree.
        docs_data += [sphinx_config]

    docs_env = {
        "SOURCE_DIRECTORY": source_dir,
        "PACKAGE_DIR": native.package_name(),
        "TEST_SOURCES": str(test_sources),
        "DATA": str(data),
        "EXTERNAL_NEEDS_FILES": str(external_needs),
        # `bazel run` starts from a runfiles tree, so this logical path is
        # resolved by score_mounts through ``RUNFILES_DIR``.
        "MOUNTS_MANIFEST": "$(rlocationpath :_mounts_manifest)" if bundles else "",
        "SCORE_SOURCELINKS": "$(location :sourcelinks_json)",
    }
    if config_is_generated:
        # The generated file is named conf.py. Run targets pass its containing
        # directory to Sphinx via -c.
        docs_env["SPHINX_CONFIG_FILE"] = "$(rlocationpath " + sphinx_config + ")"
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
        # Generated documentation artifacts may live below ``docs/``.  A
        # py_binary named ``docs`` would own the conflicting Bazel output path
        # ``docs``; expose this binary via the alias below instead.
        name = "_score_docs_cli",
        srcs = [incremental_src],
        data = docs_data,
        deps = deps,
        env = docs_env,
        tags = ["manual"],
    )

    native.alias(
        name = "docs",
        actual = ":_score_docs_cli",
        tags = ["manual"],
    )

    docs_env["ACTION"] = "linkcheck"
    py_binary(
        name = "docs_link_check",
        tags = ["manual"],
        srcs = [incremental_src],
        data = docs_data,
        deps = deps,
        env = docs_env,
    )

    docs_env["ACTION"] = "check"
    py_binary(
        name = "docs_check",
        tags = ["manual"],
        srcs = [incremental_src],
        data = docs_data,
        deps = deps,
        env = docs_env,
    )

    docs_env["ACTION"] = "live_preview"
    py_binary(
        name = "live_preview",
        tags = ["manual"],
        srcs = [incremental_src],
        data = docs_data,
        deps = deps,
        env = docs_env,
    )

    py_venv(
        name = "ide_support",
        tags = ["manual"],
        venv_name = ".venv_docs",
        deps = deps,
        data = data,
        package_collisions = "warning",
    )

    sphinx_docs(
        name = "needs_json",
        # Nested bundle sources are mounted by score_mounts. Passing the
        # complete bundle as srcs would also expose those files as raw Sphinx
        # sources and make every nested need appear twice.
        srcs = [sphinx_sources],
        deps = root_bundle_data_for_sphinx,
        config = sphinx_config,
        extra_opts = [
            "-W",
            "--keep-going",
            "-T",  # show more details in case of errors
            "--jobs",
            "auto",
            "--define=external_needs_source=" + str(data + external_needs),
            "--define=score_sourcelinks_json=$(location :sourcelinks_json)",
            "--define=score_source_code_linker_plain_links=1",
        ] + (
            # ``sphinx_docs`` is a sandboxed build action, so it needs the
            # action-input path rather than the runfiles-relative spelling.
            ["--define=mounts_manifest=$(location :_mounts_manifest)"] if bundles else []
        ) + (["--define=score_metamodel_yaml=$(location " + str(metamodel) + ")"] if metamodel else []),
        formats = ["needs"],
        sphinx = ":sphinx_build",
        tools = external_needs + metamodel_label + [":sourcelinks_json", ":docs_bundle"] + mounts_manifest_label,
        visibility = ["//visibility:public"],
        # Persistent workers cause stale symlinks after dependency version
        # changes, corrupting the Bazel cache.
        allow_persistent_workers = False,
        tags = ["manual"],
    )

    native.genrule(
        name = "metrics_json",
        srcs = [":needs_json"],
        outs = ["metrics.json"],
        cmd = "cp $(location :needs_json)/metrics.json $@",
        visibility = ["//visibility:public"],
        tags = ["manual"],
    )

    native.genrule(
        # In contrast to the "needs_json" target represents *only* the needs.json file,
        # not the whole needs build output.
        name = "needs_json_file",
        srcs = [":needs_json"],
        outs = ["needs.json"],
        cmd = "cp $(location :needs_json)/needs.json $@",
        visibility = ["//visibility:public"],
        tags = ["manual"],
    )

    native.alias(
        name = "traceability_gate",
        actual = Label("//scripts_bazel:traceability_gate"),
        tags = ["manual"],
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
        tags = ["manual"],
    )
