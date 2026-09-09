# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Private Bazel action for building the Needs output in place.

The SCORE mount extension exposes bundle inputs directly from the Bazel
execution root. This action therefore provides Sphinx with the project's
primary source directory and the mount manifest. Bundle targets remain
explicit action inputs; a manifest by itself does not make the files named by
that manifest available inside a sandbox.
"""

load("@score_docs_as_code//:bzl/bundle_rules.bzl", "DocsBundleInfo")

def _sphinx_docs_impl(ctx):
    """Run Sphinx against the Bazel execution-root source tree."""
    output = ctx.actions.declare_directory(ctx.label.name + "/_build/needs")

    bundle = ctx.attr.bundle[DocsBundleInfo]
    # The bundle owns both the direct inputs and their root. Nested sources
    # are provided separately for score_mounts, so local exports retain their
    # bundle ownership. Generated roots already use execution-root paths;
    # external source roots use runfiles spelling and need this translation.
    if not bundle.own_source_files.to_list():
        fail("Sphinx requires a bundle with direct documentation sources")
    source_dir = bundle.own_source_root
    if source_dir.startswith("../"):
        source_dir = "external/" + source_dir[3:]

    # Expand file labels at analysis time, then encode the argument list as
    # JSON so spaces, quotes and '=' in Sphinx options survive the environment
    # transport unchanged. The launcher adds these after its default options.
    env = {
        "ACTION": "build_needs_json",
        "SOURCE_DIRECTORY": source_dir or ".",
        "OUTPUT_DIRECTORY": output.path,
        "SPHINX_CONFIG_FILE": ctx.file.config.path,
        "DATA": "[]",
        "SPHINX_EXTRA_OPTS": json.encode([
            ctx.expand_location(option, targets = ctx.attr.tools)
            for option in ctx.attr.extra_opts
        ]),
    }

    # Data and mounted sources must be present at their execution-root paths.
    # The executable separately carries these labels in its Python runfiles
    # for extensions that locate external inventories through Bazel labels.
    ctx.actions.run(
        executable = ctx.executable.sphinx,
        env = env,
        inputs = depset(
            [ctx.file.config] + ctx.files.data + ctx.files.tools,
            transitive = [bundle.own_source_files],
        ),
        outputs = [output],
        mnemonic = "ScoreNeedsBuild",
        progress_message = "Building Needs inventory for %s" % ctx.label,
    )

    return [DefaultInfo(files = depset([output]))]

sphinx_docs = rule(
    implementation = _sphinx_docs_impl,
    attrs = {
        "config": attr.label(allow_single_file = True, mandatory = True),
        "bundle": attr.label(providers = [DocsBundleInfo], mandatory = True),
        "data": attr.label_list(allow_files = True),
        "tools": attr.label_list(allow_files = True),
        "extra_opts": attr.string_list(),
        # The launcher runs on the build host and carries extension runfiles.
        "sphinx": attr.label(cfg = "exec", executable = True, mandatory = True),
    },
    doc = "Private action that builds Needs from declared execution-root inputs.",
)
