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
"""data_files_runfiles: bundles made of generated, and declared sources."""

import re
from pathlib import Path

import pytest

from src.tests.docs_bzl.helpers import (
    built_output,
    load_needs,
    load_needs_json,
    run_bazel,
    run_scenario,
    toctree_links,
)

SCENARIO = "data_files_runfiles"
PACKAGE = f"scenarios/{SCENARIO}"


def _title(page: Path) -> str:
    """Return the text of a rendered page's <h1>."""
    match = re.search(r"<h1>([^<]*)", page.read_text(encoding="utf-8"))
    assert match, f"no <h1> in {page}"
    return match[1].strip()


@pytest.fixture(scope="module")
def build_dir() -> Path:
    return run_scenario("run", SCENARIO, ":docs").build_dir


@pytest.mark.bazel_slow
def test_host_page_links_every_mounted_bundle(build_dir: Path):
    """Both bundles use attach_to = "index" and show up in its toctree."""
    assert sorted(toctree_links(build_dir / "index.html")) == [
        "data_test/index.html",
        "isolated_test/index.html",
    ]


@pytest.mark.bazel_slow
def test_generated_rst_in_srcs_becomes_a_page(build_dir: Path):
    """A genrule output listed in docs_bundle(srcs=...) is rendered as a page."""
    assert _title(build_dir / "data_test" / "index.html") == "Generated Data Page"


@pytest.mark.bazel_slow
def test_generated_companion_file_is_readable_but_not_a_page(build_dir: Path):
    """The generated .mmd next to the .rst feeds the mermaid directive and is
    not registered as a Sphinx document of its own."""
    html = (build_dir / "data_test" / "index.html").read_text(encoding="utf-8")
    diagram = re.search(
        r'<pre id="generated-data-diagram" class="mermaid">(.*?)</pre>', html, re.S
    )

    assert diagram, "mermaid diagram from generated_data.mmd is missing"
    assert "class GeneratedData" in diagram[1]
    assert not (build_dir / "data_test" / "generated_data.html").exists()


@pytest.mark.bazel_slow
def test_explicit_source_bundle_renders_only_declared_pages(build_dir: Path):
    """isolated/undeclared.rst sits next to the declared page but is not in srcs."""
    isolated = build_dir / "isolated_test"

    assert _title(isolated / "index.html") == "Isolated Declared Page"
    assert not (isolated / "undeclared.html").exists()


@pytest.mark.bazel_cached
def test_needs_export_uses_the_host_project_name():
    result = run_scenario("build", SCENARIO, ":needs_json")
    assert result.artifacts is not None

    data = load_needs_json(result.artifacts["needs.json"])
    assert data["project"] == "Data Files Runfiles Test"


@pytest.mark.bazel_cached
def test_bundle_needs_exports_build_for_generated_and_declared_sources():
    """Each bundle's own Needs export builds, named after the bundle.

    Neither docs() target depends on these per-bundle exports, so only this
    test builds them. The bundles hold no Needs, so the exports are empty.
    """
    bundles = ["data_bundle", "isolated_source_bundle"]
    targets = [f"{bundle}.__internal__.needs_local" for bundle in bundles]
    run_bazel(
        ["build", *[f"//src/tests/docs_bzl/{PACKAGE}:{target}" for target in targets]]
    )

    for bundle, target in zip(bundles, targets, strict=True):
        needs_json = built_output(PACKAGE, f"{target}/needs.json")
        assert load_needs_json(needs_json)["project"] == bundle
        assert load_needs(needs_json) == {}
