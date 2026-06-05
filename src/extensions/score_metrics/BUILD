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
load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@docs_as_code_hub_env//:requirements.bzl", "all_requirements")
load("//:score_pytest.bzl", "score_pytest")

filegroup(
    name = "all_sources",
    srcs = glob(
        [
            "*.py",
        ],
    ),
    visibility = ["//visibility:public"],
)

filegroup(
    name = "tests",
    srcs = glob(
        ["tests/*.py"],
    ),
)

py_library(
    name = "score_metrics",
    srcs = [":all_sources"],
    imports = ["."],
    visibility = ["//visibility:public"],
    # TODO: Figure out if all requirements are needed or if we can break it down a bit
    deps = all_requirements + [
        "@score_docs_as_code//src/helper_lib",
    ],
)

score_pytest(
    name = "score_metrics_test",
    size = "small",
    srcs = glob(["tests/*.py"]),
    pytest_config = "//:pyproject.toml",
    # All requirements already in the library so no need to have it double
    deps = [
        ":score_metrics",
        "@score_docs_as_code//src/extensions/score_metamodel",
        "@score_docs_as_code//src/extensions/score_metamodel:score_metamodel_tests",
    ],
)
