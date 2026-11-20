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


load("@aspect_rules_py//py:defs.bzl", "py_binary", "py_library")
load("@docs_as_code_hub_env//:requirements.bzl", "all_requirements")
load("@score_tools//score_pytest:pytest.bzl", "score_pytest")

py_library(
    name = "harness_lib",
    imports = ["../src/extensions"],
    srcs = [
        "candidates/baseline.py",
        "coverage.py",
        "blocks.py",
        "impact.py",
        "query.py",
        "runner.py",
        "//scripts_bazel:traceability_coverage.py",
    ],
    data = glob(["corpus/**/*.json", "corpus/**/spec.md"]) + [
        "rules.json",
        "blocks.json",
        "trace-schema.json",
        "//scripts_bazel:traceability_metrics_schema.json",
    ],
    visibility = ["//visibility:public"],
    deps = [
        "//scripts_bazel:traceability_gate",
        "//src/extensions/score_metamodel",
    ] + all_requirements,
)

py_binary(
    name = "evaluate",
    srcs = ["runner.py"],
    main = "runner.py",
    deps = [":harness_lib"],
)

py_binary(
    name = "query",
    srcs = ["query.py"],
    main = "query.py",
    deps = [":harness_lib"],
)

score_pytest(
    name = "assurance_harness_test",
    size = "medium",
    srcs = ["tests/harness_test.py"],
    pytest_config = "//:pyproject.toml",
    deps = [":harness_lib"],
)
