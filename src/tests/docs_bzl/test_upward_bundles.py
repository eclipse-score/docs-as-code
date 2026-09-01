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
"""Public docs_bundle() hierarchy-contract tests."""

import json

from src.tests.docs_bzl.helpers import built_output, load_needs, run_scenario


def test_real_score_needs_cross_the_module_component_hierarchy():
    """Use the real SCORE metamodel across module, component and subcomponent."""
    result = run_scenario("build", "upward_bundles", ":needs_json")

    assert result.artifacts
    needs = load_needs(result.artifacts["needs.json"])

    expected_ids = {
        "feat__seat_heating",
        "feat_req__module__seat_heating",
        "mod__seat_heating_module",
        "comp__seat_heating_controller",
        "comp_req__component__temperature_control",
        "comp__seat_heating_sensor",
        "comp_req__subcomponent__temp_measure",
    }
    assert expected_ids <= needs.keys()

    # Keep this assertion deliberately representation-independent: Sphinx-Needs
    # serializes scalar and list links differently across supported versions.
    needs_text = json.dumps(needs, sort_keys=True)
    assert needs_text.count("feat_req__module__seat_heating") >= 3
    assert "comp__seat_heating_controller" in needs_text
    assert "comp__seat_heating_sensor" in needs_text


def test_docs_can_consume_an_upward_bundle_for_its_own_sources():
    run_scenario(
        "build",
        "upward_bundles",
        ":_docs_source_bundle_needs_upward",
    )
    source_needs = load_needs(
        built_output(
            "scenarios/upward_bundles",
            "_docs_source_bundle_needs_upward/needs.json",
        )
    )
    assert "feat_req__platform__seat_heating" in source_needs

    result = run_scenario("run", "upward_bundles", ":docs")
    html = (result.build_dir / "index.html").read_text(encoding="utf-8")
    assert "feat_req__platform__seat_heating" in html


def test_docs_exposes_a_stable_public_source_bundle_alias():
    run_scenario("build", "upward_bundles", ":docs_source_bundle")
    run_scenario("build", "upward_bundles", ":docs_source_bundle_needs_upward")
    needs = load_needs(
        built_output(
            "scenarios/upward_bundles",
            "docs_source_bundle_needs_upward/needs.json",
        )
    )
    assert "feat_req__platform__seat_heating" in needs


def test_bundle_needs_exports_are_local_and_include_declared_ancestors():
    run_scenario(
        "build",
        "upward_bundles",
        ":component_needs_upward",
    )
    run_scenario(
        "build",
        "upward_bundles",
        ":subcomponent_needs_upward",
    )

    component_needs = load_needs(
        built_output(
            "scenarios/upward_bundles",
            "component_needs_upward/needs.json",
        )
    )
    subcomponent_needs = load_needs(
        built_output(
            "scenarios/upward_bundles",
            "subcomponent_needs_upward/needs.json",
        )
    )

    assert "comp_req__component__temperature_control" in component_needs
    assert "feat_req__module__seat_heating" in component_needs
    assert "comp_req__subcomponent__temp_measure" not in component_needs
    assert "comp_req__subcomponent__temp_measure" in subcomponent_needs


def test_upward_bundle_documentation_renders_all_three_levels():
    result = run_scenario("run", "upward_bundles", ":docs")

    assert (result.build_dir / "index.html").is_file()
    assert (result.build_dir / "component" / "index.html").is_file()
    assert (result.build_dir / "component" / "subcomponent" / "index.html").is_file()


def test_aggregators_can_group_upward_bundle_dependencies():
    run_scenario("build", "upward_bundles", ":hierarchy_group")
    run_scenario("build", "upward_bundles", ":subcomponent_needs_upward")

    hierarchy_needs = load_needs(
        built_output(
            "scenarios/upward_bundles",
            "hierarchy_group_needs_upward/needs.json",
        )
    )
    assert "feat_req__module__seat_heating" in hierarchy_needs


def test_multiple_direct_parents_merge_their_upward_exports():
    run_scenario("build", "upward_bundles", ":multiple_parent_group_needs_upward")

    needs = load_needs(
        built_output(
            "scenarios/upward_bundles",
            "multiple_parent_group_needs_upward/needs.json",
        )
    )
    assert {
        "feat_req__platform__seat_heating",
        "feat_req__module__seat_heating",
        "comp_req__component__temperature_control",
    } <= needs.keys()
    assert len(needs) == 7


def test_shared_ancestor_is_deduplicated_in_a_diamond():
    run_scenario("build", "upward_bundles", ":diamond_group_needs_upward")

    needs = load_needs(
        built_output(
            "scenarios/upward_bundles",
            "diamond_group_needs_upward/needs.json",
        )
    )
    assert {
        "feat_req__module__seat_heating",
        "comp_req__component__temperature_control",
    } <= needs.keys()
    assert len(needs) == 7
