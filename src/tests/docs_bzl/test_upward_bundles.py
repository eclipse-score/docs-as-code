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
"""Rough specification tests for cross-bundle Needs propagation."""

from src.tests.docs_bzl.helpers import built_output, load_needs, run_bazel, run_scenario


def test_source_bundle_exports_own_needs_and_declared_parent_needs():
    """A local export stays local while an upward export merges direct parents."""
    run_scenario("build", "upward_bundles", ":component.__internal__.needs_local")
    run_scenario("build", "upward_bundles", ":component.__internal__.needs_upward")

    local_needs = load_needs(
        built_output(
            "scenarios/upward_bundles",
            "component.__internal__.needs_local/_build/needs/needs.json",
        )
    )
    needs = load_needs(
        built_output(
            "scenarios/upward_bundles",
            "component.__internal__.needs_upward/needs.json",
        )
    )

    assert {
        "comp__component_seat_heating_controller",
        "comp_req__component__temperature_control",
    } <= local_needs.keys()
    assert "feat_req__platform__seat_heating" not in local_needs

    assert {
        "feat__platform_seat_heating",
        "feat_req__platform__seat_heating",
        "comp__component_seat_heating_controller",
        "comp_req__component__temperature_control",
    } <= needs.keys()


def test_source_less_bundle_does_not_inherit_undeclared_ancestor_needs():
    """A chain only includes the explicitly declared direct ancestor."""
    run_scenario("build", "upward_bundles", ":application.__internal__.needs_upward")

    needs = load_needs(
        built_output(
            "scenarios/upward_bundles",
            "application.__internal__.needs_upward/needs.json",
        )
    )

    assert "comp__component_seat_heating_controller" in needs
    assert "feat__platform_seat_heating" not in needs


def test_source_less_bundle_is_rejected_as_upward_ancestor():
    """A source-less hierarchy group cannot provide a direct local export."""
    result = run_scenario(
        "build",
        "upward_bundles",
        ":invalid_child.__internal__.needs_upward",
        expect_error=True,
    )

    assert "has no own documentation sources" in result.stderr
    assert "would introduce transitive dependencies" in result.stderr


def test_data_only_bundle_does_not_get_needs_targets():
    """Supporting-data bundles remain outside the Needs export hierarchy."""
    run_bazel(
        [
            "query",
            "//src/tests/docs_bzl/scenarios/data_files_runfiles:legacy_data_bundle.__internal__.needs_local",
        ],
        expect_error=True,
    )
