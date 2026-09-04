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

from src.tests.docs_bzl.helpers import run_scenario


@pytest.mark.bazel_slow
def test_nested_component_package_is_mounted_by_its_module():
    """Nested component bundles are rendered at both module mount points."""
    result = run_scenario("run", "reference_integration/modern_module", ":docs")

    # The parent module owns the surrounding ``components`` tree, while each
    # child bundle supplies its own page below the corresponding mount point.
    assert (result.build_dir / "components" / "component" / "index.html").is_file()
    assert (
        result.build_dir / "components" / "unlinked_component" / "index.html"
    ).is_file()


@pytest.mark.bazel_slow
def test_linked_component_requires_parent_context():
    """A linked component cannot build standalone without its external Needs."""
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


@pytest.mark.bazel_slow
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
