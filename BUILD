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

exports_files([
    "pyproject.toml",
])

docs(
    bundles = [
        {
            "bundle": "//src/extensions/docs:extensions",
            "mount_at": "internals/extensions",
        },
        {
            "bundle": "//src/extensions/score_metamodel/docs:metamodel",
            "mount_at": "reference/metamodel",
            "attach_to": "reference/index",
        },
    ],
    code_targets = [
        "//scripts_bazel:sources",
        "//tools:module_verification_reports",
        "//src:all_sources",
    ],
    external_needs = [
        "@score_process_description//:needs_json_file",
    ],
    project = "S-CORE Docs-as-Code",
    project_url = "https://eclipse-score.github.io/docs-as-code",
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

# gallery for the standalone module verification report.
alias(
    name = "module_verification_reports",
    actual = "//tools:module_verification_reports",
)
