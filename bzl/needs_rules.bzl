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
"""Bazel rules for building and resolving local Needs inventories.

The SCORE mount extension exposes bundle inputs directly from the Bazel
execution root. This action therefore provides Sphinx with the project's
primary source directory and the mount manifest. Bundle targets remain
explicit action inputs; a manifest by itself does not make the files named by
that manifest available inside a sandbox.
"""

load(
    "@score_docs_as_code//:bzl/bundle_rules.bzl",
    "DocsBundleInfo",
    "LocalNeedsInfo",
    "sphinx_config_options",
)

# A resolved external-needs manifest records the provider-selected labels and
# carries the corresponding artifacts into both Sphinx's action inputs and the
# interactive command's runfiles.
ExternalNeedsManifestInfo = provider(
    doc = "Resolved external-needs labels and their inventory artifacts.",
    fields = {
        "file": "JSON file containing the resolved inventory labels.",
        "inventory_files": "Depset of inventory artifacts referenced by the manifest.",
    },
)

def _sphinx_docs_impl(ctx):
    """Run Sphinx against the Bazel execution-root source tree."""
    output = ctx.actions.declare_directory(ctx.label.name + "/_build/needs")

    bundle = ctx.attr.bundle[DocsBundleInfo]
    external_needs_manifest = None
    external_needs_files = depset()
    if ctx.attr.external_needs_manifest:
        manifest = ctx.attr.external_needs_manifest[ExternalNeedsManifestInfo]
        external_needs_manifest = manifest.file
        external_needs_files = manifest.inventory_files
    # The bundle owns both the direct inputs and their execution-root-relative
    # source root. Nested sources are provided separately for score_mounts, so
    # local exports retain their bundle ownership.
    if not bundle.own_source_files.to_list():
        fail("Sphinx requires a bundle with direct documentation sources")

    bundle_config = bundle.config
    config_file = ctx.file.config
    if config_file:
        # A checked-in conf.py owns Sphinx configuration. In particular, do
        # not inject the bundle's fallback metamodel because that would
        # override ``score_metamodel_yaml`` configured by conf.py.
        config_options = []
        metamodel_file = ctx.file.score_metamodel_yaml
    else:
        # Serialize the semantic provider values only at the action boundary.
        # ``required_in_id`` is the effective value from the bundle provider;
        # the bundle's root-docs association has already supplied it when this
        # is a child bundle.
        config_options = sphinx_config_options(
            project = bundle_config.project,
            project_url = bundle_config.project_url,
            required_in_id = bundle_config.required_in_id,
        )
        # Configuration-free actions need a concrete metamodel input. Use an
        # explicitly supplied label first, then the bundle's inherited default.
        metamodel_file = ctx.file.score_metamodel_yaml or bundle_config.metamodel
    if not config_file and not config_options:
        fail("Sphinx Needs action requires structured configuration options")
    if not config_file and not metamodel_file:
        fail("Sphinx Needs action requires a metamodel")

    # File labels provide execroot-relative paths for this action's sandbox.
    # Pass them through the environment variables consumed by the CLI; reserve
    # the JSON option list for non-path Sphinx overrides.
    # Encode option lists as JSON so spaces, quotes and '=' survive the
    # environment boundary. A missing config file tells the launcher to use
    # Sphinx's ``-C`` mode; structured configuration then arrives as CLI
    # overrides instead of a generated ``conf.py``.
    env = {
        "ACTION": "build_needs_json",
        "SOURCE_DIRECTORY": bundle.source_dir_execroot_path,
        "OUTPUT_DIRECTORY": output.path,
        "SPHINX_CONFIG_FILE": config_file.path if config_file else "",
        "SPHINX_CONFIG_OPTS": json.encode(config_options),
        "EXTERNAL_NEEDS_LABELS": ctx.attr.external_needs_labels,
        "EXTERNAL_NEEDS_MANIFEST": (
            external_needs_manifest.path if external_needs_manifest else ""
        ),
        "SCORE_SOURCELINKS": (
            ctx.file.score_sourcelinks_json.path if ctx.file.score_sourcelinks_json else ""
        ),
        "MOUNTS_MANIFEST": (
            ctx.file.mounts_manifest.path if ctx.file.mounts_manifest else ""
        ),
        "SCORE_METAMODEL_YAML": metamodel_file.path if metamodel_file else "",
        "SPHINX_EXTRA_OPTS": json.encode(ctx.attr.extra_opts),
    }

    # Data and mounted sources must be present at their execution-root paths.
    # The executable separately carries these labels in its Python runfiles
    # for extensions that locate external inventories through Bazel labels.
    # Manifest labels do not make their artifacts action inputs by themselves,
    # so add the provider's file set explicitly for sandboxed Sphinx builds.
    ctx.actions.run(
        executable = ctx.executable.sphinx,
        env = env,
        inputs = depset(
            [file for file in [
                config_file,
                metamodel_file,
                ctx.file.score_sourcelinks_json,
                ctx.file.mounts_manifest,
                external_needs_manifest,
            ] if file] +
            ctx.files.data + ctx.files.tools,
            transitive = [bundle.own_source_files, external_needs_files],
        ),
        outputs = [output],
        mnemonic = "ScoreNeedsBuild",
        progress_message = "Building Needs inventory for %s" % ctx.label,
    )

    return [DefaultInfo(files = depset([output]))]

sphinx_docs = rule(
    implementation = _sphinx_docs_impl,
    attrs = {
        "bundle": attr.label(providers = [DocsBundleInfo], mandatory = True),
        "config": attr.label(allow_single_file = True),
        "data": attr.label_list(allow_files = True),
        "tools": attr.label_list(allow_files = True),
        # Typed labels let the action pass their execroot paths through the
        # environment contract above and still declare sandbox inputs.
        "score_sourcelinks_json": attr.label(allow_single_file = True),
        "mounts_manifest": attr.label(allow_single_file = True),
        "score_metamodel_yaml": attr.label(allow_single_file = True),
        "external_needs_labels": attr.string(default = "[]"),
        # The resolver checks public providers during analysis and keeps the
        # selected JSON artifacts available to this action.
        "external_needs_manifest": attr.label(
            providers = [ExternalNeedsManifestInfo],
        ),
        "extra_opts": attr.string_list(),
        # The launcher runs on the build host and carries extension runfiles.
        "sphinx": attr.label(cfg = "exec", executable = True, mandatory = True),
    },
    doc = "Private action that builds Needs from declared execution-root inputs.",
)

def _docs_bundle_api_impl(ctx):
    """Forward a composed bundle and publish its optional local inventory."""
    bundle_default = ctx.attr.bundle[DefaultInfo]
    local_needs_provider = None

    if ctx.attr.local_needs:
        # ``allow_single_file`` makes the produced inventory directly
        # available as this typed attribute; source-less aggregators omit it.
        needs_file = ctx.file.local_needs
        local_needs_provider = LocalNeedsInfo(
            file = needs_file,
            label = str(ctx.attr.local_needs.label),
        )

    # The wrapper is the stable public target. Its DocsBundleInfo remains the
    # complete composition, while LocalNeedsInfo points only at this bundle's
    # direct-source export. It does not add that file to DefaultInfo: consumers
    # that import the inventory add it to their own action inputs and runfiles
    # through the resolver below.
    providers = [
        DefaultInfo(
            files = bundle_default.files,
            default_runfiles = bundle_default.default_runfiles,
            data_runfiles = bundle_default.data_runfiles,
        ),
        ctx.attr.bundle[DocsBundleInfo],
    ]
    if local_needs_provider != None:
        providers.append(local_needs_provider)
    return providers

_docs_bundle_api = rule(
    implementation = _docs_bundle_api_impl,
    attrs = {
        "bundle": attr.label(providers = [DocsBundleInfo], mandatory = True),
        "local_needs": attr.label(allow_single_file = True),
    },
    doc = "Public docs_bundle target with its local Needs provider.",
)

def expose_docs_bundle(name, bundle, local_needs = None, visibility = None, **kwargs):
    """Publish the bundle API target that forwards composition and local Needs."""
    _docs_bundle_api(
        name = name,
        bundle = bundle,
        local_needs = local_needs,
        visibility = visibility,
        **kwargs
    )

def _docs_executable_api_impl(ctx):
    """Forward the interactive docs executable and publish its local inventory."""
    cli_default = ctx.attr.cli[DefaultInfo]
    providers = []

    if ctx.attr.local_needs:
        needs_file = ctx.file.local_needs
        providers.append(LocalNeedsInfo(
            file = needs_file,
            label = str(ctx.attr.local_needs.label),
        ))

    # Preserve :docs as the same interactive command. Its Needs artifact stays
    # out of the command's runfiles; external-needs consumers add it through
    # the resolver only when they actually import this target.
    return [DefaultInfo(
        executable = ctx.executable.cli,
        files = cli_default.files,
        default_runfiles = cli_default.default_runfiles,
        data_runfiles = cli_default.data_runfiles,
    )] + providers

_docs_executable_api = rule(
    implementation = _docs_executable_api_impl,
    executable = True,
    attrs = {
        "cli": attr.label(cfg = "target", executable = True, mandatory = True),
        "local_needs": attr.label(allow_single_file = True),
    },
    doc = "Public docs() executable with its local Needs provider.",
)

def expose_docs_executable(name, cli, local_needs = None, visibility = None, tags = None):
    """Publish the interactive docs command together with its local Needs."""
    _docs_executable_api(
        name = name,
        cli = cli,
        local_needs = local_needs,
        visibility = visibility,
        tags = tags,
    )

def _resolve_external_needs_impl(ctx):
    """Validate external-needs targets and write their inventory labels."""
    labels = []
    inventory_files = []
    for target in ctx.attr.external_needs:
        if LocalNeedsInfo in target:
            # Public docs targets advertise the file and its loader label
            # together. The caller never needs to know how either private
            # target is named.
            local_needs = target[LocalNeedsInfo]
            labels.append(local_needs.label)
            inventory_files.append(local_needs.file)
        elif target.label.name in ("needs_json", "needs_json_file"):
            # These two direct inventory targets are the supported escape hatch
            # for producers that do not use docs() or docs_bundle(). Keep the
            # historical directory-valued needs_json label working as well.
            labels.append(str(target.label))
            inventory_files.extend(target[DefaultInfo].files.to_list())
        else:
            fail(
                "external_needs target %s must provide a local Needs inventory " %
                target.label +
                " (for example, a docs() or docs_bundle() target); only " +
                "needs_json and needs_json_file are also accepted",
            )

    # The Python extension still consumes Bazel labels. Resolve providers here
    # once, then write that stable runtime list as a small generated manifest.
    output = ctx.actions.declare_file(ctx.label.name + ".json")
    ctx.actions.write(output, json.encode(labels))
    inventory_file_set = depset(inventory_files)
    runfiles = ctx.runfiles(files = [output] + inventory_files)
    return [
        DefaultInfo(
            files = depset([output]),
            default_runfiles = runfiles,
            data_runfiles = runfiles,
        ),
        ExternalNeedsManifestInfo(
            file = output,
            inventory_files = inventory_file_set,
        ),
    ]

_resolve_external_needs = rule(
    implementation = _resolve_external_needs_impl,
    attrs = {
        "external_needs": attr.label_list(allow_files = True),
    },
    doc = "Resolves external_needs providers into a runtime label manifest.",
)

def resolve_external_needs(name, external_needs, visibility = None, tags = None):
    """Create an analysis-time validator and runtime manifest for external_needs."""
    _resolve_external_needs(
        name = name,
        external_needs = external_needs,
        visibility = visibility,
        tags = tags,
    )
    return ":" + name
