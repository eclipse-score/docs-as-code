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

def _mounts_manifest_impl(ctx):
    """Generate the canonical Sphinx mount manifest."""
    bundle_info = ctx.attr.bundle[DocsBundleInfo]
    entries = bundle_info.entries

    json_mounts = []
    for entry in entries:
        json_mounts.append({
            "src_root": entry.src_root,
            "runtime_path": entry.runtime_path,
            "mount_at": entry.mount_at,
            "attach_to": entry.attach_to,
            "entry_doc": entry.entry_doc,
            "external": entry.external,
            "repository": entry.repository,
            "data": [f.path for f in entry.data.to_list()],
        })

    out = ctx.actions.declare_file(ctx.label.name + ".json")
    ctx.actions.write(out, json.encode({"mounts": json_mounts}))
    return [DefaultInfo(files = depset([out]))]

_create_mounts_manifest = rule(
    implementation = _mounts_manifest_impl,
    attrs = {
        "bundle": attr.label(providers = [DocsBundleInfo]),
    },
    doc = "Writes a Sphinx mount manifest from reusable documentation bundles.",
)

def create_mounts_manifest(name, bundle):
    """Create a Sphinx mount manifest from reusable documentation bundles."""
    _create_mounts_manifest(
        name = name,
        bundle = bundle,
    )
    return ":" + name

def _bundle_target_manifest_impl(ctx):
    """Write the code targets associated with each documentation-tree subtree."""
    mappings = []
    for entry in ctx.attr.bundle[DocsBundleInfo].entries:
        if entry.code_targets:
            mappings.append({
                "mount_at": entry.mount_at,
                "targets": [
                    {"bazel_target": target.label, "bazel_type": target.type}
                    for target in entry.code_targets
                ],
            })
    out = ctx.actions.declare_file(ctx.label.name + ".json")
    ctx.actions.write(out, json.encode({"mappings": mappings}))
    return [DefaultInfo(files = depset([out]))]

_bundle_target_manifest = rule(
    implementation = _bundle_target_manifest_impl,
    attrs = {"bundle": attr.label(providers = [DocsBundleInfo])},
    doc = "Writes Bazel target metadata associated with documentation bundles.",
)

def create_bundle_target_manifest(name, bundle):
    _bundle_target_manifest(name = name, bundle = bundle)
    return ":" + name
