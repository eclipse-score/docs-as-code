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
import sys
from pathlib import Path

import coverage
import pytest

from tools.coverage_report import (
    SCHEMA,
    Branch,
    FileCoverage,
    coverage_data_lcov,
    load_reference,
    load_reports,
    main,
    markdown,
    package_of,
    parse_lcov,
    run_by,
    summarize,
)


def lcov(path: str, *body: str) -> str:
    """Return one LCOV record for ``path``."""
    return "\n".join([f"SF:{path}", *body, "end_of_record"]) + "\n"


def test_a_line_or_branch_counts_as_run_if_any_report_ran_it() -> None:
    merged = parse_lcov(
        lcov("a.py", "DA:1,0", "DA:2,3")
        + lcov("a.py", "BRDA:2,0,jump to line 3,-", "BRDA:2,0,jump to line 4,0")
        # The second report lists the same two branches in the other order.
        + lcov("a.py", "DA:1,1", "DA:2,0")
        + lcov("a.py", "BRDA:2,0,jump to line 4,0", "BRDA:2,0,jump to line 3,2")
    )
    assert merged == {
        "a.py": FileCoverage(
            lines={1: True, 2: True},
            branches={
                Branch(2, 0, "jump to line 3"): True,
                Branch(2, 0, "jump to line 4"): False,
            },
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


# coverage.py warns about the corrupt file it skips; that is the case tested.
@pytest.mark.filterwarnings("ignore::coverage.exceptions.CoverageWarning")
def test_suites_without_usable_data_are_reported_as_no_data(tmp_path: Path) -> None:
    (tmp_path / "a_file").write_text("")
    # The docs.bzl run creates its directory before any Sphinx process runs.
    (tmp_path / "no_data_files").mkdir()
    # What a Sphinx process killed while writing its data could leave behind.
    (tmp_path / "corrupt").mkdir()
    (tmp_path / "corrupt" / ".coverage.host.1.2").write_text("not a database")
    labels = ["missing", "a_file", "no_data_files", "corrupt"]
    suites = load_reports([f"{name}={tmp_path / name}" for name in labels])
    assert suites == {name: None for name in labels}


def write_data(directory: Path, lines: dict[str, list[int]]) -> None:
    """Write a coverage.py data file to ``directory``, as a measured run would.

    A file with no lines is one the run lists but never executed, as
    `source` in pyproject.toml makes coverage.py do for files no test imports.
    """
    directory.mkdir(exist_ok=True)
    data = coverage.CoverageData(
        basename=str(directory / ".coverage"), suffix=f"host.{len(lines)}.1"
    )
    data.add_lines({str(Path(path).resolve()): hit for path, hit in lines.items()})
    data.touch_files([str(Path(path).resolve()) for path in lines])
    data.write()


def test_coverage_py_data_files_become_lcov(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "mod.py").write_text("x = 1\ny = 2\n")
    write_data(tmp_path / "data", {"mod.py": [1]})
    report = coverage_data_lcov(tmp_path / "data")
    assert report.startswith("SF:mod.py\n")
    assert "DA:1,1" in report
    assert "DA:2,0" in report


@pytest.mark.parametrize(
    ("content", "note"),
    [
        (None, "No coverage of main available"),
        ('{"schema": 1, "comm', "could not be read"),
        ('{"schema": 1, "commit": "abc"}', "could not be read"),
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


def test_every_suite_counts_every_file_of_the_combined_report() -> None:
    combined = {
        "a.py": FileCoverage(lines={1: True, 2: True}),
        "unused.py": FileCoverage(lines={1: False}),
    }
    suite = {"a.py": FileCoverage(lines={1: True})}
    assert run_by(suite, combined) == {
        "a.py": FileCoverage(lines={1: True, 2: False}),
        "unused.py": FileCoverage(lines={1: False}),
    }


def test_summary_shows_the_change_against_main(tmp_path: Path) -> None:
    def files(*hits: bool) -> dict[str, FileCoverage]:
        return {"src/a.py": FileCoverage(lines=dict(enumerate(hits, start=1)))}

    before = summarize(
        {"Unit": files(True, False), "Scenarios": None}, files(True, False)
    )
    path = tmp_path / "main.json"
    path.write_text(json.dumps(before.to_json()))
    reference, note = load_reference(path)
    assert note is None

    now = summarize({"Unit": files(True, True), "Scenarios": None}, files(True, True))
    text = markdown(now, reference, note)
    assert "| Unit | 100.0% (2/2) | +50.0% | – | – |" in text
    assert "| Scenarios | no data | – | no data | – |" in text
    assert "Files with changed coverage (1, biggest drop first)" in text


def test_suites_are_reported_apart_and_combined(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BUILD_WORKSPACE_DIRECTORY", raising=False)
    (tmp_path / "a.py").write_text("x = 1\ny = 2\n")
    (tmp_path / "unused.py").write_text("z = 1\n")
    # The unit test run lists unused.py, though no test imports it.
    write_data(tmp_path / "unit", {"a.py": [1], "unused.py": []})
    write_data(tmp_path / "docs", {"a.py": [2]})
    monkeypatch.setattr(
        sys,
        "argv",
        ["coverage_report", "Unit=unit", "Scenarios=docs", "Other=missing"]
        + ["--json", "summary.json"],
    )

    main()

    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["schema"] == SCHEMA
    # Every suite counts the same 3 lines, also the one without unused.py.
    assert summary["suites"] == {
        "Unit": {"lines": [1, 3], "branches": [0, 0]},
        "Scenarios": {"lines": [1, 3], "branches": [0, 0]},
        "Other": None,
    }
    assert summary["combined"] == {"lines": [2, 3], "branches": [0, 0]}
    assert summary["files"]["unused.py"]["lines"] == [0, 1]
    assert "SF:unused.py" in (tmp_path / "coverage.lcov").read_text()
