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
load("//:docs.bzl", "docs")
load("//:score_pytest.bzl", "score_pytest")

py_library(
    name = "e2e_support",
    srcs = ["support.py"],
    imports = ["."],
    visibility = ["//visibility:public"],
)

docs(
    source_dir = "host_docs",
)

score_pytest(
    name = "docs_e2e_test",
    size = "medium",
    srcs = ["test_docs_e2e.py"],
    data = [
        ":docs",
        ":sourcelinks_json",
        "host_docs/conf.py",
        "host_docs/index.rst",
    ],
    deps = [":e2e_support"],
    env = {
        "DOCS_BINARY": "$(rootpath :docs)",
        "DOCS_CONF": "$(rootpath host_docs/conf.py)",
        "SOURCELINKS": "$(rootpath :sourcelinks_json)",
    },
    pytest_config = "//:pyproject.toml",
)
