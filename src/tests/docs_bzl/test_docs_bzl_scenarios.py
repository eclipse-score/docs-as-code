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
"""Golden-output integration tests for public ``docs.bzl`` scenarios."""

import pytest

from src.tests.docs_bzl.expected_outputs import (
    ExpectedOutput,
    discover_expected_outputs,
    discover_expected_scenarios,
    update_expected_output,
)


def _expected_output_test_cases() -> list[object]:
    """Create one pytest test case per checked-in target output.

    The target command determines the marker directly, so build-only outputs
    are cacheable and targets that execute Sphinx through ``bazel run`` are
    slow without classifying unrelated outputs in the same scenario.
    """
    test_cases: list[object] = []
    for scenario in discover_expected_scenarios():
        for expected in discover_expected_outputs(scenario):
            marker = (
                pytest.mark.bazel_slow
                if expected.target.command == "run"
                else pytest.mark.bazel_cached
            )
            test_cases.append(
                pytest.param(
                    scenario,
                    expected,
                    marks=marker,
                    id=f"{scenario}[{expected.short_name}]",
                )
            )
    return test_cases


@pytest.mark.parametrize(("scenario", "expected_output"), _expected_output_test_cases())
def test_docs_bzl_scenario_expected_output(
    scenario: str, expected_output: ExpectedOutput
):
    """Check one generated public-scenario output against its checked-in contract."""
    update_expected_output(scenario, expected_output)
