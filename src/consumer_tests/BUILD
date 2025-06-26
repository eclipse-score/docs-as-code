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

load("@aspect_rules_py//py:defs.bzl", "py_binary", "py_library", "py_test")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "consumer_tester",
    srcs = ["consumer_tester.py"],
    visibility = ["//visibility:public"],
)

py_binary(
    name = "run_consumer_tests",
    srcs = ["consumer_tester.py"],
    main = "consumer_tester.py",
    visibility = ["//visibility:public"],
)

py_test(
    name = "test_consumer_regression",
    srcs = ["test_consumer_regression.py"],
    deps = [":consumer_tester"],
    # Mark as manual since these are integration tests that require network access
    tags = ["manual", "integration", "requires-network"],
    # Set a longer timeout since these tests clone repositories and run builds
    timeout = "long",  # 15 minutes
    size = "large",
    visibility = ["//visibility:public"],
)