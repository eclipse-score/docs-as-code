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

"""docs_assets files of any type are copied unchanged into the HTML output."""

import pytest

from src.tests.docs_bzl.helpers import (
    TEST_ROOT,
    TEST_ROOT_BAZEL,
    built_output,
    run_bazel,
    run_scenario,
)

SCENARIO = "docs_assets"
PACKAGE = f"scenarios/{SCENARIO}"


@pytest.mark.bazel_slow
def test_assets_of_every_type_are_copied_unchanged():
    """HTML directory, PDF, PNG and a checked-in SVG land below child/api/."""
    result = run_scenario("run", SCENARIO, ":docs")
    api = result.build_dir / "child" / "api"

    expected_sources = {
        # A directory's contents go to the destination, keeping sub-paths.
        "index.html": built_output(PACKAGE, "api_html/index.html"),
        "files/page.html": built_output(PACKAGE, "api_html/files/page.html"),
        "doxygen.css": built_output(PACKAGE, "api_html/doxygen.css"),
        # A file goes to <destination>/<basename>.
        "manual.pdf": built_output(PACKAGE, "manual.pdf"),
        "logo.png": built_output(PACKAGE, "logo.png"),
        "diagram.svg": TEST_ROOT / PACKAGE / "assets" / "diagram.svg",
    }
    for output_path, source in expected_sources.items():
        copied = api / output_path
        assert copied.is_file(), f"missing asset {copied}"
        assert not copied.is_symlink(), f"asset {copied} must be a real file"
        assert copied.read_bytes() == source.read_bytes(), f"{copied} changed"

    # The bundle's own page links to the assets with plain relative links.
    child_page = (result.build_dir / "child" / "index.html").read_text()
    assert 'href="api/index.html"' in child_page


# Every action that reads an asset file. ``deps()`` alone is not enough: the
# asset targets are in every target's dependency graph through ``bundles``,
# but only the HTML targets may read their files.
_ASSET_FILES = (
    ".*scenarios/docs_assets/(api_html|manual.pdf|logo.png|assets/diagram.svg).*"
)


@pytest.mark.bazel_cached
@pytest.mark.parametrize(
    ("target", "reads_assets"),
    [
        (":docs", True),
        (":live_preview", True),
        (":needs_json", False),
        (":docs_check", False),
        (":docs_link_check", False),
    ],
)
def test_only_html_targets_read_assets(target: str, reads_assets: bool):
    """Assets are inputs of the HTML builds only, so Doxygen never runs for Needs."""
    label = f"{TEST_ROOT_BAZEL}/{PACKAGE}{target}"
    result = run_bazel(
        ["aquery", f"inputs('{_ASSET_FILES}', deps({label}))", "--output=text"]
    )
    assert ("Mnemonic:" in result.stdout) == reads_assets
