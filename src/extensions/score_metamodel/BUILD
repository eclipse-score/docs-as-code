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

load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@docs_as_code_hub_env//:requirements.bzl", "all_requirements")
load("//:score_pytest.bzl", "score_pytest")

filegroup(
    name = "sources",
    srcs = glob(
        [
            "*.py",
            "*.yaml",
            "*.json",
            "checks/*.py",
        ],
    ),
)

filegroup(
    name = "tests",
    srcs = glob(
        ["tests/*.py"],
    ),
)

filegroup(
    name = "metamodel_yaml",
    srcs = ["metamodel.yaml"],
)

filegroup(
    name = "all_sources",
    srcs = [
        ":sources",
        ":tests",
    ],
    visibility = ["//visibility:public"],
)

py_library(
    name = "score_metamodel",
    srcs = [":sources"],
    imports = ["."],
    visibility = ["//visibility:public"],
    # TODO: Figure out if all requirements are needed or if we can break it down a bit
    deps = all_requirements + [
        "@score_docs_as_code//src/extensions/score_metrics",
        "@score_docs_as_code//src/helper_lib",
    ],
)

score_pytest(
    name = "unit_tests",
    size = "small",
    srcs = glob(
        [
            "tests/*.py",
        ],
        exclude = ["tests/test_rules_file_based.py"],
    ),
    data = ["tests/model/simple_model.yaml"],
    pytest_config = "//:pyproject.toml",
    visibility = ["//visibility:public"],
    deps = [":score_metamodel"],
)

score_pytest(
    name = "file_based_tests_architecture",
    srcs = ["tests/test_rules_file_based.py"],
    data = glob(["tests/rst/architecture/*.rst"]) + [
        "tests/__init__.py",
        "tests/rst/conf.py",
        "tests/rst/needs.json",
    ],
    pytest_config = "//:pyproject.toml",
    deps = [":score_metamodel"],
)

score_pytest(
    name = "file_based_tests_attributes",
    srcs = ["tests/test_rules_file_based.py"],
    data = glob(["tests/rst/attributes/*.rst"]) + [
        "tests/__init__.py",
        "tests/rst/conf.py",
        "tests/rst/needs.json",
    ],
    pytest_config = "//:pyproject.toml",
    deps = [":score_metamodel"],
)

score_pytest(
    name = "file_based_tests_graph",
    srcs = ["tests/test_rules_file_based.py"],
    data = glob(["tests/rst/graph/*.rst"]) + [
        "tests/__init__.py",
        "tests/rst/conf.py",
        "tests/rst/needs.json",
    ],
    pytest_config = "//:pyproject.toml",
    deps = [":score_metamodel"],
)

score_pytest(
    name = "file_based_tests_id_contains_feature",
    srcs = ["tests/test_rules_file_based.py"],
    data = glob(["tests/rst/id_contains_feature/*.rst"]) + [
        "tests/__init__.py",
        "tests/rst/conf.py",
        "tests/rst/needs.json",
    ],
    pytest_config = "//:pyproject.toml",
    deps = [":score_metamodel"],
)

score_pytest(
    name = "file_based_tests_options",
    srcs = ["tests/test_rules_file_based.py"],
    data = glob(["tests/rst/options/*.rst"]) + [
        "tests/__init__.py",
        "tests/rst/conf.py",
        "tests/rst/needs.json",
    ],
    pytest_config = "//:pyproject.toml",
    deps = [":score_metamodel"],
)
