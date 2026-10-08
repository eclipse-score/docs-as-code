# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Unit tests for merging coverage reports and comparing them with main."""

import json
import subprocess
import sys
from pathlib import Path

import coverage
import pytest

from tools.coverage_report import (
    SCHEMA,
    FileCoverage,
    coverage_data_lcov,
    is_test_file,
    lcov_records,
    load_reference,
    load_reports,
    main,
    markdown,
    numeric_branches,
    package_of,
    parse_lcov,
    summarize,
)


def lcov(path: str, *body: str) -> str:
    """Return one LCOV record for ``path``."""
    return "\n".join([f"SF:{path}", *body, "end_of_record"]) + "\n"


@pytest.mark.parametrize(
    ("path", "is_test"),
    [
        ("src/tests/helpers.py", True),
        ("src/extensions/x/test/data.py", True),
        ("src/extensions/x/test_checks.py", True),
        ("tools/tests/coverage_report_test.py", True),
        ("conftest.py", True),
        ("src/extensions/x/checks.py", False),
        # Only whole directory and file names count, not parts of them.
        ("src/testing/latest.py", False),
        ("src/extensions/x/contest.py", False),
    ],
)
def test_test_files_are_recognised_by_directory_or_name(
    path: str, is_test: bool
) -> None:
    assert is_test_file(path) is is_test


def test_lcov_is_split_into_its_records() -> None:
    first = lcov("a.py", "DA:1,1")
    second = lcov("b.py", "DA:2,0")
    # Lines outside a record, like a test name, belong to no record.
    assert lcov_records("TN:\n" + first + second) == [
        ("a.py", first),
        ("b.py", second),
    ]


def test_a_branch_gets_the_same_number_in_every_report() -> None:
    names: dict[tuple[str, str, str], list[str]] = {}
    first = numeric_branches(
        lcov("a.py", "BRDA:3,0,jump to line 4,1", "BRDA:3,0,jump to line 6,0"), names
    )
    # The second report lists the same two branches in the other order.
    second = numeric_branches(
        lcov("a.py", "BRDA:3,0,jump to line 6,1", "BRDA:3,0,jump to line 4,-"), names
    )
    assert first == lcov("a.py", "BRDA:3,0,0,1", "BRDA:3,0,1,0")
    assert second == lcov("a.py", "BRDA:3,0,1,1", "BRDA:3,0,0,-")


def test_a_line_or_branch_counts_as_run_if_any_report_ran_it() -> None:
    merged = parse_lcov(
        lcov("a.py", "DA:1,0", "DA:2,3", "BRDA:2,0,0,-", "BRDA:2,0,1,0")
        + lcov("a.py", "DA:1,1", "DA:2,0", "BRDA:2,0,0,2", "BRDA:2,0,1,0")
    )
    assert merged == {
        "a.py": FileCoverage(
            lines={1: True, 2: True},
            branches={(2, 0, 0): True, (2, 0, 1): False},
        )
    }


@pytest.mark.parametrize(
    ("path", "package"),
    [
        (
            "src/extensions/score_metamodel/checks/graph.py",
            "src/extensions/score_metamodel",
        ),
        ("src/helper_lib/__init__.py", "src/helper_lib"),
        ("setup.py", "."),
    ],
)
def test_files_are_grouped_per_extension_else_per_directory(
    path: str, package: str
) -> None:
    assert package_of(path) == package


def test_reports_keep_only_tracked_files(tmp_path: Path) -> None:
    report = tmp_path / "unit.lcov"
    report.write_text(lcov("a.py", "DA:1,1") + lcov("venv/lib.py", "DA:1,1"))
    assert load_reports([f"Unit={report}"], {"a.py"}, {}) == [
        ("Unit", lcov("a.py", "DA:1,1"))
    ]


# coverage.py warns about the corrupt file it skips; that is the case tested.
@pytest.mark.filterwarnings("ignore::coverage.exceptions.CoverageWarning")
def test_suites_without_usable_data_are_reported_as_no_data(tmp_path: Path) -> None:
    (tmp_path / "empty.lcov").write_text("")
    (tmp_path / "untracked.lcov").write_text(lcov("venv/lib.py", "DA:1,1"))
    # The docs.bzl run creates its directory before any Sphinx process runs.
    (tmp_path / "no_data_files").mkdir()
    # What a Sphinx process killed while writing its data could leave behind.
    (tmp_path / "corrupt").mkdir()
    (tmp_path / "corrupt" / ".coverage.host.1.2").write_text("not a database")
    labels = ["missing", "empty.lcov", "untracked.lcov", "no_data_files", "corrupt"]
    suites = load_reports(
        [f"{name}={tmp_path / name}" for name in labels], {"a.py"}, {}
    )
    assert suites == [(name, None) for name in labels]


def test_coverage_py_data_files_become_lcov(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tmp_path = tmp_path.resolve()
    monkeypatch.chdir(tmp_path)
    (tmp_path / "mod.py").write_text("x = 1\ny = 2\n")
    (tmp_path / "data").mkdir()
    data = coverage.CoverageData(
        basename=str(tmp_path / "data" / ".coverage"), suffix="host.1.2"
    )
    data.add_lines({str(tmp_path / "mod.py"): [1]})
    data.write()
    report = coverage_data_lcov(tmp_path / "data")
    assert report.startswith("SF:mod.py\n")
    assert "DA:1,1" in report
    assert "DA:2,0" in report


@pytest.mark.parametrize(
    ("content", "note"),
    [
        (None, "No coverage of main available"),
        ('{"schema": 1, "comm', "could not be read"),
        ('{"commit": "abc"}', "older format"),
        ("[1]", "older format"),
    ],
)
def test_unusable_numbers_of_main_give_a_note_instead_of_a_comparison(
    tmp_path: Path, content: str | None, note: str
) -> None:
    path = tmp_path / "main.json"
    if content is not None:
        path.write_text(content)
    reference, message = load_reference(path)
    assert reference is None
    assert message is not None and note in message


def test_summary_shows_the_change_against_main(tmp_path: Path) -> None:
    def files(*hits: bool) -> dict[str, FileCoverage]:
        return {"src/a.py": FileCoverage(lines=dict(enumerate(hits, start=1)))}

    before = summarize(
        [("Unit", files(True, False)), ("Scenarios", None)], files(True, False)
    )
    path = tmp_path / "main.json"
    path.write_text(json.dumps(before))
    reference, note = load_reference(path)
    assert note is None

    now = summarize(
        [("Unit", files(True, True)), ("Scenarios", None)], files(True, True)
    )
    text = markdown(now, reference, note)
    assert "| Unit | 100.0% (2/2) | +50.0% | – | – |" in text
    assert "| Scenarios | no data | – | no data | – |" in text
    assert "Files with changed coverage (1, biggest drop first)" in text


def test_files_no_test_imports_are_added_at_zero_percent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BUILD_WORKSPACE_DIRECTORY", raising=False)
    (tmp_path / "tested.py").write_text("x = 1\n")
    (tmp_path / "untested.py").write_text("y = 1\n")
    (tmp_path / "test_tested.py").write_text("def test_x():\n    pass\n")
    subprocess.run(["git", "init", "-q"], check=True)
    subprocess.run(["git", "add", "."], check=True)
    (tmp_path / "unit.lcov").write_text(lcov("tested.py", "DA:1,1"))
    monkeypatch.setattr(
        sys,
        "argv",
        ["coverage_report", "Unit=unit.lcov", "Scenarios=missing"]
        + ["--json", "summary.json"],
    )

    main()

    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["schema"] == SCHEMA
    assert summary["suites"] == {
        "Unit": {"lines": [1, 2], "branches": [0, 0]},
        "Scenarios": None,
    }
    # Test files are not code under test.
    assert sorted(summary["files"]) == ["tested.py", "untested.py"]
    assert summary["files"]["untested.py"]["lines"] == [0, 1]
    assert "SF:untested.py" in (tmp_path / "coverage.lcov").read_text()
