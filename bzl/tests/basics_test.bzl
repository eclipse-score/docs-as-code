# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Unit tests for the small Starlark helpers in ``bzl/basics.bzl``."""

load("@bazel_skylib//lib:unittest.bzl", "asserts", "unittest")
load("//:bzl/basics.bzl", "join_path")

def _join_path_test_impl(ctx):
    """Check path joining and normalization at the Starlark level."""
    env = unittest.begin(ctx)
    # Each tuple contains ``prefix``, ``rest``, and the expected result.
    cases = [
        ("docs", "index", "docs/index"),
        ("", "docs", "docs"),
        (".", "docs", "docs"),
        ("docs", "", "docs"),
        ("package/docs", ".", "package/docs"),
        ("package/", "docs/", "package/docs"),
    ]
    for prefix, rest, expected in cases:
        asserts.equals(env, expected, join_path(prefix, rest))
    return unittest.end(env)

join_path_test = unittest.make(_join_path_test_impl)

def basics_test_suite(name):
    """Declare the unit-test suite for the basic Starlark helpers."""
    unittest.suite(name, join_path_test)
