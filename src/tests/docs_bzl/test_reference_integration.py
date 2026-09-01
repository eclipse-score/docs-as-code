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

"""Reference integration scenario for the public docs() API."""

import pytest

from src.tests.docs_bzl.helpers import load_needs, run_scenario


def test_score_platform_publishes_feature_requirement():
    result = run_scenario(
        "build", "reference_integration/score_platform", ":needs_json"
    )
    assert result.artifacts

    needs = load_needs(result.artifacts["needs.json"])
    assert "feat_req__platform__feature" in needs, sorted(needs)


@pytest.mark.parametrize(
    "scenario",
    [
        "reference_integration/legacy_module",
        "reference_integration/modern_module",
        "reference_integration/legacy_module/docs/components/component",
        "reference_integration/modern_module/docs/components/component",
    ],
)
def test_module_and_component_needs_targets_build(scenario: str):
    """Each module and component can build its needs inventory independently."""
    run_scenario("build", scenario, ":needs_json")


def test_nested_component_package_is_mounted_by_its_module():
    """A module run excludes its nested component from primary discovery."""
    result = run_scenario("run", "reference_integration/legacy_module", ":docs")

    assert (result.build_dir / "components" / "component" / "index.html").is_file()


def test_reference_integration_builds_with_platform_requirements():
    """The integration mounts modules and their nested component packages."""
    result = run_scenario("run", "reference_integration", ":docs")

    html = (result.build_dir / "index.html").read_text(encoding="utf-8")
    assert (
        "score-platform/main/platform/feature.html#feat_req__platform__feature" in html
    )
    assert (result.build_dir / "modules" / "legacy_module" / "index.html").is_file()
    assert (
        result.build_dir
        / "modules"
        / "legacy_module"
        / "components"
        / "component"
        / "index.html"
    ).is_file()
    assert (result.build_dir / "modules" / "modern_module" / "index.html").is_file()
    assert (
        result.build_dir
        / "modules"
        / "modern_module"
        / "components"
        / "component"
        / "index.html"
    ).is_file()
