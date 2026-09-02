# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

load("@docs_as_code_hub_env//:requirements.bzl", "all_requirements")
load("//:score_pytest.bzl", "score_pytest")

score_pytest(
    name = "module_verification_reports_test",
    srcs = ["module_verification_reports_test.py"],
    deps = [
        "//tools:module_verification_reports",
        "//src/helper_lib",
    ] + all_requirements,
    pytest_config = "//:pyproject.toml",
)

score_pytest(
    name = "docs_delta_test",
    srcs = ["docs_delta_test.py"],
    deps = [
        "//tools:docs_delta",
    ] + all_requirements,
    pytest_config = "//:pyproject.toml",
)
