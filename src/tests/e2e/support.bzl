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
load("//:score_pytest.bzl", "score_pytest")

def e2e_test(name, srcs, source_dir, data, deps = [], env = {}):
    """Helper function to define an end-to-end test for docs().

    Args:
        name: The name of the test target.
        srcs: The source files for the test (python files).
        source_dir: The source directory for the docs.
        data: The data dependencies for the test.
        deps: The dependencies for the test.
        env: The environment variables for the test.
    """
    score_pytest(
        name = name,
        size = "medium",
        srcs = srcs,
        data = data + [
            # provide the actual target to pytest for execution,
            # since `bazel test` would have created it, but not executed it.
            # pytest will run it directly.
            ":docs",

            # provide generated artifacts to pytest, so that they can be verified.
            ":sourcelinks_json",
        ],
        deps = deps + ["//src/tests/e2e:e2e_support"],
        env = {
            "DOCS_BINARY": "$(rootpath :docs)",
            "SOURCE_DIR": source_dir,
        },
    )
