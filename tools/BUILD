# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

load("@aspect_rules_py//py:defs.bzl", "py_binary")
load("@docs_as_code_hub_env//:requirements.bzl", "requirement")

# Standalone maintenance tools for this repository (as opposed to
# //scripts_bazel, which holds executables invoked by Bazel rules). Not part
# of the public API of this module: visibility is limited to this repo so
# downstream consumers depending on score_docs_as_code via bzlmod cannot pick
# these up as dependencies.
package(default_visibility = ["//:__subpackages__"])

py_binary(
    name = "module_verification_reports",
    srcs = ["module_verification_reports.py"],
    data = ["module_verification_reports.toml"] + glob(
        ["module_verification_reports_goldens/**"],
        allow_empty = True,
    ),
    main = "module_verification_reports.py",
    deps = [
        "//src/helper_lib",
    ],
)

# Bazel's coverage report only lists files that a test imported. This tool adds
# the rest at 0% so untested files are visible, and writes the summary posted on
# pull requests. A py_binary so CI and developers use the locked coverage.py.
py_binary(
    name = "coverage_report",
    srcs = ["coverage_report.py"],
    main = "coverage_report.py",
    deps = [requirement("coverage")],
)
