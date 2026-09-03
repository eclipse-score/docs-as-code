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

from typing import cast

from src.tests.docs_bzl.helpers import built_output, load_needs, run_bazel, run_scenario


def test_score_platform_publishes_feature_requirement():
    result = run_scenario(
        "build", "reference_integration/score_platform", ":needs_json"
    )
    assert result.artifacts

    needs = load_needs(result.artifacts["needs.json"])
    assert "feat_req__platform__feature" in needs, sorted(needs)


def test_module_and_component_needs_targets_build_with_source_links():
    """Preserve component source links in standalone and composed needs builds.

    The component targets prove that ``code_targets`` creates the expected
    links directly. The module targets prove that the links propagate through
    a nested module bundle. All four targets are built in one Bazel invocation
    because this suite deliberately drives coarse-grained integration cases.
    """
    expected_links = [
        (
            "reference_integration/legacy_module",
            "tool_req__legacy_component",
            "legacy_module/docs/components/component/implementation.py#L14",
        ),
        (
            "reference_integration/modern_module",
            "tool_req__modern_component",
            "modern_module/docs/components/component/implementation.py#L17",
        ),
        (
            "reference_integration/legacy_module/docs/components/component",
            "tool_req__legacy_component",
            "legacy_module/docs/components/component/implementation.py#L14",
        ),
        (
            "reference_integration/modern_module/docs/components/component",
            "tool_req__modern_component",
            "modern_module/docs/components/component/implementation.py#L17",
        ),
    ]
    run_bazel(
        [
            "build",
            *[
                f"//src/tests/docs_bzl/scenarios/{scenario}:needs_json"
                for scenario, _, _ in expected_links
            ],
        ]
    )

    for scenario, need_id, source_link_fragment in expected_links:
        needs = load_needs(
            built_output(
                f"scenarios/{scenario}",
                "needs_json/_build/needs/needs.json",
            )
        )
        need = needs.get(need_id)
        assert isinstance(need, dict), sorted(needs)
        typed_need = cast(dict[str, object], need)
        source_code_link = typed_need.get("source_code_link")
        assert isinstance(source_code_link, str)
        assert source_link_fragment in source_code_link


def test_nested_component_package_is_mounted_by_its_module():
    """A module run excludes its nested component from primary discovery."""
    result = run_scenario("run", "reference_integration/legacy_module", ":docs")

    assert (result.build_dir / "components" / "component" / "index.html").is_file()


def test_reference_integration_builds_with_platform_requirements():
    """Mount modules and render their nested component source-code links."""
    result = run_scenario("run", "reference_integration", ":docs")

    html = (result.build_dir / "index.html").read_text(encoding="utf-8")
    assert (
        "score-platform/main/platform/feature.html#feat_req__platform__feature" in html
    )
    # Source links are rendered on the mounted component pages, not on this
    # top-level page, because the needs themselves are owned by each component.
    legacy_component_html = (
        result.build_dir
        / "modules"
        / "legacy_module"
        / "components"
        / "component"
        / "index.html"
    ).read_text(encoding="utf-8")
    assert "legacy_module/docs/components/component/implementation.py#L14" in (
        legacy_component_html
    )
    modern_component_html = (
        result.build_dir
        / "modules"
        / "modern_module"
        / "components"
        / "component"
        / "index.html"
    ).read_text(encoding="utf-8")
    assert "modern_module/docs/components/component/implementation.py#L17" in (
        modern_component_html
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
