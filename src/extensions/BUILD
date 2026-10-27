# *******************************************************************************
# Copyright (c) 2024 Contributors to the Eclipse Foundation
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

load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@docs_as_code_hub_env//:requirements.bzl", "all_requirements")
load("@score_tools//score_pytest:pytest.bzl", "score_pytest")

py_library(
    name = "score_plantuml",
    srcs = ["@score_docs_as_code//src/extensions:score_plantuml.py"],
    imports = ["."],
    visibility = ["//visibility:public"],
    deps = ["@score_docs_as_code//src/helper_lib"],
)

py_library(
    name = "broken_link_fix",
    srcs = ["@score_docs_as_code//src/extensions:broken_link_fix.py"],
    imports = ["."],
    visibility = ["//visibility:public"],
    deps = ["@score_docs_as_code//src/helper_lib"],
)

# Coverage rendering reads prepared JSON and shares the verification report's
# chart drawing code so both displays use the same figure sizing and styling.
py_library(
    name = "score_coverage",
    srcs = ["score_coverage.py"],
    imports = ["."],
    visibility = ["//visibility:public"],
    deps = all_requirements + [
        "//src/extensions/score_sphinx_needs_templates:report_pie",
    ],
)

score_pytest(
    name = "score_coverage_test",
    srcs = ["score_coverage_test.py"],
    pytest_config = "//:pyproject.toml",
    deps = [
        ":score_coverage",
        "//src/extensions/score_sphinx_needs_templates",
    ],
)
