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

"""Generate a directly executable launcher for the selected native PlantUML."""

def _runfile_path(ctx, file):
    # External files have ../<canonical repository>/... short paths. Files in
    # the main repository instead need its runfiles directory name prepended.
    # Derive this from the resolved artifact so module consumers do not depend
    # on Bazel's generated repository naming scheme.
    if file.short_path.startswith("../"):
        return file.short_path[3:]
    return ctx.workspace_name + "/" + file.short_path

def _plantuml_binary_impl(ctx):
    launcher = ctx.actions.declare_file(ctx.label.name)
    ctx.actions.expand_template(
        template = ctx.file._launcher,
        output = launcher,
        substitutions = {
            "@@PLANTUML_RUNFILE@@": _runfile_path(ctx, ctx.file.binary),
        },
        is_executable = True,
    )

    # Sphinx starts this executable directly, bypassing `bazel run` and the
    # args attribute. Embed the selected artifact's runfiles key in the script
    # and carry its complete native distribution into every consuming target.
    runfiles = ctx.runfiles(files = [ctx.file.binary] + ctx.files.runtime)
    runfiles = runfiles.merge(ctx.attr._runfiles[DefaultInfo].default_runfiles)
    return [DefaultInfo(executable = launcher, runfiles = runfiles)]

_plantuml_binary = rule(
    implementation = _plantuml_binary_impl,
    executable = True,
    attrs = {
        "binary": attr.label(allow_single_file = True, mandatory = True),
        "runtime": attr.label(allow_files = True, mandatory = True),
        "_launcher": attr.label(
            default = Label("//src:plantuml_launcher.sh"),
            allow_single_file = True,
        ),
        "_runfiles": attr.label(default = Label("@bazel_tools//tools/bash/runfiles")),
    },
)

def plantuml_binary(name, visibility = None):
    """Select the native distribution and generate its Sphinx-compatible launcher."""

    # Label objects retain this module's repository when the macro is loaded
    # by a downstream project. Both attributes select the same distribution.
    distributions = {
        Label("//src:plantuml_linux_x86_64"): "@plantuml_native_linux_amd64",
        Label("//src:plantuml_linux_arm64"): "@plantuml_native_linux_arm64",
        Label("//src:plantuml_macos_arm64"): "@plantuml_native_macos_arm64",
        Label("//src:plantuml_windows_x86_64"): "@plantuml_native_windows_amd64",
    }
    _plantuml_binary(
        name = name,
        binary = select({
            platform: Label(repo + "//:plantuml.exe" if "windows" in repo else repo + "//:plantuml")
            for platform, repo in distributions.items()
        }),
        runtime = select({
            platform: Label(repo + "//:runtime")
            for platform, repo in distributions.items()
        }),
        visibility = visibility,
    )
