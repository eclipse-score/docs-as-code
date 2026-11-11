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
"""subdirectory_bundle: bundles in nested Bazel packages and source directories.

``producer`` mounts a bundle from its own sub-package; ``consumer`` mounts the
whole producer and therefore receives the embedded bundle transitively.
"""

from typing import Any

import pytest

from src.tests.end_to_end.testcases.helpers import load_needs, run_bazel, run_package

PRODUCER_PACKAGE = "scenarios/subdirectory_bundle/producer"
CONSUMER_PACKAGE = "scenarios/subdirectory_bundle/consumer"
PRODUCER = f"//{PRODUCER_PACKAGE}"
CONSUMER = f"//{CONSUMER_PACKAGE}"
EMBEDDED_BUNDLE = f"{PRODUCER}/docs/embedded:docs_bundle"


def _docnames(package: str) -> dict[str, str]:
    result = run_package("build", package, ":needs_json")
    assert result.artifacts is not None
    needs: dict[str, Any] = load_needs(result.artifacts["needs.json"])
    return {need_id: need["docname"] for need_id, need in needs.items()}


@pytest.mark.bazel_cached
def test_all_public_docs_targets_build_with_a_bundle_in_a_subdirectory():
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
def test_producer_exports_its_subpackage_bundle_needs():
    assert _docnames(PRODUCER_PACKAGE) == {
        "gd_req__producer_root": "index",
        "gd_req__embedded": "embedded/index",
    }


@pytest.mark.bazel_cached
def test_consumer_receives_transitive_bundle_needs_once():
    """The embedded bundle reaches the consumer through the producer, once."""
    assert _docnames(CONSUMER_PACKAGE) == {
        "gd_req__consumer": "index",
        "gd_req__producer_root": "producer/index",
        "gd_req__embedded": "producer/embedded/index",
    }


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


@pytest.mark.bazel_slow
def test_producer_renders_its_subpackage_page():
    result = run_package("run", PRODUCER_PACKAGE, ":docs")
    assert (result.build_dir / "embedded" / "index.html").is_file()


@pytest.mark.bazel_slow
def test_consumer_renders_transitive_pages():
    result = run_package("run", CONSUMER_PACKAGE, ":docs")
    assert (result.build_dir / "producer" / "index.html").is_file()
    assert (result.build_dir / "producer" / "embedded" / "index.html").is_file()


@pytest.mark.bazel_slow
def test_consumer_docs_check_passes():
    run_package("run", CONSUMER_PACKAGE, ":docs_check")


@pytest.mark.bazel_slow
def test_consumer_link_check_passes():
    run_package("run", CONSUMER_PACKAGE, ":docs_link_check")
