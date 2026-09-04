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
"""Golden-output tests for public ``docs.bzl`` scenarios."""

import pytest

from src.tests.docs_bzl.expected_outputs import (
    discover_expected_outputs,
    discover_expected_scenarios,
    verify_expected_outputs,
)


def _expected_scenario_parameters() -> list[object]:
    parameters: list[object] = []
    for scenario in discover_expected_scenarios():
        expected_outputs = discover_expected_outputs(scenario)
        marker = (
            pytest.mark.bazel_slow
            if any(expected.target.command == "run" for expected in expected_outputs)
            else pytest.mark.bazel_cached
        )
        parameters.append(pytest.param(scenario, marks=marker))
    return parameters


@pytest.mark.parametrize("scenario", _expected_scenario_parameters())
def test_scenario_matches_expected_outputs(scenario: str):
    """Each opted-in consumer fixture matches its checked-in target outputs."""
    verify_expected_outputs(scenario)
