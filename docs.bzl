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
    "bundle_own_files",
    "merge_bundle_sourcelinks",
    "external_docs_runfiles",
    "generate_code_target_sourcelinks",
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
            "{ENTRY_DOC}": repr(ctx.attr.entry_doc),
        },
    )
    return [DefaultInfo(files = depset([output]))]

_generated_conf = rule(
    implementation = _generated_conf_impl,
    attrs = {
        "project": attr.string(mandatory = True),
        "project_url": attr.string(mandatory = True),
        "required_in_id": attr.string(mandatory = True),
        "entry_doc": attr.string(default = "index"),
        "output_path": attr.string(mandatory = True),
        "template": attr.label(
            allow_single_file = True,
            default = Label("@score_docs_as_code//:default_conf.py.tpl"),
        ),
    },
)

def _create_metamodel_tool(name, metamodel):
    """Expose a metamodel file as an executable Sphinx tool input.

    rules_sphinxdocs intentionally restricts ``tools`` to executable targets,
    while ``$(location ...)`` in a Sphinx action still needs the metamodel's
    sandboxed path. Copying the file through an executable genrule satisfies
    both constraints without changing the file contents.
    """
    native.genrule(
        name = name,
        srcs = [metamodel],
        outs = [name + ".yaml"],
        cmd = "cp $(location " + str(metamodel) + ") $@",
        executable = True,
        visibility = ["//visibility:private"],
    )
    return ":" + name

def _bundle_upward_needs_label(bundle):
    """Return the generated upward-needs label for a docs_bundle label."""
    bundle_string = str(bundle)
    if bundle_string.startswith(":"):
        bundle_string = "//" + native.package_name() + bundle_string
    elif not bundle_string.startswith("//") and not bundle_string.startswith("@"):
        bundle_string = "//" + native.package_name() + ":" + bundle_string
    return Label(bundle_string + "_needs_upward")

def _external_needs_label(label):
    """Format a label for score_metamodel's external-needs parser."""
    label_string = str(label)
    if label_string.startswith("@@//"):
        return label_string[2:]
    if label_string.startswith("@@"):
        canonical = label_string[2:]
        repository, separator, package_and_target = canonical.partition("//")
        # Bazel 8's canonical Bzlmod spelling uses ``repo+``. The runfiles
        # layout and the external-needs parser use the user-facing module name
        # and add the ``+`` themselves where needed.
        if repository.endswith("+"):
            repository = repository[:-1]
        return "@" + repository + separator + package_and_target
    return label_string

def docs_bundle(name, source_dir = None, data = [], entry_doc = "index", metamodel = None, bundles = [], upward_bundles = [], scan_code = [], code_targets = [], deps = [], bundle_conf = None, visibility = None, **kwargs):
    """A docs bundle, optionally composed of others.

    Args:
      name: target name.
      source_dir: optional directory holding this bundle's own doc sources. It is
        globbed like `docs()` (same file kinds) and the contents are stored after
        stripping the `source_dir` prefix. Leave it unset for a pure aggregator.
        data:
        Files owned by this bundle that are not discovered as documentation
        sources. Use this for generated RST or other generated files that are
        part of the bundle payload and belong at the bundle's eventual mount
        location. Use ``docs(data = [...])`` only for project-level inputs
        outside a bundle. Both forms make their files available to a build;
        only bundle data travels with a mounted bundle.
      entry_doc: bundle-relative docname attached when this bundle is mounted.
        Defaults to `index`.
      metamodel: optional metamodel label used for this bundle's Needs
        processing. If omitted, the built-in SCORE metamodel is used.
      bundles: nested bundles to compose, each a dict
        {
            "bundle": <docs_bundle label>,
            "mount_at": <where it shall me mounted>,
            "attach_to": <optional document to attach the bundle to; for a bundle root it defaults to the mount_at parent's index>
        }.
      upward_bundles: docs_bundle targets in the documentation hierarchy above
        this bundle. These are explicit Bazel dependencies used by the
        bundle-local Needs export; both direct declarations and the complete
        transitive upward closure are propagated through DocsBundleInfo. A
        source bundle imports the direct parent's merged export; an aggregator
        may use the relationship as a named hierarchy group.
      scan_code: Deprecated. Explicit source files or filegroups to scan for
                 source-code links. Use `code_targets` for implementation targets.
      code_targets: Implementation targets or filegroups to scan for source-code
                    links. Implementation target source files and their dependencies
                    are collected recursively; filegroups expand to their files.
      deps: Additional Python dependencies for the bundle-local Needs export.
      bundle_conf: Optional Sphinx conf.py label to reuse for the bundle-local
                   Needs export. This is used by docs() for its generated host
                   configuration.
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
    selected_metamodel = metamodel or Label("@score_docs_as_code//src/extensions/score_metamodel:metamodel_yaml")
    create_bundle(
        name = name,
        srcs = srcs,
        sourcelinks = sourcelinks,
        strip_prefix = strip_prefix,
        entry_doc = entry_doc,
        metamodel = selected_metamodel,
        bundles = bundles,
        upward_bundles = upward_bundles,
        data = data,
        visibility = visibility,
        **kwargs
    )

    upward_needs = [_bundle_upward_needs_label(bundle) for bundle in upward_bundles]

    # A bundle owns Needs only through its own documentation sources.  Keep
    # nested bundles out of this source set, while still making the generated
    # target useful for source-less aggregators that only carry no local docs.
    if srcs:
        metamodel_tool = None
        if metamodel:
            metamodel_tool = _create_metamodel_tool(
                name + "_needs_metamodel",
                selected_metamodel,
            )

        own_files = bundle_own_files(
            name = name + "_own_files",
            bundle = ":" + name,
            visibility = visibility,
        )

        config_file_path = join_path(source_dir, "conf.py")
        if bundle_conf:
            needs_config = bundle_conf
        elif native.glob([config_file_path], allow_empty = True):
            needs_config = ":" + config_file_path
        else:
            needs_config = ":" + name + "_needs_conf"
            _generated_conf(
                name = name + "_needs_conf",
                project = name,
                project_url = "",
                required_in_id = "",
                entry_doc = entry_doc,
                output_path = config_file_path,
                template = Label("@score_docs_as_code//:bundle_needs_conf.py.tpl"),
            )

        bundle_deps = deps + _missing_requirements(deps) + [
            Label("//src:plantuml_for_python"),
            Label("//src/extensions/score_sphinx_bundle:score_sphinx_bundle"),
        ]
        bundle_data = [own_files] + upward_needs
        if metamodel:
            bundle_data.append(selected_metamodel)

        if len(sourcelinks) == 0:
            needs_sourcelinks = ":" + name + "_needs_sourcelinks_json"
            _sourcelinks_json(
                name = name + "_needs_sourcelinks_json",
                srcs = [],
            )
        elif len(sourcelinks) == 1:
            needs_sourcelinks = sourcelinks[0]
        else:
            needs_sourcelinks_name = name + "_needs_sourcelinks_json"
            merge_bundle_sourcelinks(
                name = needs_sourcelinks_name,
                bundle = ":" + name,
                visibility = visibility,
            )
            needs_sourcelinks = ":" + needs_sourcelinks_name
        bundle_data.append(needs_sourcelinks)

        sphinx_build_binary(
            name = name + "_needs_sphinx_build",
            data = bundle_data,
            deps = bundle_deps,
            visibility = visibility,
        )

        needs_local = ":" + name + "_needs_local"
        needs_extra_opts = [
            "--keep-going",
            "-T",
            "--define=external_needs_source=" + str([
                _external_needs_label(label)
                for label in upward_needs
            ]),
        ]
        if metamodel:
            needs_extra_opts.append(
                "--define=score_metamodel_yaml=$(location " + metamodel_tool + ")"
            )
        needs_extra_opts.append(
            "--define=score_sourcelinks_json=$(location " + str(needs_sourcelinks) + ")"
        )

        needs_tools = list(upward_needs)
        if metamodel:
            needs_tools.append(metamodel_tool)
        needs_tools.append(needs_sourcelinks)

        sphinx_docs(
            name = name + "_needs_local",
            srcs = [own_files],
            config = needs_config,
            # sphinxdocs removes this string literally from short_path. Keep
            # the separator so a config at ``source_dir/conf.py`` becomes
            # ``conf.py`` rather than ``/conf.py``.
            strip_prefix = strip_prefix + "/" if strip_prefix else "",
            extra_opts = needs_extra_opts,
            formats = ["needs"],
            sphinx = ":" + name + "_needs_sphinx_build",
            tools = needs_tools,
            visibility = visibility,
            allow_persistent_workers = False,
        )

        needs_upward = name + "_needs_upward"
        merge_inputs = [needs_local] + upward_needs
        merge_command = "$(location //scripts_bazel:merge_needs_json) --output $@ $(location " + needs_local + ")/needs.json"
        for input_label in upward_needs:
            merge_command += " $(location " + str(input_label) + ")"
        native.genrule(
            name = needs_upward,
            srcs = merge_inputs,
            outs = [needs_upward + "/needs.json"],
            cmd = merge_command,
            tools = [Label("//scripts_bazel:merge_needs_json")],
            visibility = visibility,
        )
    elif upward_needs:
        # A source-less hierarchy group owns no Needs of its own, but it can
        # still expose the merged export of its declared ancestors. This lets
        # a child depend on a named hierarchy group without knowing how the
        # group's parent chain is assembled.
        needs_upward = name + "_needs_upward"
        merge_command = "$(location //scripts_bazel:merge_needs_json) --output $@ $(location " + str(upward_needs[0]) + ")"
        for input_label in upward_needs[1:]:
            merge_command += " $(location " + str(input_label) + ")"
        native.genrule(
            name = needs_upward,
            srcs = upward_needs,
            outs = [needs_upward + "/needs.json"],
            cmd = merge_command,
            tools = [Label("//scripts_bazel:merge_needs_json")],
            visibility = visibility,
            tags = ["manual"],
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
        bundles = [],
        upward_bundles = [],
    ):
    """Creates all targets related to documentation.

    By using this function, you'll get any and all updates for documentation targets in one place.

    Args:
      source_dir: The source directory containing documentation files. Defaults to "docs".
      project: optional project name, prefer setting this here if you can avoid having a conf.py
      project_url: Optional project URL, prefer setting this here if you can avoid having a conf.py
      data: Additional files needed by the project-level documentation build.
        These files are outside any bundle and have no bundle mount path. If a
        file should travel with rendered or composable documentation, declare
        it in a `docs_bundle` and place that bundle through `bundles` instead.
        Generated documentation and assets are not staged into the workspace
        source tree for `bazel run`; use a data-only `docs_bundle` for those.
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
                 file instead of the default metamodel shipped with score_metamodel. The same
                 metamodel is bound to the host source bundle created by this macro.
      upward_bundles: docs_bundle targets in the documentation hierarchy above the
                      host's own source bundle. Their Needs are available while
                      processing the host sources and in the final composed Needs build.
      bundles: List of placement dicts describing documentation bundles to overlay
              into this documentation's source tree. Each entry is a dict
                {
                    "bundle": <docs_bundle label>,
                    "mount_at": <where it shall me mounted>,
                    "attach_to": <optional, file where the bundle shall be attached, defaults to the parent section's index>,
                }.
              Note: a bundle label may also point at another module's auto-exposed
              bundle, e.g. "@score_process_description//:docs_bundle".

    The short rule is about ownership and placement, not build availability:
    use a bundle for anything that should travel as one portable mount. A
    bundle may be data-only when its deliverable is generated/supporting data
    rather than source RST. Use ``docs(data = [...])`` only for project-level
    inputs that do not belong to a bundle mount.
    """
    # HINT: keep documentation sync docs/reference/bazel_macros.rst

    upward_needs = [_bundle_upward_needs_label(bundle) for bundle in upward_bundles]
    all_external_needs = external_needs + upward_needs
    all_external_needs_sources = [
        _external_needs_label(label)
        for label in all_external_needs
    ]
    data_sources = [str(label) for label in data]

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

    data_library_label_for_sphinx_docs = []
    if data:
        # ``docs_bundle`` can carry data, including as a pure-data bundle. That
        # data belongs to the bundle payload and is resolved at its eventual
        # mount. These ``docs(data = [...])`` inputs are intentionally
        # project-level instead: they support the project build or its
        # literalinclude examples and are not assigned to a bundle mount. Both
        # kinds of data are build inputs; without the staging below, project-
        # level inputs would
        # remain only execution inputs for Sphinx's tools rather than files
        # below Sphinx's source directory, where standard ``literalinclude``
        # looks for them.
        #
        # ``sphinx_docs_library`` is the generic rules_python/rules_sphinxdocs
        # mechanism for adding such files to the sandboxed needs source tree.
        # Preserve their workspace-relative paths so one ordinary
        # literalinclude works in that Sphinx action. The interactive run
        # target reads the workspace source tree directly; generated files
        # belong in a data-only docs_bundle instead.
        sphinx_docs_library(
            name = "_docs_data",
            srcs = data,
            strip_prefix = "",
        )
        data_library_label_for_sphinx_docs = [":_docs_data"]

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

    # Keep the host's own source bundle separate from the composed bundle.
    # Child bundle Needs exports use this source target as their upward
    # interface; the public bundle remains the complete source tree consumed
    # by Sphinx and docs_check. The public docs_source_bundle alias below is
    # the stable cross-package name for this source-level target.
    docs_bundle(
        name = "_docs_source_bundle",
        source_dir = source_dir,
        entry_doc = "index",
        metamodel = metamodel,
        bundle_conf = sphinx_config,
        scan_code = scan_code,
        code_targets = code_targets,
        upward_bundles = upward_bundles,
        visibility = ["//visibility:public"],
    )

    # ``_docs_source_bundle`` was the original generated label and is kept for
    # compatibility with existing consumers. Expose a stable public name for
    # the host's own-source hierarchy anchor so cross-module users do not need
    # to depend on a private-looking implementation label.
    native.alias(
        name = "docs_source_bundle",
        actual = ":_docs_source_bundle",
        visibility = ["//visibility:public"],
    )
    if glob_doc_sources(source_dir):
        # A source-bearing host always gets this generated export from
        # docs_bundle(). Use a real output target rather than an alias: the
        # external-needs loader resolves named bundle exports from their
        # runfiles path, and Bazel aliases retain the implementation target's
        # output directory.
        native.genrule(
            name = "docs_source_bundle_needs_upward",
            srcs = [":_docs_source_bundle_needs_upward"],
            outs = ["docs_source_bundle_needs_upward/needs.json"],
            cmd = "cp $(location :_docs_source_bundle_needs_upward) $@",
            visibility = ["//visibility:public"],
        )

    composed_bundles = [{
        "bundle": ":_docs_source_bundle",
        "mount_at": "",
    }] + bundles

    docs_bundle(
        name = "docs_bundle",
        metamodel = metamodel,
        bundles = composed_bundles,
        visibility = ["//visibility:public"],
    )

    sphinx_build_binary(
        name = "sphinx_build",
        visibility = ["//visibility:private"],
        data = data + all_external_needs + metamodel_label + [":docs_bundle"],
        deps = deps,
        tags = ["manual"]
    )

    known_good_label = [known_good] if known_good else []

    # The public bundle carries both the complete source tree and the
    # transitive source-code links of every nested bundle. The own-source
    # bundle is composed above so it can also be used as a private hierarchy
    # interface without depending on mounted children.
    # transitive source-code links of every nested bundle. Sphinx itself only
    # receives the host's direct sources; mounted children are staged by
    # score_mounts so their Needs are not discovered a second time.
    sphinx_sources = bundle_source_files(
        name = "_docs_sphinx_sources",
        # ``docs_bundle`` is the complete composed aggregator in the
        # hierarchy-aware implementation. Its direct sources are therefore
        # the host sources exposed by ``_docs_source_bundle``; mounted child
        # sources must remain supplied through score_mounts.
        bundle = ":_docs_source_bundle",
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
        data + all_external_needs + metamodel_label +
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
        "DATA": str(data_sources),
        "EXTERNAL_NEEDS_FILES": str(all_external_needs_sources),
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

    metamodel_tool = []
    if metamodel:
        metamodel_tool = [
            _create_metamodel_tool("_docs_metamodel", metamodel),
        ]

    sphinx_docs(
        name = "needs_json",
        # Nested bundle sources are mounted by score_mounts. Passing the
        # complete bundle as srcs would also expose those files as raw Sphinx
        # sources and make every nested need appear twice.
        srcs = [sphinx_sources],
        deps = data_library_label_for_sphinx_docs,
        config = sphinx_config,
        extra_opts = [
            "-W",
            "--keep-going",
            "-T",  # show more details in case of errors
            "--jobs",
            "auto",
            "--define=external_needs_source=" + str(data_sources + all_external_needs_sources),
            "--define=score_sourcelinks_json=$(location :sourcelinks_json)",
            "--define=score_source_code_linker_plain_links=1",
        ] + (
            # ``sphinx_docs`` is a sandboxed build action, so it needs the
            # action-input path rather than the runfiles-relative spelling.
            ["--define=mounts_manifest=$(location :_mounts_manifest)"] if bundles else []
        ) + (["--define=score_metamodel_yaml=$(location " + metamodel_tool[0] + ")"] if metamodel else []),
        formats = ["needs"],
        sphinx = ":sphinx_build",
        tools = data + all_external_needs + metamodel_tool + [":sourcelinks_json", ":docs_bundle"] + mounts_manifest_label,
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
