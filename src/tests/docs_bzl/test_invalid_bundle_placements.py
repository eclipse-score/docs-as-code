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

from src.tests.docs_bzl.helpers import repo_root, run_scenario


def test_invalid_bundle_placements_are_rejected_during_analysis():
    run_scenario("build", "invalid_bundle_placements", ":bad", expect_error=True)
    run_scenario(
        "build", "invalid_bundle_placements", ":bad_attach_to", expect_error=True
    )


def test_source_dir_and_srcs_are_rejected_during_loading():
    scenario_dir = (
        repo_root() / "src/tests/docs_bzl/scenarios/invalid_source_combination"
    )
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
