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

"""PlantUML native binary platform toolchains."""

def _plantuml_toolchain_impl(ctx):
    return [platform_common.ToolchainInfo(
        binary = ctx.file.binary,
        runtime = ctx.attr.runtime[DefaultInfo].files,
        windows = ctx.attr.windows,
    )]

plantuml_toolchain = rule(
    implementation = _plantuml_toolchain_impl,
    attrs = {
        "binary": attr.label(allow_single_file = True, mandatory = True, cfg = "exec"),
        "runtime": attr.label(mandatory = True, cfg = "exec"),
        "windows": attr.bool(default = False),
    },
    provides = [platform_common.ToolchainInfo],
)

def declare_plantuml_toolchains():
    """Declare native PlantUML toolchains; register them from MODULE.bazel."""
    variants = [
        ("linux_amd64", "@platforms//os:linux", "@platforms//cpu:x86_64", "@plantuml_native_linux_amd64", "plantuml", False),
        ("linux_arm64", "@platforms//os:linux", "@platforms//cpu:aarch64", "@plantuml_native_linux_arm64", "plantuml", False),
        ("macos_arm64", "@platforms//os:macos", "@platforms//cpu:aarch64", "@plantuml_native_macos_arm64", "plantuml", False),
        ("windows_amd64", "@platforms//os:windows", "@platforms//cpu:x86_64", "@plantuml_native_windows_amd64", "plantuml.exe", True),
    ]

    for name, os_constraint, cpu_constraint, repo, binary, windows in variants:
        toolchain_name = "_plantuml_toolchain_" + name

        plantuml_toolchain(
            name = toolchain_name + "_impl",
            binary = repo + "//:" + binary,
            runtime = repo + "//:runtime",
            windows = windows,
        )
        native.toolchain(
            name = toolchain_name,
            toolchain = ":" + toolchain_name + "_impl",
            toolchain_type = "//src:plantuml_toolchain_type",
            exec_compatible_with = [os_constraint, cpu_constraint],
            target_compatible_with = [os_constraint, cpu_constraint],
        )
