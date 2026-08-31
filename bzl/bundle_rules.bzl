# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
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
"""Internal Bazel support for composing reusable documentation bundles."""

# `docs_bundle` and `sphinx_docs_library` operate at a similar architectural level:
# both describe reusable, transitively composable collections of documentation sources
# that are later assembled into a Sphinx source tree.

# However, their data models and responsibilities differ significantly.

# `sphinx_docs_library` primarily models file placement. Each library contributes files
# together with a `strip_prefix` and a `prefix`, allowing the final Sphinx rule to map
# every source file to a new location in the generated source tree.

# `docs_bundle` instead models documentation structure at the bundle level. In
# addition to the source files, it propagates information such as:

# * where a bundle is mounted, * which document it is attached to, * which document acts
# as its entry point, * which repository owns its sources, * whether it is an internal
# or external bundle, * and how nested
# bundles are rebased when composed.

# It also performs bundle-specific validation and conflict detection. The propagated unit
# is therefore not just a set of files with path transformations, but a structured
# documentation component with composition semantics.

# Using `sphinx_docs_library` directly would not preserve the metadata required by this
# model. We would need a second provider alongside it and would still have to implement
# most of the bundle traversal, rebasing, validation, and composition logic ourselves.

# Extending `sphinx_docs_library` is also not a good fit. Its provider represents
# individual file mappings, while our provider represents complete mounted bundles. Adding
# the required metadata would therefore not be a small extension of the existing
# abstraction; it would change its propagated unit and its semantics. It would also couple
# SCORE-specific composition rules to the generic `rules_sphinxdocs` implementation.

# We therefore reimplement the relatively small overlapping part—transitive source
# collection—while keeping the richer bundle model explicit and independent.

# The name `docs_bundle` reflects that relationship: it fills the same general role
# as `sphinx_docs_library`, but uses a SCORE-specific data model for composing structured
# documentation bundles.



load("@score_docs_as_code//:bzl/basics.bzl", "join_path")

# Internal data passed between bundle targets and eventually consumed by an
# adapter such as the Sphinx mounts manifest. Users configure bundles through
# `docs_bundle()` and `docs()`; they do not need to reference this provider.
DocsBundleInfo = provider(
    doc = "A documentation bundle with its source and placement metadata.",
    fields = {
        "entries": "Ordered entries, one per source directory, including its final documentation-tree location.",
        "own_source_files": "This bundle's direct source files, excluding nested bundles.",
        "sourcelinks": "Source-code-link JSON files together with their owning repository.",
        "external_runfiles": "Documentation source files from external repositories needed in runfiles.",
        # Bundle-owned generated/supporting files. Both bundle data and
        # docs(data = [...]) are build inputs; unlike host-owned docs data,
        # these are resolved at this bundle's mount (for example, a generated
        # index.rst).
        "data": "Bundle-owned generated/supporting files resolved at the bundle's mount.",
    },
)

CodeTargetSourcesInfo = provider(
    doc = "Source files collected from an implementation target and its dependencies.",
    fields = {
        "sources": "Depset of direct and transitive source files.",
    },
)

def _source_files_from_attributes(ctx):
    """Return files explicitly declared through source or header attributes."""
    source_files = []
    for attribute_name in ["srcs", "hdrs", "textual_hdrs"]:
        if not hasattr(ctx.rule.attr, attribute_name):
            continue
        for source in getattr(ctx.rule.attr, attribute_name):
            if type(source) == "File":
                source_files.append(source)
            else:
                source_files.extend(source[DefaultInfo].files.to_list())
    return source_files

def _collect_code_target_sources_impl(target, ctx):
    """Collect source files from an implementation target and its ``deps`` tree."""
    dependency_sources = []
    if hasattr(ctx.rule.attr, "deps"):
        dependency_sources = [
            dependency[CodeTargetSourcesInfo].sources
            for dependency in ctx.rule.attr.deps
        ]
    return [CodeTargetSourcesInfo(
        sources = depset(
            direct = _source_files_from_attributes(ctx),
            transitive = dependency_sources,
        ),
    )]

_collect_code_target_sources = aspect(
    implementation = _collect_code_target_sources_impl,
    attr_aspects = ["deps"],
    provides = [CodeTargetSourcesInfo],
    doc = "Collects sources recursively through standard implementation dependencies.",
)

def _parent_index_docname(mount_at):
    """Choose the page that links to a bundled subtree by default."""
    parent = mount_at.rsplit("/", 1)[0] if "/" in mount_at else ""
    return join_path(parent, "index")

def _ensure_unique_entries(entries):
    """Reject a source directory reached through more than one bundle path."""
    seen = {}
    for entry in entries:
        key = entry.runtime_path
        if key in seen:
            fail(("bundle conflict: source directory %r is included through more " +
                  "than one bundle path; include every documentation source directory once") % key)
        seen[key] = entry

def _bundle_runtime_path(ctx):
    """Return this bundle source directory's Bazel runtime path.

    Bazel spells a source in an external repository as ``../<repo>/...`` in
    runfiles. Keep that spelling here; ``_bundle_execroot_path`` converts it to
    the corresponding ``external/<repo>/...`` form for build actions.
    """
    source_file = ctx.files.srcs[0].short_path
    external_prefix = ""
    if source_file.startswith("../"):
        path_parts = source_file.split("/")
        external_prefix = path_parts[0] + "/" + path_parts[1] + "/"
    return external_prefix + ctx.attr.strip_prefix.rstrip("/")

def _bundle_execroot_path(runtime_path):
    """Return the execroot-relative spelling of an external runtime path."""
    if runtime_path.startswith("../"):
        return "external/" + runtime_path[3:]
    return runtime_path

def _pure_data_runtime_path(ctx):
    """Return a stable identity for a bundle that has no source directory.

    Pure-data bundles do not use ``runtime_path`` to resolve a source tree;
    their files are resolved from the manifest's ``data`` entries instead.
    Give them a synthetic, label-derived identity so multiple distinct
    pure-data bundles can be composed into one documentation site.
    """
    # Encode the complete label identity so every target gets a stable,
    # distinct synthetic path. In particular, local and external labels remain
    # distinct when both are composed by one consuming project.
    label = str(ctx.label)
    encoded_label = (
        label.replace("%", "%25")
        .replace("@", "%40")
        .replace("/", "%2F")
        .replace(":", "%3A")
    )
    return "__data__/%s" % encoded_label

def _rebase_bundle_entry(entry, mount_at, attach_to):
    """Place a bundle entry below a requested documentation-tree location.

    A bundle's own root has no ``mount_at`` yet. For that root, an omitted
    ``attach_to`` means the parent directory's ``index`` page. Nested entries
    retain their existing attachment and are rebased below ``mount_at``.

    ``data`` is deliberately kept with the entry that declares it. A composed
    bundle may expose several source and data-only entries, each resolving its
    generated files at a different mount. Giving every rebased entry the
    bundle's aggregate data would associate the same file with unrelated
    mounts, so the mounts resolver could select the wrong destination.
    """
    is_bundle_root = not entry.mount_at
    if is_bundle_root:
        rebased_attach_to = attach_to or _parent_index_docname(mount_at)
    else:
        rebased_attach_to = join_path(mount_at, entry.attach_to)

    return struct(
        runtime_path = entry.runtime_path,
        src_root = entry.src_root,
        mount_at = join_path(mount_at, entry.mount_at),
        attach_to = rebased_attach_to,
        entry_doc = entry.entry_doc,
        external = entry.external,
        repository = entry.repository,
        data = entry.data,
        path_check = entry.path_check,
    )

def _entry_with_path_check(entry, path_check):
    """Return an entry with the requested sphinx-mounts confinement mode."""
    return struct(
        runtime_path = entry.runtime_path,
        src_root = entry.src_root,
        mount_at = entry.mount_at,
        attach_to = entry.attach_to,
        entry_doc = entry.entry_doc,
        external = entry.external,
        repository = entry.repository,
        data = entry.data,
        path_check = path_check,
    )

def _has_data_only_entry(entries):
    """Return whether the entries contain a declared pure-data bundle."""
    for entry in entries:
        if not entry.src_root and entry.data.to_list():
            return True
    return False

def _entries_visible_through(ctx, child):
    """Keep an external module's own docs, but not its foreign mounts."""
    entries = child[DocsBundleInfo].entries
    child_repository = child.label.workspace_name
    if child_repository == ctx.label.workspace_name:
        return entries
    return [entry for entry in entries if entry.repository == child_repository]

def _sourcelinks_visible_through(ctx, child):
    """Return source-code links that may cross a module boundary."""
    sourcelinks = child[DocsBundleInfo].sourcelinks
    child_repository = child.label.workspace_name
    if child_repository == ctx.label.workspace_name:
        return sourcelinks
    return [link for link in sourcelinks if link.repository == child_repository]

def _parse_bundle_declaration(bundle):
    """Read one nested-bundle declaration and fill in optional values."""
    if type(bundle) != "dict":
        fail("each bundle declaration must be a dict, got %r" % bundle)

    allowed_keys = ["bundle", "mount_at", "attach_to"]
    unknown = [key for key in bundle if key not in allowed_keys]
    if unknown:
        fail("unknown key(s) %r in %r; allowed keys: %r" %
             (unknown, bundle, allowed_keys))
    if "bundle" not in bundle or "mount_at" not in bundle:
        fail("each entry needs 'bundle' and 'mount_at'; got %r" % bundle)

    mount_at = bundle["mount_at"]
    attach_to = bundle.get("attach_to", "")

    return struct(
        bundle = bundle["bundle"],
        mount_at = mount_at,
        attach_to = attach_to,
    )

def _docs_bundle_impl(ctx):
    """Compose source files and nested bundles into a reusable bundle."""
    entries = []
    own_source_files = []
    own_external_runfiles = []
    own_data = depset(direct = ctx.files.data)
    own_source_entry = None

    if ctx.files.srcs:
        runtime_path = _bundle_runtime_path(ctx)
        external = runtime_path.startswith("../")
        own_source_entry = struct(
            runtime_path = runtime_path,
            # The execution root and runfiles tree spell external repositories
            # differently. Keep both locations so every public docs() target can
            # resolve them in its own context.
            src_root = _bundle_execroot_path(runtime_path),
            mount_at = "",
            attach_to = "",
            entry_doc = ctx.attr.entry_doc,
            external = external,
            repository = ctx.label.workspace_name,
            data = own_data,
            path_check = "off" if own_data.to_list() else "error",
        )
        entries.append(own_source_entry)
        own_source_files.extend(ctx.files.srcs)
        # Local sources are read directly from the workspace by ``bazel run``.
        # Only sources from external repositories must be staged in runfiles.
        if external:
            own_external_runfiles.extend(ctx.files.srcs)
    elif own_data:
        # Pure data bundle: create an entry so the data files appear in the manifest.
        entries.append(struct(
            runtime_path = _pure_data_runtime_path(ctx),
            src_root = "",
            mount_at = "",
            attach_to = "",
            entry_doc = ctx.attr.entry_doc,
            external = False,
            repository = ctx.label.workspace_name,
            data = own_data,
            path_check = "error",
        ))

    child_source_files = []
    child_external_runfiles = []
    sourcelinks = [
        struct(file = source_link, repository = ctx.label.workspace_name)
        for source_link in ctx.files.sourcelinks
    ]
    for index, child in enumerate(ctx.attr.bundles):
        child_entries = _entries_visible_through(ctx, child)
        if own_source_entry != None and _has_data_only_entry(child_entries):
            # Supporting files composed through a data-only child are available
            # to this source tree. sphinx-mounts 0.1.x has no per-file allowlist,
            # so the source entry uses its documented non-confining mode.
            own_source_entry = _entry_with_path_check(own_source_entry, "off")
            entries[0] = own_source_entry
        entries.extend([
            _rebase_bundle_entry(
                entry,
                ctx.attr.bundle_mount_ats[index],
                ctx.attr.bundle_attach_tos[index],
            )
            for entry in child_entries
        ])
        child_source_files.append(child[DefaultInfo].files)
        child_external_runfiles.append(child[DocsBundleInfo].external_runfiles)
        sourcelinks.extend(_sourcelinks_visible_through(ctx, child))

    _ensure_unique_entries(entries)
    all_source_files = depset(
        direct = own_source_files,
        transitive = child_source_files,
    )
    external_runfiles = depset(
        direct = own_external_runfiles,
        transitive = child_external_runfiles,
    )
    all_data = depset(
        transitive = [own_data] + [
            child[DocsBundleInfo].data
            for child in ctx.attr.bundles
        ],
    )
    return [
        DefaultInfo(files = depset(transitive = [all_source_files, all_data])),
        DocsBundleInfo(
            entries = entries,
            own_source_files = depset(direct = own_source_files),
            sourcelinks = sourcelinks,
            external_runfiles = external_runfiles,
            data = all_data,
        ),
    ]

_docs_bundle = rule(
    implementation = _docs_bundle_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "sourcelinks": attr.label_list(allow_files = True),
        "strip_prefix": attr.string(default = ""),
        "entry_doc": attr.string(default = "index"),
        "bundles": attr.label_list(providers = [DocsBundleInfo]),
        "bundle_mount_ats": attr.string_list(),
        "bundle_attach_tos": attr.string_list(),
        "data": attr.label_list(allow_files = True),
    },
    doc = "Internal rule that carries bundle files and their documentation-tree locations.",
)

def create_bundle(name, bundles, srcs = [], sourcelinks = [], strip_prefix = "", entry_doc = "index", data = [], visibility = None, **kwargs):
    """Create a reusable documentation bundle from files and child declarations."""
    parsed_bundles = [_parse_bundle_declaration(declaration) for declaration in bundles]
    _docs_bundle(
        name = name,
        srcs = srcs,
        sourcelinks = sourcelinks,
        strip_prefix = strip_prefix,
        entry_doc = entry_doc,
        bundles = [bundle.bundle for bundle in parsed_bundles],
        bundle_mount_ats = [bundle.mount_at for bundle in parsed_bundles],
        bundle_attach_tos = [bundle.attach_to for bundle in parsed_bundles],
        data = data,
        visibility = visibility,
        **kwargs
    )
    return ":" + name

def _bundle_source_files_impl(ctx):
    """Expose only a bundle's direct sources as a Sphinx source tree."""
    return [DefaultInfo(files = ctx.attr.bundle[DocsBundleInfo].own_source_files)]

_bundle_source_files = rule(
    implementation = _bundle_source_files_impl,
    attrs = {
        "bundle": attr.label(providers = [DocsBundleInfo]),
    },
    doc = "Exposes direct bundle sources without nested bundle sources.",
)

def bundle_source_files(name, bundle, visibility = None):
    """Create a target containing only the direct sources of a bundle."""
    _bundle_source_files(
        name = name,
        bundle = bundle,
        visibility = visibility,
    )
    return ":" + name

def _is_sphinx_source_file(file):
    """Return whether ``file`` is discovered as a normal Sphinx document."""
    return file.basename.endswith(".rst") or file.basename.endswith(".md")

def _bundle_supporting_files_impl(ctx):
    """Expose non-document bundle data for a sandboxed Sphinx source tree."""
    bundle = ctx.attr.bundle[DocsBundleInfo]
    return [DefaultInfo(files = depset(direct = [
        file
        for file in bundle.data.to_list()
        if not _is_sphinx_source_file(file)
    ]))]

_bundle_supporting_files = rule(
    implementation = _bundle_supporting_files_impl,
    attrs = {
        "bundle": attr.label(providers = [DocsBundleInfo]),
    },
    doc = "Exposes non-document data from a complete docs bundle.",
)

def bundle_supporting_files(name, bundle, visibility = None):
    """Create a target that stages bundle payloads without duplicate documents."""
    _bundle_supporting_files(
        name = name,
        bundle = bundle,
        visibility = visibility,
    )
    return ":" + name

def _external_docs_runfiles_impl(ctx):
    """Expose external documentation sources needed under ``bazel run``."""
    bundle = ctx.attr.bundle[DocsBundleInfo]
    return [DefaultInfo(files = depset(
        transitive = [bundle.external_runfiles, bundle.data],
    ))]

_external_docs_runfiles = rule(
    implementation = _external_docs_runfiles_impl,
    attrs = {
        "bundle": attr.label(providers = [DocsBundleInfo]),
    },
    doc = "Internal adapter from a docs bundle to its runtime runfiles.",
)

def external_docs_runfiles(name, bundle, visibility = None):
    """Create a target containing only external bundle sources for ``bazel run``."""
    _external_docs_runfiles(
        name = name,
        bundle = bundle,
        visibility = visibility,
    )
    return ":" + name

def _merge_bundle_sourcelinks_impl(ctx):
    """Merge source-code links propagated by a documentation bundle."""
    sourcelinks = [link.file for link in ctx.attr.bundle[DocsBundleInfo].sourcelinks]
    out = ctx.actions.declare_file(ctx.label.name + ".json")
    args = ctx.actions.args()
    args.add("--output", out.path)
    if ctx.file.known_good:
        args.add("--known_good", ctx.file.known_good.path)
    args.add_all(sourcelinks)
    inputs = [depset(sourcelinks)]
    if ctx.file.known_good:
        inputs.append(depset([ctx.file.known_good]))
    ctx.actions.run(
        executable = ctx.executable._merge_sourcelinks,
        arguments = [args],
        inputs = depset(transitive = inputs),
        outputs = [out],
        mnemonic = "MergeBundleSourcelinks",
    )
    return [DefaultInfo(files = depset([out]))]

_merge_bundle_sourcelinks = rule(
    implementation = _merge_bundle_sourcelinks_impl,
    attrs = {
        "bundle": attr.label(providers = [DocsBundleInfo]),
        "known_good": attr.label(allow_single_file = True),
        "_merge_sourcelinks": attr.label(
            default = Label("//scripts_bazel:merge_sourcelinks"),
            cfg = "exec",
            executable = True,
        ),
    },
)

def merge_bundle_sourcelinks(name, bundle, known_good = None, visibility = None):
    """Create one source-code-link JSON file for a complete docs bundle."""
    _merge_bundle_sourcelinks(
        name = name,
        bundle = bundle,
        known_good = known_good,
        visibility = visibility,
    )

def _code_targets_sourcelinks_impl(ctx):
    """Generate one source-link cache for the implementation targets of a bundle."""
    source_files = depset(transitive = [
        target[CodeTargetSourcesInfo].sources
        for target in ctx.attr.code_targets
    ])
    if not source_files.to_list():
        fail("code_targets must declare source files through filegroups, srcs, hdrs, or textual_hdrs")

    output = ctx.actions.declare_file(ctx.label.name + ".json")
    arguments = ctx.actions.args()
    arguments.add("--output", output.path)
    arguments.add_all(source_files)
    ctx.actions.run(
        executable = ctx.executable._generate_sourcelinks,
        arguments = [arguments],
        inputs = source_files,
        outputs = [output],
        mnemonic = "GenerateCodeTargetSourcelinks",
    )
    return [DefaultInfo(files = depset([output]))]

_code_targets_sourcelinks = rule(
    implementation = _code_targets_sourcelinks_impl,
    attrs = {
        "code_targets": attr.label_list(aspects = [_collect_code_target_sources]),
        "_generate_sourcelinks": attr.label(
            default = Label("//scripts_bazel:generate_sourcelinks"),
            cfg = "exec",
            executable = True,
        ),
    },
    doc = "Generates source-code links from implementation target source files.",
)

def generate_code_target_sourcelinks(name, code_targets, visibility = None):
    """Create a cached source-link JSON file for one documentation bundle."""
    _code_targets_sourcelinks(
        name = name,
        code_targets = code_targets,
        visibility = visibility,
    )
    return ":" + name
