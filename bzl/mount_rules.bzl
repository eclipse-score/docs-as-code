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

def _composition_manifest_impl(ctx):
    """Generate the bundle composition manifest."""
    bundle_info = ctx.attr.bundle[DocsBundleInfo]
    entries = bundle_info.entries

    json_mounts = []
    for entry in entries:
        # A standalone bundle's Needs action must see only the entries it owns.
        # Composed documentation still receives every entry through the normal
        # manifest, so this filter changes only the manifest view requested by
        # the caller.
        if ctx.attr.own_only and not entry.root_bundle:
            continue
        mount = {
            "src_root": entry.src_root,
            "runtime_path": entry.runtime_path,
            "mount_at": entry.mount_at,
            "attach_to": entry.attach_to,
            "toctree_index": entry.toctree_index,
            "entry_doc": entry.entry_doc,
            "external": entry.external,
            "repository": entry.repository,
            # Tell the runtime resolver whether src_root is a generated output
            # tree rather than a workspace or external-repository directory.
            "generated": entry.generated,
            "data": [f.path for f in entry.data.to_list()],
            # Keep identity and direct-target metadata in the same manifest as
            # placement so all runtime consumers use one composition snapshot.
            "root_bundle": entry.root_bundle,
            "bundle": {
                "label": entry.bundle_label,
                "name": entry.bundle_name,
                # This explicit ID identifies the primary Need represented by
                # the bundle. It is intentionally independent of the Bazel
                # target name and of any other Need IDs in the bundle.
                "primary_need_id": entry.primary_need_id,
                # Each direct target contributes its Bazel label and rule kind
                # to the bundle metadata consumed by Python.
                "code_targets": [
                    {
                        "label": target.label,
                        "type": target.type,
                    }
                    for target in entry.code_targets
                ],
            },
        }
        # Explicit source targets are mounted as a file allowlist. Directory
        # bundles omit this key and retain the existing recursive behavior.
        if entry.files:
            mount["files"] = entry.files
        json_mounts.append(mount)

    # Assets are copied only into the composed HTML output, so the local
    # Needs view never lists them. Only paths are written here: the manifest
    # action does not build the asset files themselves.
    json_assets = [] if ctx.attr.own_only else [
        {
            "path": asset_file.path,
            "destination": asset.destination,
            # A directory output (for example Doxygen HTML) is one File whose
            # contents are copied below the destination.
            "is_directory": asset_file.is_directory,
        }
        for asset in bundle_info.assets
        for asset_file in asset.files.to_list()
    ]

    out = ctx.actions.declare_file(ctx.label.name + ".json")
    ctx.actions.write(out, json.encode({"mounts": json_mounts, "assets": json_assets}))
    return [DefaultInfo(files = depset([out]))]

_composition_manifest = rule(
    implementation = _composition_manifest_impl,
    attrs = {
        "bundle": attr.label(providers = [DocsBundleInfo]),
        # ``own_only`` creates the local view used by a bundle's standalone
        # Needs export; the default keeps the complete composition unchanged.
        "own_only": attr.bool(default = False),
    },
    doc = "Writes the bundle composition consumed by runtime documentation tools.",
)

def create_composition_manifest(name, bundle, own_only = False, visibility = None):
    """Create a mount manifest for composed builds or local Needs document mapping."""
    _composition_manifest(
        name = name,
        bundle = bundle,
        own_only = own_only,
        visibility = visibility,
    )
    return ":" + name
