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
"""external_bundle: a docs() site mounts a bundle from another Bazel module."""

from pathlib import Path

import pytest

from src.tests.docs_bzl.helpers import (
    assert_no_compatibility_findings,
    run_scenario,
    toctree_links,
)

SCENARIO = "external_bundle"
MOUNT = "process"


@pytest.fixture(scope="module")
def build_dir() -> Path:
    return run_scenario("run", SCENARIO, ":docs").build_dir


@pytest.mark.bazel_slow
def test_external_bundle_is_rendered_at_its_mount_point(build_dir: Path):
    """@score_process_description//:docs_bundle lands below mount_at = "process"."""
    assert (build_dir / MOUNT / "index.html").is_file()


@pytest.mark.bazel_slow
def test_host_page_links_the_external_bundle(build_dir: Path):
    """Without attach_to, the bundle is linked from the host's root toctree."""
    assert toctree_links(build_dir / "index.html") == [f"{MOUNT}/index.html"]


@pytest.mark.bazel_slow
def test_docs_build_reports_no_compatibility_findings(build_dir: Path):
    assert_no_compatibility_findings(build_dir)


@pytest.mark.bazel_cached
def test_needs_build_reports_no_compatibility_findings():
    result = run_scenario("build", SCENARIO, ":needs_json")
    assert result.artifacts is not None

    assert_no_compatibility_findings(result.artifacts["needs.json"].parent)
