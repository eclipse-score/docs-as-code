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
load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@docs_as_code_hub_env//:requirements.bzl", "all_requirements")
load("@score_tools//score_pytest:pytest.bzl", "score_pytest")

filegroup(
    name = "all_sources",
    srcs = [
        "__init__.py",
        "report_pie.py",
    ],
    visibility = ["//visibility:public"],
)

py_library(
    # Keep chart drawing independent of template setup: the coverage renderer
    # shares these figures, and template setup enables that renderer's directive.
    name = "report_pie",
    srcs = ["report_pie.py"],
    visibility = ["//src/extensions:__pkg__"],
    deps = all_requirements,
)

py_library(
    name = "score_sphinx_needs_templates",
    srcs = ["__init__.py"],
    data = ["@score_docs_as_code//src/needs_templates:files"],
    visibility = ["//visibility:public"],
    deps = all_requirements + [
        ":report_pie",
        "//src/extensions:score_coverage",
        "@score_docs_as_code//src/helper_lib",
    ],
)

score_pytest(
    name = "unit_tests",
    # The template regression test builds a temporary Sphinx HTML project,
    # so it needs more time than a pure Python unit test.
    size = "medium",
    srcs = [
        "tests/test_needs_templates.py",
        "tests/test_report_pie.py",
    ],
    pytest_config = "//:pyproject.toml",
    deps = [
        ":score_sphinx_needs_templates",
        "//src/extensions/score_metamodel",
    ],
)
