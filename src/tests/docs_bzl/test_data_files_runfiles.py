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

"""Verify that genrule-generated RST sources are reachable at ``bazel run`` time.

The ``srcs`` attribute of ``docs_bundle`` can carry genrule outputs that live
in ``bazel-out/.../bin/``. The bundle stages them into the runfiles of
``:docs``; ``score_mounts`` then resolves the generated source root through
``<ws_root>/bazel-bin`` and mounts it. This end-to-end test fails if either half
of that chain regresses."""

from src.tests.docs_bzl.helpers import built_output, run_bazel, run_scenario


def test_generated_source_files_reachable_at_runtime():
    """Genrule output in a docs_bundle src dep must be resolved by Sphinx."""
    result = run_scenario("run", "data_files_runfiles", ":docs")

    generated_html = result.build_dir / "data_test" / "index.html"

    assert "Generated Data Page" in generated_html.read_text(encoding="utf-8")
    assert "generated-data-diagram" in generated_html.read_text(encoding="utf-8")


def test_legacy_generated_data_files_remain_reachable_at_runtime():
    """Legacy generated RST files declared through ``data`` still work."""
    result = run_scenario("run", "data_files_runfiles", ":docs")

    legacy_html = result.build_dir / "legacy_data_test" / "index.html"

    assert "Legacy Data Page" in legacy_html.read_text(encoding="utf-8")


def test_explicit_source_bundle_excludes_undeclared_siblings():
    """Explicit source bundles must not recursively mount undeclared files."""
    result = run_scenario("run", "data_files_runfiles", ":docs")

    declared_html = result.build_dir / "isolated_test" / "index.html"
    undeclared_html = result.build_dir / "isolated_test" / "undeclared.html"

    assert "Isolated Declared Page" in declared_html.read_text(encoding="utf-8")
    assert not undeclared_html.exists()


def test_explicit_source_bundles_export_local_needs_from_their_source_root():
    """Explicit source targets are staged with their bundle entry as the root."""
    run_bazel(
        [
            "build",
            "//src/tests/docs_bzl/scenarios/data_files_runfiles:data_bundle.__internal__.needs_local",
            "//src/tests/docs_bzl/scenarios/data_files_runfiles:isolated_source_bundle.__internal__.needs_local",
        ]
    )

    for target in ("data_bundle", "isolated_source_bundle"):
        needs_output = built_output(
            "scenarios/data_files_runfiles",
            f"{target}.__internal__.needs_local/_build/needs/needs.json",
        )
        assert needs_output.is_file()
