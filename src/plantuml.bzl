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

plantuml_binary = rule(
    implementation = _plantuml_binary_impl,
    executable = True,
    doc = "Generate a directly executable launcher with the selected native distribution in runfiles.",
    attrs = {
        "binary": attr.label(
            allow_single_file = True,
            mandatory = True,
            doc = "Native executable; its artifact determines the embedded runfiles key.",
        ),
        "runtime": attr.label(
            allow_files = True,
            mandatory = True,
            doc = "Complete matching distribution, including shared libraries and resources.",
        ),
        "_launcher": attr.label(
            default = Label("//src:plantuml_launcher.sh"),
            allow_single_file = True,
        ),
        "_runfiles": attr.label(default = Label("@bazel_tools//tools/bash/runfiles")),
    },
)
