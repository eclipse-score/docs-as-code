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
"""Focused tests for source-bearing docs_bundle Needs exports."""

from src.tests.docs_bzl.helpers import built_output, load_needs, run_scenario


def test_source_bundle_exports_its_own_needs():
    """A local export contains the Needs declared by the bundle's own sources."""
    run_scenario("build", "local_bundle", ":platform.__internal__.needs_local")

    needs = load_needs(
        built_output(
            "scenarios/local_bundle",
            "platform.__internal__.needs_local/_build/needs/needs.json",
        )
    )

    assert {
        "feat__platform_seat_heating",
        "feat_req__platform__seat_heating",
    } <= needs.keys()
