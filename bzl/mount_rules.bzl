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
"""
Conversion of documentation bundles from Bazel into mount metadata.
"""

load("@score_docs_as_code//:bzl/bundle_rules.bzl", "DocsBundleInfo")

def _source_includes(entry):
    """Return direct Sphinx sources relative to a bundle's mount root."""
    source_root = entry.runtime_path.rstrip("/")
    if source_root.endswith("/."):
        source_root = source_root[:-2]
    source_prefix = source_root + "/"
    includes = []
    for source_file in entry.source_files:
        if not source_file.basename.endswith((".md", ".rst")):
            continue
        if not source_file.short_path.startswith(source_prefix):
            fail("source file %r is outside bundle root %r" % (source_file.short_path, entry.runtime_path))
        includes.append("/" + source_file.short_path[len(source_prefix):])
    if includes:
        return sorted(includes)

    # An empty allowlist disables filtering in sphinx-mounts. Use an impossible
    # path so an asset-only bundle cannot accidentally discover nearby docs.
    return ["/__score_docs_as_code_no_direct_sources__"]

def _entry_json(entry):
    """Serialize one source or data entry for the mounts manifest."""
    return {
        "src_root": entry.src_root,
        "runtime_path": entry.runtime_path,
        "mount_at": entry.mount_at,
        "attach_to": entry.attach_to,
        "entry_doc": entry.entry_doc,
        "external": entry.external,
        "repository": entry.repository,
        "include": _source_includes(entry) if entry.src_root else [],
        "data": [f.path for f in entry.data.to_list()],
        "path_check": entry.path_check,
    }

def _mounts_manifest_impl(ctx):
    """Generate the canonical Sphinx mount manifest."""
    bundle_info = ctx.attr.bundle[DocsBundleInfo]
    entries = bundle_info.entries
    primary_entry = None
    if ctx.attr.primary_bundle:
        primary_entry = ctx.attr.primary_bundle[DocsBundleInfo].own_source_entry

    json_mounts = []
    for entry in entries:
        json_mounts.append(_entry_json(entry))

    out = ctx.actions.declare_file(ctx.label.name + ".json")
    manifest = {"mounts": json_mounts}
    if primary_entry != None:
        manifest["primary_source"] = _entry_json(primary_entry)
    ctx.actions.write(out, json.encode(manifest))
    return [DefaultInfo(files = depset([out]))]

_create_mounts_manifest = rule(
    implementation = _mounts_manifest_impl,
    attrs = {
        "bundle": attr.label(providers = [DocsBundleInfo]),
        "primary_bundle": attr.label(default = None, providers = [DocsBundleInfo]),
    },
    doc = "Writes a Sphinx mount manifest from reusable documentation bundles.",
)

def create_mounts_manifest(name, bundle, primary_bundle = None):
    """Create a Sphinx mount manifest from reusable documentation bundles."""
    _create_mounts_manifest(
        name = name,
        bundle = bundle,
        primary_bundle = primary_bundle,
    )
    return ":" + name
