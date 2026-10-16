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

import json

import pytest

from src.tests.docs_bzl.helpers import built_output, load_needs, run_bazel, run_scenario


@pytest.mark.bazel_slow
def test_nested_component_package_is_mounted_by_its_module():
    """Mounted component pages retain navigation and filter source controls."""
    result = run_scenario("run", "reference_integration/modern_module", ":docs")
    # ``needs_json`` remains accepted in ``external_needs`` without the INFO
    # message reserved for Needs inventories passed through ``data``.
    assert "Passing a Needs inventory through" not in (result.stdout + result.stderr)

    # The parent module owns the surrounding ``components`` tree, while each
    # child bundle supplies its own page below the corresponding mount point.
    assert (result.build_dir / "components" / "component" / "index.html").is_file()
    assert (
        result.build_dir / "components" / "unlinked_component" / "index.html"
    ).is_file()

    # The nested metamodel bundle is generated below bazel-out, so this page
    # exercises the mounted-source branch that cannot provide a repository edit
    # URL. The page table of contents is independent of that source control and
    # must remain available.
    generated_page = (
        result.build_dir
        / "components"
        / "unlinked_component"
        / "generated_metamodel"
        / "index.html"
    )
    assert generated_page.is_file()
    generated_html = generated_page.read_text(encoding="utf-8")
    assert 'aria-label="On this page"' in generated_html
    assert "Edit on GitHub" not in generated_html


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

    # The top-level site imports the platform's public ``docs`` target, so its
    # feature link is rendered before the module mounts are traversed.
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


@pytest.mark.bazel_cached
def test_bundle_metadata_is_added_to_the_explicit_primary_need():
    """A component bundle contributes its direct Bazel target to its Need.

    The fixture's bundle uses the generic Bazel target name ``docs_bundle`` but
    explicitly selects ``tool_req__legacy_component``. This proves that the
    association is independent of both the bundle name and imported Needs.
    """
    result = run_scenario("build", "reference_integration", ":needs_json")
    assert result.artifacts is not None

    needs = load_needs(result.artifacts["needs.json"])
    # The Need is selected by the bundle's explicit ``primary_need_id``.
    legacy_need = needs["tool_req__legacy_component"]
    assert isinstance(legacy_need, dict)
    assert (
        legacy_need["bazel_target"]
        == "@@//src/tests/docs_bzl/scenarios/reference_integration/legacy_module/"
        "docs/components/component:component_sources"
    )
    assert legacy_need["bazel_type"] == "filegroup"


@pytest.mark.bazel_cached
@pytest.mark.parametrize(
    ("bundle_name", "expected_files", "expected_link_files"),
    [
        pytest.param(
            "docs_bundle",
            (
                "component/api.h",
                "component/implementation.cc",
                "component/implementation.py",
                "component/detail/support.cc",
                "component/generated/config.def",
                "unlinked_component/api.h",
            ),
            (
                "component/implementation.py",
                "component/detail/support.cc",
                "unlinked_component/api.h",
            ),
            id="local_support_reached_only_through_sibling",
        ),
        pytest.param(
            "selected_sibling_api",
            (
                "component/api.h",
                "component/detail/support.cc",
                "unlinked_component/api.h",
            ),
            ("component/detail/support.cc", "unlinked_component/api.h"),
            id="explicit_sibling_api_excludes_its_sibling_implementation",
        ),
    ],
)
def test_component_files_and_sourcelinks_share_the_component_boundary(
    bundle_name: str,
    expected_files: tuple[str, ...],
    expected_link_files: tuple[str, ...],
):
    """Explicit selections and local leaves survive foreign dependency paths.

    The linked component reaches its local support library only through the
    sibling implementation. The second bundle explicitly selects the sibling's
    header-only API, which depends on that same sibling implementation. In both
    cases the implementation's files and marker are excluded, while the local
    support files and marker are retained. The selected API's own header and
    marker must also survive despite its out-of-package label.
    """
    scenario = "reference_integration/modern_module/docs/components/component"
    package = f"//src/tests/docs_bzl/scenarios/{scenario}"
    components_prefix = package[2:].rsplit("/", 1)[0] + "/"
    # Other scenario builds may leave this target cached in multiple Bazel
    # configurations. Inspect only the current top-level configuration.
    result = run_bazel(
        [
            "cquery",
            f"config({package}:{bundle_name}.__internal__.files, target)",
            "--output=starlark",
            '--starlark:expr="\\n".join([f.short_path for f in target.files.to_list()])',
        ]
    )
    assert sorted(result.stdout.splitlines()) == sorted(
        components_prefix + path for path in expected_files
    )

    run_scenario("build", scenario, f":{bundle_name}.__internal__.sourcelinks_json")
    cache = built_output(
        f"scenarios/{scenario}", f"{bundle_name}.__internal__.sourcelinks_json.json"
    )
    links = json.loads(cache.read_text(encoding="utf-8"))
    # Repository metadata entries have no file; compare the actual code links.
    assert {link["file"] for link in links if "file" in link} == {
        components_prefix + path for path in expected_link_files
    }
