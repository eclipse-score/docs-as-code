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
"""data_files_runfiles: bundles whose pages are generated or explicitly selected.

The ``srcs`` of a ``docs_bundle`` can carry genrule outputs that live in
``bazel-out``. The bundle stages them into the runfiles of ``:docs`` and
``score_mounts`` resolves the generated source root at ``bazel run`` time.
"""

from pathlib import Path

import pytest

from src.tests.end_to_end.testcases.helpers import run_scenario, toctree_links

SCENARIO = "data_files_runfiles"


@pytest.fixture(scope="module")
def build_dir() -> Path:
    """Render the scenario once and share the output between its checks."""
    return run_scenario("run", SCENARIO, ":docs").build_dir


def _page(build_dir: Path, path: str) -> str:
    return (build_dir / path).read_text(encoding="utf-8")


@pytest.mark.bazel_slow
def test_generated_bundle_sources_are_mounted(build_dir: Path):
    """A genrule-generated .rst in srcs renders as the bundle entry page."""
    assert "Generated Data Page" in _page(build_dir, "data_test/index.html")


@pytest.mark.bazel_slow
def test_generated_companion_file_resolves_next_to_its_page(build_dir: Path):
    """A generated non-rst file in srcs is readable relative to its page."""
    html = _page(build_dir, "data_test/index.html")
    assert 'id="generated-data-diagram"' in html
    assert "class GeneratedData" in html


@pytest.mark.bazel_slow
def test_legacy_generated_page_in_data_still_mounts(build_dir: Path):
    """A generated .rst passed through data (legacy form) still renders."""
    assert "Legacy Data Page" in _page(build_dir, "legacy_data_test/index.html")


@pytest.mark.bazel_slow
def test_explicit_source_bundle_mounts_only_declared_pages(build_dir: Path):
    """srcs = [...] selects pages; undeclared siblings are not mounted."""
    assert "Isolated Declared Page" in _page(build_dir, "isolated_test/index.html")
    assert not (build_dir / "isolated_test" / "undeclared.html").exists()


@pytest.mark.bazel_slow
def test_attached_mounts_are_listed_in_the_host_toctree(build_dir: Path):
    """Each bundle with attach_to = "index" is linked from the root page."""
    assert toctree_links(_page(build_dir, "index.html")) == {
        "data_test/index.html": "Generated Data Page",
        "isolated_test/index.html": "Isolated Declared Page",
        "legacy_data_test/index.html": "Legacy Data Page",
    }
