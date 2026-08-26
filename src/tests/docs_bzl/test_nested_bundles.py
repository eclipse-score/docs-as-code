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

# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
# *******************************************************************************
"""Nested docs_bundle() scenario."""

import json

from src.tests.docs_bzl.helpers import built_output, run_scenario


def test_nested_bundles_render_and_preserve_metadata():
    result = run_scenario("run", "nested_bundles", ":docs")

    manifest = json.loads(
        built_output("scenarios/nested_bundles", "_mounts_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert [mount["mount_at"] for mount in manifest["mounts"]] == [
        "concepts/example_bundle",
        "concepts/example_bundle/child",
    ]
    assert [mount["entry_doc"] for mount in manifest["mounts"]] == [
        "index",
        "landing",
    ]
    # Verify that the parent bundle's data (generated doc output) appears in the manifest.
    parent_mount = next(
        m for m in manifest["mounts"] if m["mount_at"] == "concepts/example_bundle"
    )
    assert parent_mount["data"] == [
        "src/tests/docs_bzl/scenarios/nested_bundles/generated/generated_output.txt",
    ]

    sourcelinks = json.loads(
        built_output("scenarios/nested_bundles", "sourcelinks_json.json").read_text(
            encoding="utf-8"
        )
    )
    assert {link["file"] for link in sourcelinks} == {
        "src/tests/docs_bzl/scenarios/nested_bundles/child/example.py",
        "src/tests/docs_bzl/scenarios/nested_bundles/child/example.cc",
        "src/tests/docs_bzl/scenarios/nested_bundles/child/filegroup_source.py",
    }
    by_file = {link["file"]: link for link in sourcelinks}
    assert (
        by_file["src/tests/docs_bzl/scenarios/nested_bundles/child/example.py"][
            "bazel_target"
        ]
        == "//src/tests/docs_bzl/scenarios/nested_bundles:example_binary"
    )
    assert (
        by_file["src/tests/docs_bzl/scenarios/nested_bundles/child/example.py"][
            "bazel_type"
        ]
        == "py_binary"
    )
    assert (
        by_file["src/tests/docs_bzl/scenarios/nested_bundles/child/example.cc"][
            "bazel_target"
        ]
        == "//src/tests/docs_bzl/scenarios/nested_bundles:example_executable"
    )
    assert (
        by_file["src/tests/docs_bzl/scenarios/nested_bundles/child/example.cc"][
            "bazel_type"
        ]
        == "cc_binary"
    )
    needs = json.loads((result.build_dir / "needs.json").read_text(encoding="utf-8"))
    need = needs["needs"]["doc_concept__child"]
    assert need["bazel_target"] == (
        "//src/tests/docs_bzl/scenarios/nested_bundles:example_binary, "
        "//src/tests/docs_bzl/scenarios/nested_bundles:example_executable, "
        "//src/tests/docs_bzl/scenarios/nested_bundles:nested_filegroup_sources"
    )
    assert need["bazel_type"] == "cc_binary, filegroup, py_binary"
    unlinked_need = needs["needs"]["doc_concept__unlinked"]
    assert unlinked_need["bazel_target"] == need["bazel_target"]
    assert unlinked_need["bazel_type"] == need["bazel_type"]
    assert (result.build_dir / "concepts" / "example_bundle" / "index.html").is_file()
    assert (
        result.build_dir / "concepts" / "example_bundle" / "child" / "landing.html"
    ).is_file()


def test_nested_bundle_aggregator_preserves_declared_order():
    run_scenario("build", "nested_bundles", ":ordered_aggregate_manifest")

    manifest = json.loads(
        built_output(
            "scenarios/nested_bundles", "ordered_aggregate_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert [mount["mount_at"] for mount in manifest["mounts"]] == ["first", "second"]
