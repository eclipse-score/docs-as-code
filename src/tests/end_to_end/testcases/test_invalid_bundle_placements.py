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

# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
# *******************************************************************************
"""Invalid docs_bundle() placement scenario."""

import pytest

from src.tests.end_to_end.testcases.helpers import SCENARIOS_ROOT, run_scenario

BUNDLE_CONFLICT = (
    'bundle conflict: source directory "scenarios/invalid_bundle_placements/child" '
    "is included through more than one bundle path"
)


@pytest.mark.bazel_slow
def test_bundle_reached_at_two_mount_points_is_rejected():
    """The same child below two different wrappers would render twice."""
    result = run_scenario(
        "build", "invalid_bundle_placements", ":bad", expect_error=True
    )
    assert BUNDLE_CONFLICT in result.stderr


@pytest.mark.bazel_slow
def test_bundle_reached_with_conflicting_attach_to_is_rejected():
    """One final location with two different attach_to values is rejected."""
    result = run_scenario(
        "build", "invalid_bundle_placements", ":bad_attach_to", expect_error=True
    )
    assert BUNDLE_CONFLICT in result.stderr


@pytest.mark.bazel_slow
def test_source_dir_and_srcs_are_rejected_during_loading():
    scenario_dir = SCENARIOS_ROOT / "invalid_source_combination"
    build_file = scenario_dir / "BUILD"
    fixture = scenario_dir / "BUILD.negative"
    # Keep this load-time failure fixture hidden from recursive Bazel targets.
    assert not build_file.exists(), (
        "negative test package must not be discovered by //..."
    )

    # Install the invalid BUILD file only while the subprocess test exercises it.
    build_file.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        result = run_scenario(
            "build",
            "invalid_source_combination",
            ":bad_source_and_srcs",
            expect_error=True,
        )
    finally:
        build_file.unlink()

    assert "srcs cannot be combined with source_dir" in result.stderr
