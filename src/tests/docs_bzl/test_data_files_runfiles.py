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

"""Keep the negative source-bundle boundary assertion for the data fixture."""

import pytest

from src.tests.docs_bzl.helpers import run_scenario


@pytest.mark.bazel_slow
def test_explicit_source_bundle_excludes_undeclared_siblings():
    """Expected-output matching intentionally does not cover forbidden extras."""
    result = run_scenario("run", "data_files_runfiles", ":docs")

    undeclared_html = result.build_dir / "isolated_test" / "undeclared.html"

    assert not undeclared_html.exists()
