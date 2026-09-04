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

import pytest

from src.tests.docs_bzl.helpers import built_output, load_needs, run_bazel, run_scenario


def test_score_platform_publishes_feature_requirement():
    """The platform fixture provides the external requirement used by modules."""
    result = run_scenario(
        "build", "reference_integration/score_platform", ":needs_json"
    )
    assert result.artifacts

    needs = load_needs(result.artifacts["needs.json"])
    assert "feat_req__platform__feature" in needs, sorted(needs)


def test_module_and_component_needs_targets_build_with_source_links():
    """Preserve component source links in composed Needs builds.

    The module targets prove that ``code_targets`` creates links for nested
    component bundles and propagates them through the module bundle. Both
    targets are built in one Bazel invocation because this suite deliberately
    drives coarse-grained integration cases.
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
    ]
    # Build the module and nested component bundles together so the assertions
    # below verify source-link propagation at each relevant bundle boundary.
    run_bazel(
        [
            "build",
            *[
                f"//src/tests/docs_bzl/scenarios/{scenario}:needs_json"
                for scenario, _, _ in expected_links
            ],
            "//src/tests/docs_bzl/scenarios/reference_integration/legacy_module/docs/components/component:docs_bundle.__internal__.needs_local",
        ]
    )

    for scenario, need_id, source_link_fragment in expected_links:
        # Each Needs export must retain the source path belonging to the
        # package where the annotated implementation is defined.
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

    # The component's own export uses the same source-link input as the
    # composed module build. Keep this assertion separate from the module
    # outputs so the local target is verified as an actual standalone export.
    local_needs = load_needs(
        built_output(
            "scenarios/reference_integration/legacy_module/docs/components/component",
            "docs_bundle.__internal__.needs_local/_build/needs/needs.json",
        )
    )
    local_need = local_needs.get("tool_req__legacy_component")
    assert isinstance(local_need, dict), sorted(local_needs)
    typed_local_need = cast(dict[str, object], local_need)
    local_source_code_link = typed_local_need.get("source_code_link")
    assert isinstance(local_source_code_link, str)
    assert "legacy_module/docs/components/component/implementation.py#L14" in (
        local_source_code_link
    )


def test_nested_component_package_is_mounted_by_its_module():
    """Nested component bundles are rendered at both module mount points."""
    result = run_scenario("run", "reference_integration/modern_module", ":docs")

    # The parent module owns the surrounding ``components`` tree, while each
    # child bundle supplies its own page below the corresponding mount point.
    assert (result.build_dir / "components" / "component" / "index.html").is_file()
    assert (
        result.build_dir / "components" / "unlinked_component" / "index.html"
    ).is_file()


def test_modern_module_linked_and_unlinked_components():
    """Parent context is required only for the component with an external link.

    The modern module imports the platform Needs. Its linked component relies
    on that imported feature requirement, whereas the unlinked component has
    no dependency outside its own bundle and is the independent-build control.
    """
    module_result = run_scenario(
        "build", "reference_integration/modern_module", ":needs_json"
    )
    assert module_result.artifacts
    module_needs = load_needs(module_result.artifacts["needs.json"])
    # Building through the module provides the platform requirement and must
    # export both the linked and unlinked component requirements.
    assert {
        "comp_req__modern_component__platform_feature",
        "tool_req__modern_component",
        "tool_req__modern_unlinked_component",
    } <= module_needs.keys()

    # The unlinked component has no external references, so its local Needs
    # export is valid without the modern module's external_needs declaration.
    run_scenario(
        "build",
        "reference_integration/modern_module/docs/components/unlinked_component",
        ":docs_bundle.__internal__.needs_local",
    )
    unlinked_needs = load_needs(
        built_output(
            "scenarios/reference_integration/modern_module/docs/components/unlinked_component",
            "docs_bundle.__internal__.needs_local/_build/needs/needs.json",
        )
    )
    assert "tool_req__modern_unlinked_component" in unlinked_needs

    # The linked component intentionally omits that external Needs input. The
    # standalone build must therefore fail while resolving its derived_from
    # link to the platform feature requirement.
    with pytest.raises(RuntimeError) as exc_info:
        run_scenario(
            "build",
            "reference_integration/modern_module/docs/components/component",
            ":docs_bundle.__internal__.needs_local",
        )
    assert "feat_req__platform__feature" in str(exc_info.value)


def test_reference_integration_root_bundle_exports_its_own_needs():
    """The root docs() bundle exposes a local Needs export for its own sources."""
    run_scenario(
        "build", "reference_integration", ":docs_bundle.__internal__.needs_local"
    )

    assert built_output(
        "scenarios/reference_integration",
        "docs_bundle.__internal__.needs_local/_build/needs/needs.json",
    ).is_file()


def test_reference_integration_builds_with_platform_requirements():
    """Mount modules and render nested component source-code links."""
    result = run_scenario("run", "reference_integration", ":docs")

    # The top-level site imports the platform bundle, so its feature link is
    # rendered on the main page before the module mounts are traversed.
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
    # Both module pages and their nested component pages must be present after
    # composition; source links are checked above on the component pages.
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
