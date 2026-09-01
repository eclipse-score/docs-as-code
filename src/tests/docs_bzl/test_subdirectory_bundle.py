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

from src.tests.docs_bzl.helpers import load_needs, run_bazel, run_package

PRODUCER = "//src/tests/docs_bzl/scenarios/subdirectory_bundle/producer"
CONSUMER = "//src/tests/docs_bzl/scenarios/subdirectory_bundle/consumer"


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


def test_producer_needs_include_subdirectory_bundle_once():
    result = run_package(
        "build", "scenarios/subdirectory_bundle/producer", ":needs_json"
    )
    assert result.artifacts is not None

    needs = load_needs(result.artifacts["needs.json"])
    assert set(needs) == {
        "gd_req__producer_root",
        "gd_req__embedded",
    }


def test_consumer_can_render_and_check_transitive_bundle_without_duplicate_needs():
    result = run_package(
        "build", "scenarios/subdirectory_bundle/consumer", ":needs_json"
    )
    assert result.artifacts is not None
    needs = load_needs(result.artifacts["needs.json"])
    assert set(needs) == {
        "gd_req__producer_root",
        "gd_req__embedded",
        "gd_req__consumer",
    }

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
