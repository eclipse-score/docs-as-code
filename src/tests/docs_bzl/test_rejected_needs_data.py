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

"""Needs inventories passed through ``docs(data = [...])`` are rejected."""

import pytest

from src.tests.docs_bzl.helpers import run_negative_scenario


@pytest.mark.bazel_slow
def test_needs_in_data_is_rejected_during_loading():
    """A Needs inventory in data fails and points to external_needs."""
    result = run_negative_scenario("rejected_needs_data", ":docs")

    assert "Needs inventories are not accepted in data" in result.stderr
    # The message names the offending label so users can find it quickly.
    assert "score_platform:needs_json_file" in result.stderr
    assert "external_needs = [...]" in result.stderr
