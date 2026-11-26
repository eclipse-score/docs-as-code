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
    CONSUMER_ROOT,
    load_needs,
    load_needs_json,
    run_bazel,
    run_package,
)

PRODUCER = "//subdirectory_bundle/producer"
CONSUMER = "//subdirectory_bundle/consumer"
EMBEDDED_BUNDLE = "//subdirectory_bundle/producer/docs/embedded:docs_bundle"

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


# One linked chain per layer (consumer, producer root, embedded):
# (gd_req, workflow, workproduct, role). The gd_req satisfies the workflow;
# the workflow uses the workproduct as input/output and the role as
# approver/responsible. Sphinx-Needs adds the matching *_back links.
LINKED_NEEDS = [
    (
        "gd_req__consumer",
        "wf__test_workflow",
        "wp__test_workproduct",
        "rl__test_workflow",
    ),
    (
        "gd_req__producer_root",
        "wf__test_producer_root",
        "wp__test_producer_root",
        "rl__test_producer_root",
    ),
    ("gd_req__embedded", "wf__test_embedded", "wp__test_embedded", "rl__test_embedded"),
]
LINK_FIELDS = {
    "gd_req": ["satisfies"],
    "workflow": ["approved_by", "input", "output", "responsible", "satisfies_back"],
    "workproduct": ["input_back", "output_back"],
    "role": ["approved_by_back", "responsible_back"],
}


def _needs_export(
    package: str,
) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    """Build a package's needs_json and return its metadata and Needs."""
    result = run_package("build", package, ":needs_json")
    assert result.artifacts is not None
    needs_json = result.artifacts["needs.json"]
    needs = cast("dict[str, dict[str, object]]", load_needs(needs_json))
    return load_needs_json(needs_json), needs


def _docnames(needs: dict[str, dict[str, object]]) -> dict[str, object]:
    return {need_id: need["docname"] for need_id, need in needs.items()}


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
        ],
        cwd=CONSUMER_ROOT,
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
        ],
        cwd=CONSUMER_ROOT,
    )

    dependencies = set(result.stdout.splitlines())
    assert f"{PRODUCER}:docs_bundle.__internal__.source_bundle" in dependencies
    assert EMBEDDED_BUNDLE not in dependencies


@pytest.mark.bazel_cached
def test_producer_exports_its_own_and_embedded_needs():
    """Needs of the embedded bundle are exported below its mount point."""
    data, needs = _needs_export("consumer/subdirectory_bundle/producer")

    assert data["project"] == "Subdirectory Bundle Producer"
    assert _docnames(needs) == {
        **dict.fromkeys(PRODUCER_ROOT_NEEDS, "index"),
        **dict.fromkeys(EMBEDDED_NEEDS, "embedded/index"),
    }


@pytest.mark.bazel_cached
def test_consumer_exports_the_mounted_producer_needs_below_its_mount():
    """Mounting the producer moves all its Needs, embedded ones included,
    below "producer/" in the consumer's export, each exactly once."""
    data, needs = _needs_export("consumer/subdirectory_bundle/consumer")

    assert data["project"] == "Subdirectory Bundle Consumer"
    assert _docnames(needs) == {
        **dict.fromkeys(CONSUMER_NEEDS, "index"),
        **dict.fromkeys(PRODUCER_ROOT_NEEDS, "producer/index"),
        **dict.fromkeys(EMBEDDED_NEEDS, "producer/embedded/index"),
    }


@pytest.mark.bazel_cached
def test_consumer_resolves_links_of_mounted_needs():
    """After both mounts, every layer's links and back links still resolve."""
    _, needs = _needs_export("consumer/subdirectory_bundle/consumer")

    expected: dict[str, dict[str, list[str]]] = {}
    for gd_req, workflow, workproduct, role in LINKED_NEEDS:
        expected[gd_req] = {"satisfies": [workflow]}
        expected[workflow] = {
            "approved_by": [role],
            "input": [workproduct],
            "output": [workproduct],
            "responsible": [role],
            "satisfies_back": [gd_req],
        }
        expected[workproduct] = dict.fromkeys(LINK_FIELDS["workproduct"], [workflow])
        expected[role] = dict.fromkeys(LINK_FIELDS["role"], [workflow])

    assert {
        need_id: {
            # needs.json drops empty link fields, so a broken link is a missing key.
            field: need.get(field, [])
            for field in LINK_FIELDS[cast("str", need["type"])]
        }
        for need_id, need in needs.items()
    } == expected


@pytest.mark.bazel_slow
def test_consumer_can_render_and_run_documentation_checks():
    """Runtime rendering and documentation checks work across package boundaries."""
    producer_result = run_package(
        "run", "consumer/subdirectory_bundle/producer", ":docs"
    )
    assert (producer_result.build_dir / "embedded" / "index.html").is_file()

    consumer_result = run_package(
        "run", "consumer/subdirectory_bundle/consumer", ":docs"
    )
    assert (consumer_result.build_dir / "producer" / "index.html").is_file()
    assert (
        consumer_result.build_dir / "producer" / "embedded" / "index.html"
    ).is_file()

    run_package("run", "consumer/subdirectory_bundle/consumer", ":docs_check")
    run_package("run", "consumer/subdirectory_bundle/consumer", ":docs_link_check")
