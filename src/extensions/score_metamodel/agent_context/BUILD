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
load("//:score_pytest.bzl", "score_pytest")

py_library(
    name = "agent_context_generator",
    srcs = ["generate_agent_context.py"],
    imports = ["."],
    deps = all_requirements,
)

# Public so other repositories can consume the generated projection.
py_binary(
    name = "generate_agent_context_bin",
    srcs = ["generate_agent_context.py"],
    data = ["//src/extensions/score_metamodel:metamodel_yaml"],
    main = "generate_agent_context.py",
    visibility = ["//visibility:public"],
    deps = all_requirements,
)

score_pytest(
    name = "unit_tests",
    size = "small",
    srcs = glob(["tests/*.py"]),
    data = [
        "tests/model/nested_model.yaml",
        "tests/model/precedence_model.yaml",
        "tests/model/simple_expected.json",
        "tests/model/simple_model.yaml",
        "//src/extensions/score_metamodel:metamodel_yaml",
    ],
    pytest_config = "//:pyproject.toml",
    visibility = ["//visibility:public"],
    deps = [":agent_context_generator"],
)
