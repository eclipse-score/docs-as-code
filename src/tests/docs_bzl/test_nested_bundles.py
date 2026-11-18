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

import json
from pathlib import Path
from typing import cast

import pytest

from src.tests.docs_bzl.helpers import (
    TEST_ROOT,
    assert_no_compatibility_findings,
    built_output,
    load_needs,
    repo_root,
    run_scenario,
    toctree_links,
    toctrees,
)

SCENARIO = "nested_bundles"
PACKAGE = f"scenarios/{SCENARIO}"
SCENARIO_PATH = (TEST_ROOT / PACKAGE).relative_to(repo_root()).as_posix()
PARENT_MOUNT = "concepts/example_bundle"
CHILD_MOUNT = f"{PARENT_MOUNT}/child"


def _manifest_mounts(target: str) -> list[dict[str, object]]:
    """Build a composition manifest target and return its mount entries."""
    run_scenario("build", SCENARIO, f":{target}")
    manifest = json.loads(
        built_output(PACKAGE, f"{target}.json").read_text(encoding="utf-8")
    )
    return cast("list[dict[str, object]]", manifest["mounts"])


@pytest.fixture(scope="module")
def build_dir() -> Path:
    return run_scenario("run", SCENARIO, ":docs").build_dir


@pytest.fixture(scope="module")
def needs() -> dict[str, dict[str, object]]:
    result = run_scenario("build", SCENARIO, ":needs_json")
    assert result.artifacts is not None
    return cast(
        "dict[str, dict[str, object]]", load_needs(result.artifacts["needs.json"])
    )


@pytest.mark.bazel_slow
def test_parent_is_linked_from_the_toctree_selected_by_toctree_index(
    build_dir: Path,
):
    """toctree_index = 1 attaches the parent to the second toctree of
    concepts/index.rst ("Mounted bundles") and leaves the first one empty."""
    assert toctrees(build_dir / "concepts" / "index.html") == [
        [],
        ["example_bundle/index.html"],
    ]


@pytest.mark.bazel_slow
def test_child_is_mounted_below_the_parent_at_its_entry_doc(build_dir: Path):
    """The child's mount_at is relative to the parent, and the parent links
    the child's entry_doc ("landing"), not its index."""
    assert toctree_links(build_dir / PARENT_MOUNT / "index.html") == [
        "child/landing.html"
    ]
    assert toctree_links(build_dir / CHILD_MOUNT / "landing.html") == ["index.html"]


@pytest.mark.bazel_slow
def test_docs_build_reports_no_compatibility_findings(build_dir: Path):
    assert_no_compatibility_findings(build_dir)


@pytest.mark.bazel_cached
def test_nested_needs_are_exported_once_below_the_parent_mount(
    needs: dict[str, dict[str, object]],
):
    assert {
        need_id: need["docname"] for need_id, need in needs.items()
    } == dict.fromkeys(
        [
            "gd_req__docs_bzl_nested_bundle",
            "rl__docs_bzl",
            "tool_req__docs_bzl_nested_bundle",
            "wf__docs_bzl",
            "wp__docs_bzl",
        ],
        f"{PARENT_MOUNT}/index",
    )
    assert needs["tool_req__docs_bzl_nested_bundle"]["satisfies"] == [
        "gd_req__docs_bzl_nested_bundle"
    ]


@pytest.mark.bazel_cached
def test_code_target_sources_are_collected_transitively_and_once(
    needs: dict[str, dict[str, object]],
):
    """Source links come through cc_binary -> cc_library, nested filegroups and
    a py_binary that the root and the child both list (reported once). The
    untagged example_main.cc contributes nothing."""
    # source_code_link is one string of "<url><><file>:<line>" entries.
    links = cast("str", needs["tool_req__docs_bzl_nested_bundle"]["source_code_link"])

    assert sorted(link.split("<>")[1] for link in links.split(", ")) == [
        f"{SCENARIO_PATH}/child/example.cc:1",
        f"{SCENARIO_PATH}/child/example.py:14",
        f"{SCENARIO_PATH}/child/filegroup_source.py:14",
    ]


@pytest.mark.bazel_cached
def test_bundle_data_stays_with_the_mount_that_declares_it():
    """Only :parent declares data; the root and the child get none of it.

    The data file is not rendered into any page, so the mounts manifest is
    the only place that shows which mount owns it.
    """
    data = {
        mount["mount_at"]: mount["data"]
        for mount in _manifest_mounts("_mounts_manifest")
    }

    assert data == {
        "": [],
        PARENT_MOUNT: [f"{SCENARIO_PATH}/generated/generated_output.txt"],
        CHILD_MOUNT: [],
    }


@pytest.mark.bazel_cached
def test_aggregate_bundle_keeps_the_declared_bundle_order():
    """Bundles listed in a docs_bundle(bundles=...) keep their declaration order."""
    mounts = _manifest_mounts("ordered_aggregate_manifest")

    assert [(m["mount_at"], m["entry_doc"]) for m in mounts] == [
        ("first", "index"),
        ("second", "landing"),
    ]
