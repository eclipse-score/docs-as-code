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

score_pytest(
    name = "test",
    size = "large",
    srcs = [
        "conftest.py",
        "test_consumer.py",
    ],
    data = [],
    deps = [],
    env = {},

    # These tests are huge, don't run them on //...
    tags = ["manual"]
)
