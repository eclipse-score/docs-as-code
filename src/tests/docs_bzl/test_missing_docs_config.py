# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Validation of docs() configuration fallback."""

import pytest

from src.tests.docs_bzl.helpers import run_negative_scenario


@pytest.mark.bazel_slow
def test_missing_conf_and_macro_values_fails_analysis():
    result = run_negative_scenario("missing_docs_config", ":docs")

    assert "no docs/conf.py found" in result.stderr
    assert "provide both project and project_url" in result.stderr
