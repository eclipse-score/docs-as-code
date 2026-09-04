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

def _bundle_internal_target(name, target):
    """Return the conventional name for a target internal to a bundle."""
    return name + ".__internal__." + target

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

def _is_needs_json_target(label):
    """Return whether ``label`` names the directory-valued ``needs_json`` target.

    ``docs(data = [...])`` historically accepts ``:needs_json`` labels as
    external Needs inventories. The target is a Bazel TreeArtifact containing
    ``needs.json`` and other generated outputs, so it is a build/runfile input
    rather than a file that belongs in a portable documentation-bundle mount.
    Keep this compatibility distinction at the public macro boundary instead
    of making the generic bundle and mount implementations understand a
    special-purpose generated directory.
    """
    return str(label).rsplit(":", 1)[-1] == "needs_json"

def _declare_docs_bundle(
    name,
    source_dir = None,
    srcs = [],
    data = [],
    entry_doc = "index",
    bundles = [],
    code_targets = [],
    visibility = None,
    **kwargs):
    """Declare the shared bundle target implementation.

    This helper performs the bundle declaration used by both public entry
    points. It deliberately contains no targets for consuming a bundle on its
    own; those can be added to the public ``docs_bundle`` wrapper without
    making ``docs()`` create them for the project root.

    Args:
      name: target name.
      source_dir: optional directory holding this bundle's own doc sources. It is
        globbed like `docs()` (same file kinds) and the contents are stored after
        stripping the `source_dir` prefix. Leave it unset for a pure aggregator.
      srcs: Explicit documentation source files, including generated files.
        Use this for a source-less bundle whose documentation is produced by a
        build action. All files must share one parent directory so they can be
        mounted as one bundle entry.
      data: Files owned by this bundle that are not discovered as documentation
        sources. Use this for runtime/support files that belong at the bundle's
        eventual mount location. ``docs(data = [...])`` is the corresponding
        shorthand for supporting files in the project's root bundle. Both
        forms make their files available to a build; only bundle data travels
        with a mounted bundle.
      entry_doc: bundle-relative docname attached when this bundle is mounted.
        Defaults to `index`.
      bundles: nested bundles to compose, each a dict
        {
            "bundle": <docs_bundle label>,
            "mount_at": <where it shall me mounted>,
            "attach_to": <optional document to attach the bundle to; for a bundle root it defaults to the mount_at parent's index>
        }.
      code_targets: Implementation targets or filegroups to scan for source-code
                    links. Implementation target source files and their dependencies
                    are collected recursively; filegroups expand to their files.
      visibility: Target visibility.
      **kwargs: Additional attributes forwarded to the underlying rule.
    """

    if source_dir != None and srcs:
        fail(
            ("docs_bundle(%s): srcs cannot be combined with source_dir; " +
             "put generated sources in a dedicated bundle") % name,
        )
    # Keep directory-discovered sources separate from explicit Bazel targets so
    # each kind can retain its own runtime path and staging behavior.
    source_dir_globbed = glob_doc_sources(source_dir) if source_dir != None else []
    sourcelinks_json = None
    if code_targets:
        sourcelinks_json = generate_code_target_sourcelinks(
            name = _bundle_internal_target(name, "sourcelinks_json"),
            code_targets = code_targets,
        )

    # Store the source directory relative to the workspace so bundle consumers
    # can locate the original files without copying them.
    pkg = native.package_name()
    strip_prefix = join_path(pkg, source_dir) if source_dir != None else ""

    # ``needs_json`` is an inventory consumed by score_metamodel, not content
    # owned by this bundle. It must remain in the caller's build/runfile inputs
    # for the legacy ``docs(data = [...])`` API, but propagating the TreeArtifact
    # through DocsBundleInfo would make a later bundle mount treat its directory
    # path as a regular data file. Filter only this special target here; all
    # ordinary supporting files retain the root-bundle behavior.
    bundle_data = [
        data_file
        for data_file in data
        if not _is_needs_json_target(data_file)
    ]

    # The helper validates child declarations and creates the internal target.
    create_bundle(
        name = name,
        source_dir_globbed = source_dir_globbed,
        source_targets = srcs,
        sourcelinks_json = sourcelinks_json,
        strip_prefix = strip_prefix,
        entry_doc = entry_doc,
        bundles = bundles,
        data = bundle_data,
        visibility = visibility,
        **kwargs
    )

def docs_bundle(
    name,
    source_dir = None,
    srcs = [],
    data = [],
    entry_doc = "index",
    bundles = [],
    code_targets = [],
    visibility = None,
    **kwargs):
    """Declare a reusable documentation bundle.

    The declaration itself is delegated to the shared helper. Keeping this
    public entry point separate gives bundle-specific consumer targets a
    distinct home while allowing ``docs()`` to use the shared declaration for
    the project root.
    """
    _declare_docs_bundle(
        name = name,
        source_dir = source_dir,
        srcs = srcs,
        data = data,
        entry_doc = entry_doc,
        bundles = bundles,
        code_targets = code_targets,
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
        For generated documentation in a mounted child, use that bundle's
        explicit ``srcs`` instead; ``data`` remains for supporting/runtime
        files.
      deps: Additional dependencies for the documentation build.
      external_needs: List of external needs targets to include in the documentation build.
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
    contains only supporting files. Use explicit ``srcs`` in a source-less
    child bundle when its documentation is generated by a build action.
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
        # TODO: Replace this adapter once the mounts manifest can preserve a
        # data file's destination path below the root documentation tree.
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
    _declare_docs_bundle(
        name = "docs_bundle",
        source_dir = source_dir,
        data = data,
        entry_doc = "index",
        bundles = bundles,
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

def filtered_needs_json(
        name,
        src,
        types = [],
        names = [],
        strict = False,
        extra_needs = [],
        link_fields = [],
        visibility = None):
    """Extract a subset of sphinx-needs elements from a needs.json file.

    Produces a `<name>.json` file containing only the needs that match all of
    the given filters. This is useful to hand a downstream consumer just the
    elements (e.g. `feat_req`) of one or more particular features/components.

    Args:
        name: Name of the generated target. The output file is `<name>.json`.
        src: Label of a `needs_json` build output (a directory containing
            `needs.json`), e.g. `":needs_json"` or `"@score_process//:needs_json"`.
        types: Optional list of sphinx-needs element types to keep
            (e.g. `["feat_req", "comp_req"]`). If empty, all types are kept.
        names: Optional list of feature/component names to keep, matched against
            the `title` of the `feat`/`comp` element the need links to:
            `feat_req`/`comp_req` via `satisfied_by` (legacy `belongs_to`
            fallback), `feat_arc_*`/`comp_arc_*` via `belongs_to`. Other types
            fall back to the second `__`-separated ID segment. If empty, all
            features/components are kept.
        strict: When True the build fails (and no `<name>.json` is written) if any
            kept need has a dangling link, i.e. a link target that is present
            neither in `src` nor in any `extra_needs` input. Off by default.
        extra_needs: Optional list of additional `needs_json` build outputs whose
            needs count as resolvable link targets in `strict` mode (e.g.
            requirements imported from an upstream repository). Typically the same
            upstream `needs_json` targets passed as `data` to `docs(...)` (e.g.
            `["@score_platform//:needs_json"]`).
        link_fields: Optional list of link fields checked for dangling references
            in `strict` mode (e.g. `["derived_from", "satisfies"]`). If empty,
            every link field is checked (auto-detected from the data).
        visibility: Standard Bazel visibility for the generated target.
    """
    filter_tool = Label("//scripts_bazel:filter_needs_json")

    type_args = " ".join(["--type '%s'" % t for t in types])
    name_args = " ".join(["--name '%s'" % n for n in names])
    strict_arg = "--strict" if strict else ""
    link_args = " ".join(["--link-field '%s'" % f for f in link_fields])
    extra_args = " ".join(["--extra-needs-json $(location %s)" % e for e in extra_needs])

    native.genrule(
        name = name,
        srcs = [src] + extra_needs,
        outs = [name + ".json"],
        cmd = """
        SRC="$(location {src})"
        if [ -d "$$SRC" ]; then SRC="$$SRC/needs.json"; fi
        $(location {filter_tool}) \
            --output $@ \
            {type_args} \
            {name_args} \
            {strict_arg} \
            {link_args} \
            {extra_args} \
            "$$SRC"
        """.format(
            filter_tool = filter_tool,
            type_args = type_args,
            name_args = name_args,
            strict_arg = strict_arg,
            link_args = link_args,
            extra_args = extra_args,
            src = src,
        ),
        tools = [filter_tool],
        visibility = visibility,
    )

def component_requirements(
        name,
        src = "//:needs_json",
        component = None,
        strict = False,
        extra_needs = [],
        link_fields = [],
        visibility = None):
    """Extract the component requirements (`comp_req`) from a needs.json file.

    Convenience wrapper around `filtered_needs_json`. Produces a `<name>.json`
    file containing only `comp_req` elements.

    Args:
        name: Name of the generated target. The output file is `<name>.json`.
        src: Label of a `needs_json` build output. Defaults to the calling
            package's `//:needs_json`.
        component: Optional component name. If given, only component requirements
            linked to a component whose `title` matches are kept; the component
            is resolved via the requirement's `satisfied_by` link (legacy
            `belongs_to` fallback). If omitted, all component requirements are
            kept.
        strict: When True the build fails (no output) on any dangling link in the
            kept needs. See `filtered_needs_json`.
        extra_needs: Additional `needs_json` build outputs whose needs count as
            resolvable link targets in `strict` mode. See `filtered_needs_json`.
        link_fields: Link fields checked for dangling references in `strict`
            mode. If empty, every link field is checked.
        visibility: Standard Bazel visibility for the generated target.
    """
    filtered_needs_json(
        name = name,
        src = src,
        types = ["comp_req"],
        names = [component] if component else [],
        strict = strict,
        extra_needs = extra_needs,
        link_fields = link_fields,
        visibility = visibility,
    )

def feature_requirements(
        name,
        src = "//:needs_json",
        feature = None,
        strict = False,
        extra_needs = [],
        link_fields = [],
        visibility = None):
    """Extract the feature requirements (`feat_req`) from a needs.json file.

    Convenience wrapper around `filtered_needs_json`. Produces a `<name>.json`
    file containing only `feat_req` elements.

    Args:
        name: Name of the generated target. The output file is `<name>.json`.
        src: Label of a `needs_json` build output. Defaults to the calling
            package's `//:needs_json`.
        feature: Optional feature name. If given, only feature requirements
            linked to a feature whose `title` matches are kept; the feature is
            resolved via the requirement's `satisfied_by` link (legacy
            `belongs_to` fallback). If omitted, all feature requirements are
            kept.
        strict: When True the build fails (no output) on any dangling link in the
            kept needs. See `filtered_needs_json`.
        extra_needs: Additional `needs_json` build outputs whose needs count as
            resolvable link targets in `strict` mode. See `filtered_needs_json`.
        link_fields: Link fields checked for dangling references in `strict`
            mode. If empty, every link field is checked.
        visibility: Standard Bazel visibility for the generated target.
    """
    filtered_needs_json(
        name = name,
        src = src,
        types = ["feat_req"],
        names = [feature] if feature else [],
        strict = strict,
        extra_needs = extra_needs,
        link_fields = link_fields,
        visibility = visibility,
    )

def assumptions_of_use(
        name,
        src = "//:needs_json",
        component = None,
        strict = False,
        extra_needs = [],
        link_fields = [],
        visibility = None):
    """Extract the assumptions of use (`aou_req`) from a needs.json file.

    Convenience wrapper around `filtered_needs_json`. Produces a `<name>.json`
    file containing only `aou_req` elements.

    Args:
        name: Name of the generated target. The output file is `<name>.json`.
        src: Label of a `needs_json` build output. Defaults to the calling
            package's `//:needs_json`.
        component: Optional component name. If given, only assumptions of use
            named with that component (per the `<type>__<name>__...`
            convention) are kept; if omitted, all assumptions of use are kept.
        strict: When True the build fails (no output) on any dangling link in the
            kept needs. See `filtered_needs_json`.
        extra_needs: Additional `needs_json` build outputs whose needs count as
            resolvable link targets in `strict` mode. See `filtered_needs_json`.
        link_fields: Link fields checked for dangling references in `strict`
            mode. If empty, every link field is checked.
        visibility: Standard Bazel visibility for the generated target.
    """
    filtered_needs_json(
        name = name,
        src = src,
        types = ["aou_req"],
        names = [component] if component else [],
        strict = strict,
        extra_needs = extra_needs,
        link_fields = link_fields,
        visibility = visibility,
    )

def feature_architecture(
        name,
        src = "//:needs_json",
        feature = None,
        strict = False,
        extra_needs = [],
        link_fields = [],
        visibility = None):
    """Extract the feature architecture from a needs.json file.

    Convenience wrapper around `filtered_needs_json`. Produces a `<name>.json`
    file containing the feature architecture elements. Static (`feat_arc_sta`)
    and dynamic (`feat_arc_dyn`) architecture are not differentiated; both are
    kept.

    Args:
        name: Name of the generated target. The output file is `<name>.json`.
        src: Label of a `needs_json` build output. Defaults to the calling
            package's `//:needs_json`.
        feature: Optional feature name. If given, only feature architecture
            elements linked to a feature whose `title` matches are kept; the
            feature is resolved via the element's `belongs_to` link. If omitted,
            all feature architecture elements are kept.
        strict: When True the build fails (no output) on any dangling link in the
            kept needs. See `filtered_needs_json`.
        extra_needs: Additional `needs_json` build outputs whose needs count as
            resolvable link targets in `strict` mode. See `filtered_needs_json`.
        link_fields: Link fields checked for dangling references in `strict`
            mode. If empty, every link field is checked.
        visibility: Standard Bazel visibility for the generated target.
    """
    filtered_needs_json(
        name = name,
        src = src,
        types = ["feat_arc_sta", "feat_arc_dyn"],
        names = [feature] if feature else [],
        strict = strict,
        extra_needs = extra_needs,
        link_fields = link_fields,
        visibility = visibility,
    )

def component_architecture(
        name,
        src = "//:needs_json",
        component = None,
        strict = False,
        extra_needs = [],
        link_fields = [],
        visibility = None):
    """Extract the component architecture from a needs.json file.

    Convenience wrapper around `filtered_needs_json`. Produces a `<name>.json`
    file containing the component architecture elements. Static (`comp_arc_sta`)
    and dynamic (`comp_arc_dyn`) architecture are not differentiated; both are
    kept.

    Args:
        name: Name of the generated target. The output file is `<name>.json`.
        src: Label of a `needs_json` build output. Defaults to the calling
            package's `//:needs_json`.
        component: Optional component name. If given, only component architecture
            elements linked to a component whose `title` matches are kept; the
            component is resolved via the element's `belongs_to` link. If
            omitted, all component architecture elements are kept.
        strict: When True the build fails (no output) on any dangling link in the
            kept needs. See `filtered_needs_json`.
        extra_needs: Additional `needs_json` build outputs whose needs count as
            resolvable link targets in `strict` mode. See `filtered_needs_json`.
        link_fields: Link fields checked for dangling references in `strict`
            mode. If empty, every link field is checked.
        visibility: Standard Bazel visibility for the generated target.
    """
    filtered_needs_json(
        name = name,
        src = src,
        types = ["comp_arc_sta", "comp_arc_dyn"],
        names = [component] if component else [],
        strict = strict,
        extra_needs = extra_needs,
        link_fields = link_fields,
        visibility = visibility,
    )

def requirements_checklist(
        name,
        deps,
        mod_insp_id,
        src = "//:needs_json",
        link_fields = ["derived_from", "satisfies", "covers"],
        extra_needs = [],
        visibility = None):
    """Validate a requirement inspection record against its build output.

    Building this target recomputes the SHA256 over the requirements in `deps`
    **and**, by default, over everything they depend on transitively, and
    compares it to the `sha256` attribute of the `mod_insp` inspection record
    `mod_insp_id` (looked up in `src`'s `needs.json`). The build **fails** when
    the hashes differ, i.e. when a validated requirement *or one of its
    (recursive) dependencies* has changed since the inspection was last reviewed.

    The dependency graph is the sphinx-needs link graph: starting from the
    requirements in `deps` (the *roots*), the `link_fields` (by default
    `derived_from`, `satisfies` and `covers`) are followed recursively through
    `src`'s `needs.json`. For feature requirements this means the linked
    stakeholder requirements (and their parents in turn) are part of the hash, so
    changing a relevant stakeholder requirement makes this checklist go out of
    date. Pass `link_fields = []` to restore the old behaviour of hashing only
    the requirements in `deps`.

    Typical usage validates the extracted requirements of a component against the
    inspection record that reviewed them:

        component_requirements(
            name = "bitmanipulation_comp_reqs",
            component = "bitmanipulation",
        )

        requirements_checklist(
            name = "bitmanipulation_req_checklist",
            mod_insp_id = "mod_insp__bitmanipulation__comp_req",
            deps = [":bitmanipulation_comp_reqs"],
        )

    Run with `bazel build //:bitmanipulation_req_checklist`. On the first run (or
    after the requirements change) the build fails and prints the actual SHA256;
    copy it into the `sha256` attribute of the inspection record once it has
    been (re-)reviewed.

    Args:
        name: Name of the generated target. The output file is `<name>.sha256`.
        deps: List of labels whose outputs define the root requirements that are
            hashed and validated. Usually a single
            `component_requirements`/`feature_requirements`/`filtered_needs_json`
            target.
        mod_insp_id: Id of the `mod_insp` inspection record to validate
            (e.g. `"mod_insp__bitmanipulation__comp_req"`).
        src: Label of a `needs_json` build output containing the inspection record
            and the full link graph. Defaults to the calling package's
            `//:needs_json`.
        link_fields: Sphinx-needs link fields followed recursively from the root
            requirements to include their (transitive) dependencies in the hash.
            Defaults to `["derived_from", "satisfies", "covers"]`. Set to `[]` to
            hash only the requirements in `deps`.
        extra_needs: Optional list of additional `needs_json` build outputs that
            provide the full content of needs referenced from the validated
            requirements but not contained in `src` (e.g. stakeholder
            requirements imported from an upstream repository). Without them such
            external needs are hashed as `<MISSING>` and changes to them are not
            detected. Typically the same upstream `needs_json` targets passed as
            `data` to `docs(...)` (e.g. `["@score_platform//:needs_json"]`).
        visibility: Standard Bazel visibility for the generated target.
    """
    validate_tool = Label("//scripts_bazel:validate_checklist")

    dep_args = " ".join(["$(locations %s)" % d for d in deps])
    link_args = " ".join(["--link-field '%s'" % f for f in link_fields])
    extra_args = " ".join(["--extra-needs-json $(location %s)/needs.json" % e for e in extra_needs])

    native.genrule(
        name = name,
        srcs = [src] + extra_needs + deps,
        outs = [name + ".sha256"],
        cmd = """
        $(location {validate_tool}) \
            --needs-json $(location {src})/needs.json \
            --checklist-id '{mod_insp_id}' \
            --output $@ \
            {link_args} \
            {extra_args} \
            {dep_args}
        """.format(
            validate_tool = validate_tool,
            mod_insp_id = mod_insp_id,
            src = src,
            link_args = link_args,
            extra_args = extra_args,
            dep_args = dep_args,
        ),
        tools = [validate_tool],
        visibility = visibility,
    )

def architecture_checklist(
        name,
        deps,
        mod_insp_id,
        src = "//:needs_json",
        link_fields = ["fulfils", "includes", "uses", "provides", "derived_from", "satisfies", "covers"],
        extra_needs = [],
        visibility = None):
    """Validate an architecture inspection record against its build output.

    Building this target recomputes the SHA256 over the architecture in `deps`
    **and**, by default, over everything they depend on transitively, and
    compares it to the `sha256` attribute of the `mod_insp` inspection record
    `mod_insp_id` (looked up in `src`'s `needs.json`). The build **fails** when
    the hashes differ, i.e. when a validated architecture element *or one of its
    (recursive) dependencies* has changed since the inspection was last reviewed.

    The dependency graph is the sphinx-needs link graph: starting from the
    architecture elements in `deps` (the *roots*), the `link_fields` are followed
    recursively through `src`'s `needs.json`. The defaults follow the structural
    architecture links (`includes`, `uses`, `provides`) as well as `fulfils` and
    the requirement links (`derived_from`, `satisfies`, `covers`), so the closure
    reaches the fulfilled requirements and their parents. Changing a fulfilled
    requirement (or a stakeholder requirement it derives from) therefore makes
    this checklist go out of date. Pass `link_fields = []` to restore the old
    behaviour of hashing only the elements in `deps`.

    Typical usage validates the extracted architecture of a component against the
    inspection record that reviewed it:

        component_architecture(
            name = "bitmanipulation_comp_arch",
            component = "bitmanipulation",
        )

        architecture_checklist(
            name = "bitmanipulation_arch_checklist",
            mod_insp_id = "mod_insp__bitmanipulation__comp_arc",
            deps = [":bitmanipulation_comp_arch"],
        )

    Run with `bazel build //:bitmanipulation_arch_checklist`. On the first run (or
    after the architecture changes) the build fails and prints the actual SHA256;
    copy it into the `sha256` attribute of the inspection record once it has
    been (re-)reviewed.

    Args:
        name: Name of the generated target. The output file is `<name>.sha256`.
        deps: List of labels whose outputs define the root architecture elements
            that are hashed and validated. Usually a single
            `feature_architecture`/`component_architecture`/`filtered_needs_json`
            target.
        mod_insp_id: Id of the `mod_insp` inspection record to validate
            (e.g. `"mod_insp__baselibs__feat_arc"`).
        src: Label of a `needs_json` build output containing the inspection record
            and the full link graph. Defaults to the calling package's
            `//:needs_json`.
        link_fields: Sphinx-needs link fields followed recursively from the root
            architecture elements to include their (transitive) dependencies in
            the hash. Defaults to the structural architecture links plus the
            requirement links. Set to `[]` to hash only the elements in `deps`.
        extra_needs: Optional list of additional `needs_json` build outputs that
            provide the full content of needs referenced from the validated
            architecture elements but not contained in `src` (e.g. feature
            requirements imported from an upstream repository). Without them such
            external needs are hashed as `<MISSING>` and changes to them are not
            detected. Typically the same upstream `needs_json` targets passed as
            `data` to `docs(...)` (e.g. `["@score_platform//:needs_json"]`).
        visibility: Standard Bazel visibility for the generated target.
    """
    validate_tool = Label("//scripts_bazel:validate_checklist")

    dep_args = " ".join(["$(locations %s)" % d for d in deps])
    link_args = " ".join(["--link-field '%s'" % f for f in link_fields])
    extra_args = " ".join(["--extra-needs-json $(location %s)/needs.json" % e for e in extra_needs])

    native.genrule(
        name = name,
        srcs = [src] + extra_needs + deps,
        outs = [name + ".sha256"],
        cmd = """
        $(location {validate_tool}) \
            --needs-json $(location {src})/needs.json \
            --checklist-id '{mod_insp_id}' \
            --output $@ \
            {link_args} \
            {extra_args} \
            {dep_args}
        """.format(
            validate_tool = validate_tool,
            mod_insp_id = mod_insp_id,
            src = src,
            link_args = link_args,
            extra_args = extra_args,
            dep_args = dep_args,
        ),
        tools = [validate_tool],
        visibility = visibility,
    )
