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
"""Verify that data files (e.g. genrule outputs) are reachable at runtime."""

from src.tests.docs_bzl.helpers import run_scenario


def test_data_files_reachable_at_runtime():
    """Data files from genrule must be in runfiles and resolved by Sphinx."""
    result = run_scenario("run", "data_files_runfiles", ":docs")

    index_html = result.build_dir / "index.html"

    assert "Data RST Title" in index_html.read_text(encoding="utf-8")
