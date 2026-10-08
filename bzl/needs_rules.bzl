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

load(
    "@score_docs_as_code//:bzl/bundle_rules.bzl",
    "DocsBundleInfo",
    "sphinx_config_options",
)

# The Sphinx action's environment is the fixed dict built in _sphinx_docs_impl,
# so `--action_env` cannot switch coverage on inside it; these string flags
# carry the coverage.py settings in instead. An own minimal rule instead of
# bazel_skylib's string_flag: skylib is only a dev dependency of this module,
# so consumers could not load it.
PythonCoverageSettingInfo = provider(
    doc = "A coverage.py setting forwarded to the Sphinx Needs action.",
    fields = ["value"],
)

def _python_coverage_setting_impl(ctx):
    return [PythonCoverageSettingInfo(value = ctx.build_setting_value)]

python_coverage_setting = rule(
    implementation = _python_coverage_setting_impl,
    build_setting = config.string(flag = True),
    doc = "String flag holding one coverage.py environment value; empty disables it.",
)

def _sphinx_docs_impl(ctx):
    """Run Sphinx against the Bazel execution-root source tree."""
    output = ctx.actions.declare_directory(ctx.label.name + "/_build/needs")

    bundle = ctx.attr.bundle[DocsBundleInfo]
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
        "SCORE_SOURCELINKS": (
            ctx.file.score_sourcelinks_json.path if ctx.file.score_sourcelinks_json else ""
        ),
        "MOUNTS_MANIFEST": (
            ctx.file.mounts_manifest.path if ctx.file.mounts_manifest else ""
        ),
        "SCORE_METAMODEL_YAML": metamodel_file.path if metamodel_file else "",
        "SPHINX_EXTRA_OPTS": json.encode(ctx.attr.extra_opts),
    }

    # The docs.bzl scenario tests measure the code Sphinx runs in this action;
    # the hook in src/docs_cli/cli.py reads these variables. Only add them when
    # the flags are set, so normal builds keep their environment and with it
    # their cache keys.
    execution_requirements = {}
    coverage_process_start = ctx.attr._coverage_process_start[PythonCoverageSettingInfo].value
    if coverage_process_start:
        env["COVERAGE_PROCESS_START"] = coverage_process_start
        env["COVERAGE_FILE"] = ctx.attr._coverage_file[PythonCoverageSettingInfo].value
        # The coverage data file is not a declared output. A cache hit would
        # restore the Needs output without running Sphinx, and the scenario
        # would silently drop out of the coverage report.
        execution_requirements["no-cache"] = "1"

    # Data and mounted sources must be present at their execution-root paths.
    # The executable separately carries these labels in its Python runfiles
    # for extensions that locate external inventories through Bazel labels.
    ctx.actions.run(
        executable = ctx.executable.sphinx,
        env = env,
        inputs = depset(
            [file for file in [
                config_file,
                metamodel_file,
                ctx.file.score_sourcelinks_json,
                ctx.file.mounts_manifest,
            ] if file] +
            ctx.files.data + ctx.files.tools,
            transitive = [bundle.own_source_files],
        ),
        outputs = [output],
        execution_requirements = execution_requirements,
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
        "extra_opts": attr.string_list(),
        # The launcher runs on the build host and carries extension runfiles.
        "sphinx": attr.label(cfg = "exec", executable = True, mandatory = True),
        # A rule can only read a flag's value through an attribute.
        "_coverage_file": attr.label(default = Label("//src/docs_cli:__internal__.coverage_file")),
        "_coverage_process_start": attr.label(
            default = Label("//src/docs_cli:__internal__.coverage_process_start"),
        ),
    },
    doc = "Private action that builds Needs from declared execution-root inputs.",
)
