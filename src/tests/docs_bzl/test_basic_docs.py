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
"""basic_docs: the smallest consumer, configured only through docs() arguments."""

import re
from pathlib import Path

import pytest

from src.tests.docs_bzl.helpers import (
    assert_no_compatibility_findings,
    load_needs_json,
    run_scenario,
)

SCENARIO = "basic_docs"


@pytest.fixture(scope="module")
def needs_dir() -> Path:
    result = run_scenario("build", SCENARIO, ":needs_json")
    assert result.artifacts is not None
    return result.artifacts["needs.json"].parent


@pytest.fixture(scope="module")
def build_dir() -> Path:
    return run_scenario("run", SCENARIO, ":docs").build_dir


@pytest.mark.bazel_cached
def test_project_attributes_replace_a_missing_conf_py(needs_dir: Path):
    """Without docs/conf.py, project and project_url come from the macro."""
    data = load_needs_json(needs_dir / "needs.json")

    assert data["project"] == "Basic Test"
    assert data["project_url"] == "https://github.com/eclipse-score/docs-as-code"
    # External consumers cannot use a needs.json with an empty current_version.
    assert data["current_version"], "current_version must be non-empty"


@pytest.mark.bazel_cached
def test_needs_build_reports_no_compatibility_findings(needs_dir: Path):
    assert_no_compatibility_findings(needs_dir)


@pytest.mark.bazel_slow
def test_root_data_file_is_available_to_literalinclude(build_dir: Path):
    """A file passed through docs(data=...) is readable by the rendered pages."""
    html = (build_dir / "index.html").read_text(encoding="utf-8")
    # Syntax highlighting wraps each token in a <span>; compare the plain text.
    text = re.sub(r"<[^>]+>", "", html)

    assert "The root bundle owns this supporting file." in text


@pytest.mark.bazel_slow
def test_docs_build_reports_no_compatibility_findings(build_dir: Path):
    assert_no_compatibility_findings(build_dir)
