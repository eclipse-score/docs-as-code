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
"""nested_bundles: a parent bundle composes a child bundle below its own mount."""

from pathlib import Path
from typing import Any

import pytest

from src.tests.docs_bzl.helpers import (
    built_output,
    load_json,
    load_needs,
    run_scenario,
    scenario_label,
    scenario_path,
    toctree_links,
)

SCENARIO = "nested_bundles"
PACKAGE = f"scenarios/{SCENARIO}"
PARENT_MOUNT = "concepts/example_bundle"
CHILD_MOUNT = f"{PARENT_MOUNT}/child"


def _mounts(manifest: Any) -> dict[str, dict[str, Any]]:
    """Index the entries of a composition manifest by their mount point."""
    return {mount["mount_at"]: mount for mount in manifest["mounts"]}


@pytest.fixture(scope="module")
def build_dir() -> Path:
    return run_scenario("run", SCENARIO, ":docs").build_dir


@pytest.fixture(scope="module")
def mounts() -> dict[str, dict[str, Any]]:
    run_scenario("build", SCENARIO, ":_mounts_manifest")
    return _mounts(load_json(built_output(PACKAGE, "_mounts_manifest.json")))


@pytest.fixture(scope="module")
def needs() -> dict[str, Any]:
    result = run_scenario("build", SCENARIO, ":needs_json")
    assert result.artifacts is not None
    return load_needs(result.artifacts["needs.json"])


@pytest.mark.bazel_cached
def test_parent_attaches_to_the_requested_toctree(mounts: dict[str, dict[str, Any]]):
    """toctree_index = 1 attaches the parent to the second toctree of concepts."""
    parent = mounts[PARENT_MOUNT]
    assert parent["attach_to"] == "concepts/index"
    assert parent["toctree_index"] == 1


@pytest.mark.bazel_slow
def test_parent_is_linked_from_the_requested_toctree(build_dir: Path):
    """The rendered link sits in the "Mounted bundles" toctree, not the first one."""
    html = (build_dir / "concepts" / "index.html").read_text(encoding="utf-8")
    article = html[html.index("<article") :]
    _, mounted = article.split('caption-text">Mounted bundles', 1)
    assert 'href="example_bundle/index.html"' in mounted.split("</ul>", 1)[0]


@pytest.mark.bazel_cached
def test_child_mounts_below_its_parent_with_its_entry_doc(
    mounts: dict[str, dict[str, Any]],
):
    """The child is placed relative to the parent and keeps entry_doc = landing."""
    assert sorted(mounts) == ["", PARENT_MOUNT, CHILD_MOUNT]
    child = mounts[CHILD_MOUNT]
    assert child["attach_to"] == f"{PARENT_MOUNT}/index"
    assert child["entry_doc"] == "landing"


@pytest.mark.bazel_slow
def test_child_entry_page_is_linked_from_the_parent(build_dir: Path):
    parent_html = (build_dir / PARENT_MOUNT / "index.html").read_text(encoding="utf-8")
    assert toctree_links(parent_html) == {"child/landing.html": "Child landing page"}
    assert (build_dir / CHILD_MOUNT / "landing.html").is_file()


@pytest.mark.bazel_cached
def test_data_stays_with_the_mount_that_declares_it(mounts: dict[str, dict[str, Any]]):
    """Only :parent declares data; the root and the child get none of it."""
    assert mounts[PARENT_MOUNT]["data"] == [
        f"{scenario_path(SCENARIO)}/generated/generated_output.txt"
    ]
    assert mounts[""]["data"] == []
    assert mounts[CHILD_MOUNT]["data"] == []


@pytest.mark.bazel_cached
def test_nested_needs_are_exported_once_below_the_parent_mount(
    needs: dict[str, Any],
):
    assert set(needs) == {
        "tool_req__docs_bzl_nested_bundle",
        "gd_req__docs_bzl_nested_bundle",
    }
    for need in needs.values():
        assert need["docname"] == f"{PARENT_MOUNT}/index"
    tool_req = needs["tool_req__docs_bzl_nested_bundle"]
    assert tool_req["satisfies"] == ["gd_req__docs_bzl_nested_bundle"]


@pytest.mark.bazel_cached
def test_code_target_sources_are_collected_transitively(needs: dict[str, Any]):
    """Source links come through cc_binary -> cc_library, nested filegroups and
    a py_binary that root and child both list (reported once). The untagged
    example_main.cc contributes nothing."""
    root = scenario_path(SCENARIO)
    # source_code_link is one string of "<url><><file>:<line>" entries.
    links: str = needs["tool_req__docs_bzl_nested_bundle"]["source_code_link"]
    assert sorted(link.split("<>")[1] for link in links.split(", ")) == sorted(
        [
            f"{root}/child/example.cc:1",
            f"{root}/child/example.py:14",
            f"{root}/child/filegroup_source.py:14",
        ]
    )


@pytest.mark.bazel_cached
def test_code_targets_keep_their_rule_kind(mounts: dict[str, dict[str, Any]]):
    code_targets: list[dict[str, str]] = mounts[CHILD_MOUNT]["bundle"]["code_targets"]
    assert {target["label"]: target["type"] for target in code_targets} == {
        scenario_label(SCENARIO, ":example_binary"): "py_binary",
        scenario_label(SCENARIO, ":example_executable"): "cc_binary",
        scenario_label(SCENARIO, ":nested_filegroup_sources"): "filegroup",
    }


@pytest.mark.bazel_cached
def test_aggregate_bundle_preserves_declared_order():
    """Bundles listed in a docs_bundle keep their declaration order."""
    run_scenario("build", SCENARIO, ":ordered_aggregate_manifest")
    manifest = load_json(built_output(PACKAGE, "ordered_aggregate_manifest.json"))
    mounts: list[dict[str, str]] = manifest["mounts"]
    assert [mount["mount_at"] for mount in mounts] == ["first", "second"]
    assert [mount["entry_doc"] for mount in mounts] == ["index", "landing"]
