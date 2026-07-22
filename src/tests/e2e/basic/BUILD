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

load("@score_docs_as_code//:docs.bzl", "docs")
load("@score_docs_as_code//src/tests/e2e:support.bzl", "e2e_test")

docs(
    source_dir = "docs",
)

e2e_test(
    name = "test",
    srcs = ["test.py"],

    # source_dir must be passed redundantly here, so that the test can access the docs source files.
    source_dir = "docs",

    # docs must be passed redundantly here as a data dependency.
    data = glob(["docs/**/*"]),
)
