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
"""Verify coverage attribution, workflow artifact discovery and documentation cache reuse."""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from src.docs_cli.lcov_summary import (
    load_code_file_lists,
    parse_lcov,
    summarize,
)
from src.tests.docs_bzl.helpers import (
    built_output,
    repo_root,
    run_bazel,
    run_scenario,
    staged_coverage_report,
)


@pytest.fixture
def workflow_coverage() -> Iterator[Path]:
    """Stage the workflow artifact at its conventional path, preserving local data."""
    fixture = (
        repo_root()
        / "src/tests/docs_bzl/scenarios/reference_integration/modern_module/coverage.info"
    )
    with staged_coverage_report(fixture) as report:
        yield report


@pytest.mark.bazel_cached
def test_coverage_summary_uses_existing_bounded_implementation_files(
    workflow_coverage: Path,
):
    scenario = "reference_integration/modern_module"
    run_scenario("build", scenario, ":docs_bundle.__internal__.code_file_lists")
    folder = f"scenarios/{scenario}"
    manifest = json.loads(
        built_output(
            folder, "docs_bundle.__internal__.code_file_lists.json"
        ).read_text()
    )
    assert len(manifest["code_file_lists"]) == 1
    code_file_list = manifest["code_file_lists"][0]
    assert code_file_list["primary_need_id"] == "comp__modern_component"
    prefix = f"src/tests/docs_bzl/{folder}/docs/components/"
    # These are exactly the existing private collection's files: selected
    # sibling headers and local leaves behind excluded dependencies survive,
    # while sibling implementation files and external malloc sources do not.
    assert code_file_list["files"] == [
        {"repository": "_main", "path": prefix + path}
        for path in (
            "component/api.h",
            "component/detail/support.cc",
            "component/generated/config.def",
            "component/implementation.cc",
            "component/implementation.py",
            "unlinked_component/api.h",
        )
    ]
    summary: dict[str, object] = {
        "version": 1,
        "coverage_summaries": summarize(
            load_code_file_lists(
                built_output(folder, "docs_bundle.__internal__.code_file_lists.json")
            ),
            parse_lcov(workflow_coverage.read_text(encoding="utf-8")),
        ),
    }
    assert summary == {
        "version": 1,
        "coverage_summaries": [
            {
                "primary_need_id": "comp__modern_component",
                "files": {"total": 6, "measured": 2},
                "lines": {"total": 3, "percent": 67},
                "branches": {"total": 2, "percent": 100},
            }
        ],
    }


@pytest.mark.bazel_cached
def test_primary_need_types_empty_files_and_explicit_external_targets():
    """A module primary Need and a component primary Need both retain code ownership."""
    scenario = "coverage_summary"
    run_scenario("build", scenario, ":aggregate.__internal__.code_file_lists")
    manifest = json.loads(
        built_output(
            f"scenarios/{scenario}", "aggregate.__internal__.code_file_lists.json"
        ).read_text()
    )
    assert [entry["primary_need_id"] for entry in manifest["code_file_lists"]] == [
        "comp__files",
        "mod__empty",
    ]
    assert manifest["code_file_lists"][1]["files"] == []
    files = manifest["code_file_lists"][0]["files"]
    assert {
        "repository": "bazel_tools",
        "path": "tools/cpp/runfiles/runfiles.h",
    } in files
    assert len(files) == len({(file["repository"], file["path"]) for file in files})
    result = {
        "coverage_summaries": summarize(
            load_code_file_lists(
                built_output(
                    f"scenarios/{scenario}",
                    "aggregate.__internal__.code_file_lists.json",
                )
            ),
            parse_lcov(
                (
                    repo_root()
                    / f"src/tests/docs_bzl/scenarios/{scenario}/coverage.info"
                ).read_text(encoding="utf-8")
            ),
        )
    }
    assert len(result["coverage_summaries"]) == 2
    assert result["coverage_summaries"][1]["primary_need_id"] == "mod__empty"
    assert result["coverage_summaries"][1]["files"] == {"total": 0, "measured": 0}
    # The external zero-hit header contributes alongside the local hit. Matching
    # solely on a workspace path would incorrectly report 100% here.
    assert result["coverage_summaries"][0]["lines"] == {"total": 2, "percent": 50}


@pytest.mark.bazel_slow
def test_conflicting_primary_need_ids_fail_instead_of_overwriting_membership():
    result = run_bazel(
        [
            "build",
            "//src/tests/docs_bzl/scenarios/coverage_summary:conflict.__internal__.code_file_lists",
        ],
        expect_error=True,
    )
    assert "belongs to multiple bundles" in result.stderr


@pytest.mark.bazel_slow
def test_docs_use_summary_and_reuse_cache_for_equivalent_measurements(
    workflow_coverage: Path,
):
    """An ordinary docs() consumer needs only its completed coverage report."""
    scenario = "reference_integration/modern_module"
    package = repo_root() / "src/tests/docs_bzl/scenarios" / scenario
    report = workflow_coverage
    original = report.read_bytes()
    output = package / "_build"
    summary_path = package / "_build/coverage_summary.json"
    try:
        run_scenario("run", scenario, ":docs")
        summary = summary_path.read_bytes()
        component_page = output / "components/component/index.html"
        html = component_page.read_text()
        assert html.count("score-coverage") == 1
        assert "67%" in html and "100%" in html
        assert "files 2/6" in html
        unselected = (output / "components/unlinked_component/index.html").read_text()
        assert "score-coverage" not in unselected
        witness = output / "coverage-cache-witness"
        witness.touch()
        # A different positive execution counter leaves every summarized item unchanged.
        report.write_bytes(original.replace(b"DA:1,2", b"DA:1,900", 1))
        run_scenario("run", scenario, ":docs")
        assert summary_path.read_bytes() == summary
        assert witness.exists(), (
            "Equivalent rounded results must preserve the docs cache"
        )

        # Removing the only hit for this line changes 2/3 covered lines to 1/3.
        report.write_bytes(original.replace(b"DA:1,2", b"DA:1,0", 1))
        run_scenario("run", scenario, ":docs")
        assert not witness.exists(), "Changed coverage must invalidate the docs cache"
        changed = json.loads(summary_path.read_text())
        assert changed["coverage_summaries"][0]["lines"]["percent"] == 33
        assert "33%" in component_page.read_text()

        # An invalid workspace report cannot affect the sandboxed Needs export.
        report.write_text("SF:broken\nDA:invalid\n")
        result = run_scenario("build", scenario, ":needs_json")
        assert result.artifacts is not None
        assert "coverage_summary.json" not in result.artifacts
    finally:
        report.write_bytes(original)


@pytest.mark.bazel_cached
@pytest.mark.parametrize("target", ["needs_json", "docs_check", "docs_link_check"])
def test_documentation_checks_do_not_consume_coverage_file_lists(target: str):
    """Coverage metadata is used only by the rendering CLI, outside the Needs graph."""
    package = "//src/tests/docs_bzl/scenarios/reference_integration/modern_module"
    result = run_bazel(
        [
            "aquery",
            f"inputs('.*code_file_lists[.]json', deps({package}:{target}))",
        ]
    )
    assert not result.stdout.strip()


@pytest.mark.bazel_slow
def test_optional_workflow_report_tracks_appearance_changes_and_removal(
    workflow_coverage: Path,
):
    """Each CLI invocation reads the report even when Bazel inputs are unchanged."""
    original = workflow_coverage.read_bytes()
    scenario = "reference_integration/modern_module"

    def result():
        rendered = run_scenario("run", scenario, ":docs")
        return json.loads((rendered.build_dir / "coverage_summary.json").read_text())[
            "coverage_summaries"
        ][0]

    workflow_coverage.unlink()
    assert result()["files"] == {"total": 6, "measured": 0}
    workflow_coverage.write_bytes(original)
    assert result()["lines"]["percent"] == 67
    workflow_coverage.write_bytes(original.replace(b"DA:1,2", b"DA:1,0", 1))
    assert result()["lines"]["percent"] == 33
    workflow_coverage.unlink()
    assert result()["files"] == {"total": 6, "measured": 0}
