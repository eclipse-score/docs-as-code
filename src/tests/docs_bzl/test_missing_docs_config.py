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

from src.tests.docs_bzl.helpers import repo_root, run_scenario


@pytest.mark.bazel_slow
def test_missing_conf_and_macro_values_fails_analysis():
    scenario_dir = repo_root() / "src/tests/docs_bzl/scenarios/missing_docs_config"
    build_file = scenario_dir / "BUILD"
    fixture = scenario_dir / "BUILD.negative"
    assert not build_file.exists(), (
        "negative test package must not be discovered by //..."
    )

    build_file.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        result = run_scenario(
            "build", "missing_docs_config", ":docs", expect_error=True
        )
    finally:
        build_file.unlink()

    assert "no docs/conf.py found" in result.stderr
    assert "provide both project and project_url" in result.stderr
