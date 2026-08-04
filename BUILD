# *******************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
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

load("//:docs.bzl", "docs")

package(default_visibility = ["//visibility:public"])
exports_files(["pyproject.toml"])

docs(
    external_needs = [
        "@score_process//:needs_json_file",
    ],
    bundles = [
        {
            "bundle": "//src/extensions/score_mounts/docs:concept",
            "mount_at": "concepts/mounts",
        },
        {
            "bundle": "//src/extensions/score_mounts/docs:howto",
            "mount_at": "how-to/mounts",
        },
        {
            "bundle": "//src/extensions/score_mounts/docs:internals",
            "mount_at": "internals/extensions/mounts",
        },
        {
            "bundle": "//src/extensions/score_metamodel/docs:metamodel",
            "mount_at": "reference/metamodel",
            "attach_to": "reference/index",
        },
    ],
    scan_code = [
        "//scripts_bazel:sources",
        "//src:all_sources",
    ],
    source_dir = "docs",
)

# bazel run //:shellcheck
alias(
    name = "shellcheck",
    actual = "@score_devcontainer//tools:shellcheck",
)

# bazel run //:actionlint
alias(
    name = "actionlint",
    actual = "@score_devcontainer//tools:actionlint",
)
