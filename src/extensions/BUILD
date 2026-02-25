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

py_library(
    name = "score_plantuml",
    srcs = ["@score_docs_as_code//src/extensions:score_plantuml.py"],
    imports = ["."],
    visibility = ["//visibility:public"],
    deps = ["@score_docs_as_code//src/helper_lib"],
)
