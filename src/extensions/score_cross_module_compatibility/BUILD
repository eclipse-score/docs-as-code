# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@docs_as_code_hub_env//:requirements.bzl", "all_requirements")
load("//:score_pytest.bzl", "score_pytest")

py_library(
    name = "score_cross_module_compatibility",
    srcs = ["__init__.py"],
    imports = ["."],
    visibility = ["//visibility:public"],
    deps = all_requirements + ["@score_docs_as_code//src/helper_lib"],
)

score_pytest(
    name = "unit_tests",
    srcs = ["tests/test_compatibility.py"],
    pytest_config = "//:pyproject.toml",
    deps = [":score_cross_module_compatibility"],
)
