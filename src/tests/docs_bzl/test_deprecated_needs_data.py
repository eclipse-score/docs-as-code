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
"""Coverage for the informational warning on deprecated Needs ``data`` input."""

import pytest

from src.tests.docs_bzl.helpers import run_bazel


@pytest.mark.bazel_cached
def test_needs_in_data_prints_deprecation_info():
    """Loading a docs() package with a Needs target in data prints the INFO."""
    result = run_bazel(
        [
            "query",
            "//src/tests/docs_bzl/scenarios/deprecated_needs_data:docs",
        ]
    )

    output = result.stdout + result.stderr
    assert "INFO: ⚠️ DEPRECATED: Passing a Needs inventory through" in output
    assert "Move it to external_needs = [...] instead." in output
