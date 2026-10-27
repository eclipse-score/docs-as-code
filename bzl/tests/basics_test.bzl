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

load("@bazel_skylib//lib:partial.bzl", "partial")
load("@bazel_skylib//lib:unittest.bzl", "analysistest", "asserts", "unittest")
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
        ("docs", None, "docs"),
        (None, "docs", "docs"),
        ("", None, ""),
        (None, "", ""),
        ("package/docs", ".", "package/docs"),
        ("package/", None, "package"),
        (None, "docs/", "docs"),
        ("package/", "docs/", "package/docs"),
    ]
    for prefix, rest, expected in cases:
        asserts.equals(env, expected, join_path(prefix, rest))
    return unittest.end(env)

join_path_test = unittest.make(_join_path_test_impl)

def _join_path_none_none_target_impl(ctx):
    """Invoke the invalid input so the analysis test can inspect its failure."""
    join_path(None, None)
    return []

_join_path_none_none_target = rule(
    implementation = _join_path_none_none_target_impl,
)

def _join_path_none_none_test_impl(ctx):
    """Require ``join_path(None, None)`` to fail during analysis."""
    env = analysistest.begin(ctx)
    asserts.expect_failure(env, "join_path requires at least one non-None segment")
    return analysistest.end(env)

join_path_none_none_test = analysistest.make(
    _join_path_none_none_test_impl,
    expect_failure = True,
)

def basics_test_suite(name):
    """Declare the unit-test suite for the basic Starlark helpers."""
    _join_path_none_none_target(
        name = name + "_none_none_target",
        # This target is intentionally invalid; it is consumed only by the
        # analysis test that asserts the expected loading-phase failure.
        tags = ["manual"],
    )
    unittest.suite(
        name,
        join_path_test,
        partial.make(
            join_path_none_none_test,
            target_under_test = ":" + name + "_none_none_target",
        ),
    )
