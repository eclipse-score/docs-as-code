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

package(default_visibility = ["//visibility:public"])

py_library(
    name = "schema_export_lib",
    srcs = ["generate_schema.py", "export_data.py"],
    imports = ["."],
    deps = all_requirements,
)

py_binary(
    name = "generate_schema_bin",
    srcs = ["generate_schema.py"],
    main = "generate_schema.py",
    data = ["//src/extensions/score_metamodel:metamodel_yaml"],
    deps = all_requirements,
    visibility = ["//visibility:public"],
)

py_binary(
    name = "export_data_bin",
    srcs = ["export_data.py"],
    main = "export_data.py",
    data = ["//src/extensions/score_metamodel:metamodel_yaml"],
    deps = all_requirements,
    visibility = ["//visibility:public"],
)

py_binary(
    name = "generate_all_bin",
    srcs = ["generate_all.py"],
    main = "generate_all.py",
    data = ["//src/extensions/score_metamodel:metamodel_yaml"],
    deps = all_requirements,
    visibility = ["//visibility:public"],
)

score_pytest(
    name = "unit_tests",
    size = "small",
    srcs = glob(["tests/*.py"]),
    data = ["//src/extensions/score_metamodel:metamodel_yaml"],
    pytest_config = "//:pyproject.toml",
    visibility = ["//visibility:public"],
    deps = [
        ":schema_export_lib",
    ] + all_requirements,
)
