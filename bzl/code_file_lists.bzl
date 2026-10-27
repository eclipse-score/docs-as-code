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
"""Export composed bundles' code-file lists for coverage attribution."""

load("@score_docs_as_code//:bzl/bundle_rules.bzl", "DocsBundleInfo")

def _file_identity(file):
    """Export Bazel's repository-relative identity for a code artifact.

    short_path spells an external file as ../<canonical repo>/<path>, even
    when the file is generated. The path inside that repository is independent
    of the host execroot and of the documentation bundle mounting the file.
    """
    path = file.short_path
    if path.startswith("../"):
        repository, _, path = path[3:].partition("/")
    else:
        repository = "_main"
    # short_path already omits the configuration root for generated outputs.
    return struct(repository = repository, path = path)

def _code_file_lists_impl(ctx):
    """Export code-file identities and primary Need IDs from composed bundles.

    Membership comes from the bounded file sets shared with source links. Only
    identities enter this JSON, so source edits that preserve membership leave
    the exported file lists unchanged. Bundle entries retain each file set's
    ownership as children are mounted into a parent.
    """
    code_file_lists = {}
    for entry in ctx.attr.bundle[DocsBundleInfo].entries:
        # A primary Need belongs to this bundle's own documentation. Pure
        # aggregators and data-only entries provide no local Need declarations.
        # The metamodel validates the actual ID against those own documents.
        if not entry.primary_need_id or not entry.src_root:
            continue
        if entry.primary_need_id in code_file_lists:
            fail("primary Need ID %s belongs to multiple bundles: %s and %s" % (
                entry.primary_need_id,
                code_file_lists[entry.primary_need_id]["bundle"],
                entry.bundle_label,
            ))
        files = {}
        for file in entry.code_files.to_list():
            identity = _file_identity(file)
            files[(identity.repository, identity.path)] = {
                "repository": identity.repository,
                "path": identity.path,
            }
        code_file_lists[entry.primary_need_id] = {
            "primary_need_id": entry.primary_need_id,
            "bundle": entry.bundle_label,
            "files": [files[key] for key in sorted(files)],
        }
    out = ctx.actions.declare_file(ctx.label.name + ".json")
    ctx.actions.write(out, json.encode({
        "version": 1,
        "code_file_lists": [code_file_lists[key] for key in sorted(code_file_lists)],
    }) + "\n")
    return [DefaultInfo(files = depset([out]))]

_code_file_lists = rule(
    implementation = _code_file_lists_impl,
    attrs = {"bundle": attr.label(mandatory = True, providers = [DocsBundleInfo])},
)

def declare_code_file_lists(name, bundle):
    """Export a bundle's composed file identities as a private JSON target."""
    _code_file_lists(
        name = name,
        bundle = bundle,
        visibility = ["//visibility:private"],
        tags = ["manual"],
    )
    return ":" + name
