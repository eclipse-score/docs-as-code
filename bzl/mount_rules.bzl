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

    out = ctx.actions.declare_file(ctx.label.name + ".json")
    ctx.actions.write(out, json.encode({"mounts": json_mounts}))
    return [DefaultInfo(files = depset([out]))]

_composition_manifest = rule(
    implementation = _composition_manifest_impl,
    attrs = {
        "bundle": attr.label(providers = [DocsBundleInfo]),
    },
    doc = "Writes the composition consumed by runtime documentation tools.",
)

def create_composition_manifest(name, bundle, visibility = None):
    """Create a common mount and bundle-metadata manifest."""
    _composition_manifest(
        name = name,
        bundle = bundle,
        visibility = visibility,
    )
    return ":" + name
