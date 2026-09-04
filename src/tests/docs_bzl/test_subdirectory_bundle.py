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

import pytest

from src.tests.docs_bzl.helpers import run_bazel, run_package

PRODUCER = "//src/tests/docs_bzl/scenarios/subdirectory_bundle/producer"
CONSUMER = "//src/tests/docs_bzl/scenarios/subdirectory_bundle/consumer"


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
