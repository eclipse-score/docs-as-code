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
"""Coverage for bundles in nested Bazel packages and source directories."""

from typing import cast

import pytest

from src.tests.docs_bzl.helpers import (
    load_needs,
    load_needs_json,
    run_bazel,
    run_package,
)

PRODUCER = "//src/tests/docs_bzl/scenarios/subdirectory_bundle/producer"
CONSUMER = "//src/tests/docs_bzl/scenarios/subdirectory_bundle/consumer"
EMBEDDED_BUNDLE = "//src/tests/docs_bzl/scenarios/subdirectory_bundle/producer/docs/embedded:docs_bundle"

# The producer's own Needs and the ones of the bundle it embeds at "embedded".
PRODUCER_ROOT_NEEDS = [
    "gd_req__producer_root",
    "rl__test_producer_root",
    "wf__test_producer_root",
    "wp__test_producer_root",
]
EMBEDDED_NEEDS = [
    "gd_req__embedded",
    "rl__test_embedded",
    "wf__test_embedded",
    "wp__test_embedded",
]
CONSUMER_NEEDS = [
    "gd_req__consumer",
    "rl__test_workflow",
    "wf__test_workflow",
    "wp__test_workproduct",
]


def _needs_export(package: str) -> tuple[dict[str, object], dict[str, str]]:
    """Build a package's needs_json and return its metadata and Need docnames."""
    result = run_package("build", package, ":needs_json")
    assert result.artifacts is not None
    needs_json = result.artifacts["needs.json"]
    docnames = {
        need_id: cast("dict[str, str]", need)["docname"]
        for need_id, need in load_needs(needs_json).items()
    }
    return load_needs_json(needs_json), docnames


@pytest.mark.bazel_cached
def test_docs_targets_build_with_a_bundle_in_a_subdirectory():
    targets = [
        "docs",
        "docs_check",
        "docs_link_check",
        "live_preview",
        "ide_support",
        "docs_bundle",
        "sourcelinks_json",
        "needs_json",
        "metrics_json",
        "needs_json_file",
        "traceability_gate",
    ]
    run_bazel(
        [
            "build",
            *[
                f"{package}:{target}"
                for package in (PRODUCER, CONSUMER)
                for target in targets
            ],
        ]
    )


@pytest.mark.bazel_cached
def test_parent_needs_export_does_not_depend_on_mounted_child_bundle():
    """The root's local Needs export must use its source-only provider.

    The public ``docs_bundle`` provider includes the embedded child for
    rendering. Querying dependencies of ``needs_local`` verifies that its
    source-only provider prevents the export action from pulling that child
    into the parent's ownership boundary.
    """
    result = run_bazel(
        [
            "query",
            f"deps({PRODUCER}:docs.__internal__.needs_local)",
            "--output=label",
        ]
    )

    dependencies = set(result.stdout.splitlines())
    assert f"{PRODUCER}:docs_bundle.__internal__.source_bundle" in dependencies
    assert EMBEDDED_BUNDLE not in dependencies


@pytest.mark.bazel_cached
def test_producer_exports_its_own_and_embedded_needs():
    """Needs of the embedded bundle are exported below its mount point."""
    data, docnames = _needs_export("scenarios/subdirectory_bundle/producer")

    assert data["project"] == "Subdirectory Bundle Producer"
    assert docnames == {
        **dict.fromkeys(PRODUCER_ROOT_NEEDS, "index"),
        **dict.fromkeys(EMBEDDED_NEEDS, "embedded/index"),
    }


@pytest.mark.bazel_cached
def test_consumer_exports_the_mounted_producer_needs_below_its_mount():
    """Mounting the producer moves all its Needs, embedded ones included,
    below "producer/" in the consumer's export, each exactly once."""
    data, docnames = _needs_export("scenarios/subdirectory_bundle/consumer")

    assert data["project"] == "Subdirectory Bundle Consumer"
    assert docnames == {
        **dict.fromkeys(CONSUMER_NEEDS, "index"),
        **dict.fromkeys(PRODUCER_ROOT_NEEDS, "producer/index"),
        **dict.fromkeys(EMBEDDED_NEEDS, "producer/embedded/index"),
    }


@pytest.mark.bazel_slow
def test_consumer_can_render_and_run_documentation_checks():
    """Runtime rendering and documentation checks work across package boundaries."""
    producer_result = run_package(
        "run", "scenarios/subdirectory_bundle/producer", ":docs"
    )
    assert (producer_result.build_dir / "embedded" / "index.html").is_file()

    consumer_result = run_package(
        "run", "scenarios/subdirectory_bundle/consumer", ":docs"
    )
    assert (consumer_result.build_dir / "producer" / "index.html").is_file()
    assert (
        consumer_result.build_dir / "producer" / "embedded" / "index.html"
    ).is_file()

    run_package("run", "scenarios/subdirectory_bundle/consumer", ":docs_check")
    run_package("run", "scenarios/subdirectory_bundle/consumer", ":docs_link_check")
