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
"""Merge Python coverage reports and add every tracked file no test imports.

Coverage reports only contain files that some test imported; a file no test
touches is simply absent. This tool merges the given reports and adds every
tracked non-test Python file at 0%, so untested files show up. Reports are
LCOV files or directories of coverage.py data files (the docs.bzl scenario
run's), optionally labelled as ``LABEL=PATH``:

    bazel coverage //... --combined_report=lcov --build_tests_only
    bazel run //tools:coverage_report -- \\
        "Unit tests=bazel-out/_coverage/_coverage_report.dat" \\
        "docs.bzl scenarios=.coverage_docs_bzl" --markdown summary.md
    genhtml --branch-coverage coverage.lcov -o genhtml

genhtml must be LCOV 2.x: coverage.py names its branches ("jump to line 45"),
which lcov/genhtml 1.x silently drop.

To show what a change does to coverage, write the numbers of main with
``--json main.json`` and pass them to a later run with ``--compare-with
main.json``. The Markdown summary then shows the change per suite, package and
file. CI takes main.json from the latest run on main.

LCOV, the format most examples below show, has one record per source file::

    SF:src/app.py    the record of src/app.py starts
    DA:3,1           line 3 ran once                     (DA:<line>,<hits>)
    BRDA:2,0,jump to line 4,-
                     the branch of block 0 from line 2   (BRDA:<line>,<block>,
                     to line 4 did not run: "-" means      <branch>,<taken>)
                     line 2 never ran, "0" that it ran
                     but took the other branch
    LF, LH, FN*,     totals and functions; ignored here
    BRF, BRH
    end_of_record    the record ends

The examples in the docstrings all use this small repository::

    src/app.py              1  def check(x):
                            2      if x:
                            3          return "yes"
                            4      return "no"
    src/unused.py           1  VALUE = 1          (no test imports it)
    src/tests/test_app.py   a test, so not code under test

The "Unit tests" suite ran ``check(True)`` (lines 1, 2, 3), the "docs.bzl
scenarios" suite ran ``check(False)`` (lines 1, 2, 4).
"""

import argparse
import json
import os
import subprocess
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath
from typing import Any, Self, cast

import coverage
from coverage.exceptions import NoDataError

# Tests are not code under test; listing them would only add 0% noise.
TEST_DIRECTORIES = {"test", "tests"}
TEST_FILE_PATTERNS = ("test_*.py", "*_test.py", "conftest.py")
# Lets coverage_comment.yml find and update its earlier comment instead of
# adding a new one on every push.
COMMENT_MARKER = "<!-- python-coverage-report -->"
# Version of the --json format. Raise it whenever that format changes, so a
# pull request does not compare against numbers of main it cannot read.
SCHEMA = 1


@dataclass(frozen=True)
class Branch:
    """One branch of a source file, as named in a BRDA line.

    Example: ``BRDA:2,0,jump to line 3,1`` is the branch
    ``Branch(line=2, block=0, name="jump to line 3")``.
    """

    line: int
    block: int
    name: str


@dataclass
class FileCoverage:
    """Executed state of each line and branch of one source file.

    Example, src/app.py after the Unit tests ran ``check(True)``::

        FileCoverage(
            lines={1: True, 2: True, 3: True, 4: False},
            branches={
                Branch(2, 0, "jump to line 3"): True,
                Branch(2, 0, "jump to line 4"): False,
            },
        )
    """

    lines: dict[int, bool] = field(default_factory=dict[int, bool])
    branches: dict[Branch, bool] = field(default_factory=dict[Branch, bool])


@dataclass
class Record:
    """One LCOV record: the file it covers and its text, SF: to end_of_record.

    Example: ``Record("src/app.py", "SF:src/app.py\\nDA:1,1\\nend_of_record\\n")``.
    """

    source: str
    text: str


def _percent(column: tuple[int, int] | None) -> float | None:
    """Return the percentage of a (hit, total) column, None if there is none.

    Example::

        (3, 5)  -> 60.0
        (0, 0)  -> None   nothing to run, e.g. a file without branches
        None    -> None   no data
    """
    if not column or not column[1]:
        return None
    hit, total = column
    return 100 * hit / total


@dataclass
class TotalCoverage:
    """How many lines and branches of a file, package or suite ran.

    Example: src/app.py after the Unit tests (see FileCoverage)::

        TotalCoverage(lines_hit=3, lines_total=4, branches_hit=1, branches_total=2)

    In the --json file: ``{"lines": [3, 4], "branches": [1, 2]}``.
    """

    lines_hit: int
    lines_total: int
    branches_hit: int
    branches_total: int

    @classmethod
    def of(cls, files: list[FileCoverage]) -> Self:
        """Return how many lines and branches of ``files`` ran.

        Example: src/app.py after the Unit tests (lines 3 of 4, branches 1 of
        2) plus src/unused.py (its 1 line not run): ``TotalCoverage(3, 5, 1, 2)``.
        """
        lines = [hit for f in files for hit in f.lines.values()]
        branches = [hit for f in files for hit in f.branches.values()]
        return cls(sum(lines), len(lines), sum(branches), len(branches))

    @property
    def lines_percent(self) -> float | None:
        return _percent((self.lines_hit, self.lines_total))

    def to_json(self) -> dict[str, list[int]]:
        return {
            "lines": [self.lines_hit, self.lines_total],
            "branches": [self.branches_hit, self.branches_total],
        }

    @classmethod
    def from_json(cls, data: dict[str, list[int]]) -> Self:
        lines_hit, lines_total = data["lines"]
        branches_hit, branches_total = data["branches"]
        return cls(lines_hit, lines_total, branches_hit, branches_total)


@dataclass
class Summary:
    """The numbers of the summary, per suite, package and file.

    Also written as JSON: a pull request compares its numbers with the ones
    the latest main run stored.

    Example, after both suites ran (see the module docstring)::

        Summary(
            commit="1a2b3c4d5e6f...",
            suites={
                "Unit tests": TotalCoverage(3, 5, 1, 2),
                "docs.bzl scenarios": TotalCoverage(3, 5, 1, 2),
            },
            combined=TotalCoverage(4, 5, 2, 2),
            packages={"src": TotalCoverage(4, 5, 2, 2)},
            files={
                "src/app.py": TotalCoverage(4, 4, 2, 2),
                "src/unused.py": TotalCoverage(0, 1, 0, 0),
            },
        )

    A suite without data has None instead of TotalCoverage.
    """

    commit: str
    suites: dict[str, TotalCoverage | None]
    combined: TotalCoverage
    packages: dict[str, TotalCoverage]
    files: dict[str, TotalCoverage]

    def to_json(self) -> dict[str, Any]:
        """Return the --json content, with TotalCoverage as in its docstring."""
        return {
            "schema": SCHEMA,
            "commit": self.commit,
            "suites": {
                label: c.to_json() if c else None for label, c in self.suites.items()
            },
            "combined": self.combined.to_json(),
            "packages": {name: c.to_json() for name, c in self.packages.items()},
            "files": {path: c.to_json() for path, c in self.files.items()},
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Self:
        """Return the Summary of to_json()'s output.

        Raises KeyError, TypeError, ValueError or AttributeError if ``data`` has another
        shape.
        """
        return cls(
            commit=data["commit"],
            suites={
                label: TotalCoverage.from_json(c) if c else None
                for label, c in data["suites"].items()
            },
            combined=TotalCoverage.from_json(data["combined"]),
            packages={
                n: TotalCoverage.from_json(c) for n, c in data["packages"].items()
            },
            files={p: TotalCoverage.from_json(c) for p, c in data["files"].items()},
        )


def is_test_file(path: str) -> bool:
    """Return whether ``path`` lies in a test directory or is named like a test.

    Example::

        "src/tests/test_app.py"  -> True    directory "tests"
        "src/x/test_checks.py"   -> True    name matches "test_*.py"
        "conftest.py"            -> True    name matches "conftest.py"
        "src/testing/latest.py"  -> False   only whole names count
        "src/app.py"             -> False
    """
    *directories, name = PurePosixPath(path).parts
    in_test_directory = any(part in TEST_DIRECTORIES for part in directories)
    named_like_test = any(fnmatchcase(name, p) for p in TEST_FILE_PATTERNS)
    return in_test_directory or named_like_test


def tracked_python_files() -> list[str]:
    """Return the non-test Python files git tracks below the current directory.

    Asking git instead of walking the tree never picks up virtualenvs, bazel-*
    symlinks or build output.

    Example: git lists src/app.py, src/tests/test_app.py and src/unused.py;
    returns ``["src/app.py", "src/unused.py"]``.
    """
    out = subprocess.check_output(["git", "ls-files", "*.py"], text=True)
    return [f for f in out.splitlines() if not is_test_file(f)]


def _coverage(tmp: str) -> coverage.Coverage:
    """Return a coverage.py object that keeps its data file in ``tmp``.

    Example: ``"/tmp/abc"`` -> a Coverage whose data file is /tmp/abc/.coverage.
    """
    # config_file=False: pyproject.toml's [tool.coverage] is for measuring the
    # Sphinx runs and would hide every file outside src/ from the report.
    return coverage.Coverage(data_file=str(Path(tmp) / ".coverage"), config_file=False)


def _lcov_from_data(cov: coverage.Coverage, tmp: str) -> str:
    """Return the LCOV text of ``cov``'s data, going through a file in ``tmp``.

    Example: see the outputs of coverage_data_lcov() and baseline_lcov().
    Raises NoDataError if the data names no file.
    """
    lcov_file = Path(tmp) / "report.lcov"
    cov.lcov_report(outfile=str(lcov_file), ignore_errors=True)
    return lcov_file.read_text()


def coverage_data_lcov(directory: Path) -> str:
    """Return LCOV for the coverage.py data files in ``directory``.

    Empty if there are none, or none of them can be read, so the caller reports
    the suite as having no data.

    Example: ``cov_docs/`` holds ``.coverage.runner.4242.123456``, written by a
    Sphinx run that called ``check(False)``. Returns::

        SF:src/app.py
        DA:1,1
        DA:2,1
        DA:3,0
        DA:4,1
        LF:4
        LH:3
        FN:1,4,check
        FNDA:1,check
        FNF:1
        FNH:1
        BRDA:2,0,jump to line 3,0
        BRDA:2,0,jump to line 4,1
        BRF:2
        BRH:1
        end_of_record

    An empty ``cov_docs/``, or one holding only unreadable files, returns "".
    """
    data_files = [str(p) for p in directory.glob(".coverage*")]
    # The directory exists as soon as a coverage run starts, even if no Sphinx
    # process wrote data into it.
    if not data_files:
        return ""
    with tempfile.TemporaryDirectory() as tmp:
        cov = _coverage(tmp)
        # keep=True so the report can be regenerated from the same data.
        # Unreadable files (e.g. of a killed process) are skipped with a warning.
        cov.combine(data_paths=data_files, keep=True)
        try:
            return _lcov_from_data(cov, tmp)
        except NoDataError:
            return ""


def baseline_lcov(files: list[str]) -> str:
    """Return LCOV records listing ``files`` with no line or branch executed.

    Example: ``["src/app.py", "src/unused.py"]`` returns::

        SF:src/app.py
        DA:1,0
        DA:2,0
        DA:3,0
        DA:4,0
        LF:4
        LH:0
        FN:1,4,check
        FNDA:0,check
        FNF:1
        FNH:0
        BRDA:2,0,jump to line 3,-
        BRDA:2,0,jump to line 4,-
        BRF:2
        BRH:0
        end_of_record
        SF:src/unused.py
        DA:1,0
        LF:1
        LH:0
        end_of_record
    """
    with tempfile.TemporaryDirectory() as tmp:
        cov = _coverage(tmp)
        data = cov.get_data()
        # Branch data, so untested files add their branches to the totals too.
        # touch_files() refuses data that is neither line nor branch data yet.
        data.add_arcs({})
        data.touch_files([os.path.abspath(f) for f in files])
        return _lcov_from_data(cov, tmp)


def lcov_records(lcov: str) -> list[Record]:
    r"""Split LCOV text into its records.

    A record runs from its SF: line to its end_of_record line.

    Example input::

        TN:
        SF:src/app.py
        DA:1,1
        end_of_record
        SF:src/unused.py
        DA:1,0
        end_of_record

    Output; the TN: line lies outside every record and is dropped::

        [
            Record("src/app.py", "SF:src/app.py\nDA:1,1\nend_of_record\n"),
            Record("src/unused.py", "SF:src/unused.py\nDA:1,0\nend_of_record\n"),
        ]
    """
    records: list[Record] = []
    record: list[str] = []
    for line in lcov.splitlines():
        if line.startswith("SF:"):
            record = [line]
        elif record:
            record.append(line)
            if line == "end_of_record":
                records.append(Record(record[0][3:], "\n".join(record) + "\n"))
                record = []
    return records


def parse_lcov(lcov: str) -> dict[str, FileCoverage]:
    """Merge all records of LCOV text: executed anywhere wins.

    A line counts as tested if any suite ran it, so files that appear in
    several reports are not counted more than once. A branch is the same in
    every report if its line, block and name are.

    Example: the baseline, Unit tests and docs.bzl scenarios records of
    src/app.py, joined one after the other (shown side by side, totals and FN
    lines left out, "jump to line 3" shortened to "j3")::

        baseline         Unit tests       docs.bzl scenarios
        SF:src/app.py    SF:src/app.py    SF:src/app.py
        DA:1,0           DA:1,1           DA:1,1
        DA:2,0           DA:2,1           DA:2,1
        DA:3,0           DA:3,1           DA:3,0
        DA:4,0           DA:4,0           DA:4,1
        BRDA:2,0,j3,-    BRDA:2,0,j3,1    BRDA:2,0,j3,0
        BRDA:2,0,j4,-    BRDA:2,0,j4,0    BRDA:2,0,j4,1
        end_of_record    end_of_record    end_of_record

    Output: line 3 ran in one suite and line 4 in the other, so all count::

        {"src/app.py": FileCoverage(
            lines={1: True, 2: True, 3: True, 4: True},
            branches={
                Branch(2, 0, "jump to line 3"): True,
                Branch(2, 0, "jump to line 4"): True,
            },
        )}
    """
    files: dict[str, FileCoverage] = {}
    current: FileCoverage | None = None
    for line in lcov.splitlines():
        if line.startswith("SF:"):
            current = files.setdefault(line[3:], FileCoverage())
        elif current is None:
            continue
        elif line.startswith("DA:"):
            lineno, hits = line[3:].split(",")[:2]
            key = int(lineno)
            current.lines[key] = current.lines.get(key, False) or hits != "0"
        elif line.startswith("BRDA:"):
            # BRDA:<line>,<block>,<branch>,<taken>; split from both ends, as
            # the branch name is free text.
            lineno, block, rest = line[5:].split(",", 2)
            name, taken = rest.rsplit(",", 1)
            branch = Branch(int(lineno), int(block), name)
            executed = taken not in ("-", "0")
            current.branches[branch] = current.branches.get(branch, False) or executed
        elif line == "end_of_record":
            current = None
    return files


def package_of(path: str) -> str:
    """Group files per extension below src/extensions, else per directory.

    Extensions are what reviewers reason about; grouping by directory would
    split one extension across its subdirectories such as checks/.

    Example::

        "src/extensions/score_metamodel/checks/graph.py"
                                          -> "src/extensions/score_metamodel"
        "src/helper_lib/__init__.py"      -> "src/helper_lib"
        "src/app.py"                      -> "src"
        "setup.py"                        -> "."
    """
    parts = path.split("/")
    if parts[:2] == ["src", "extensions"] and len(parts) > 2:
        return "/".join(parts[:3])
    return "/".join(parts[:-1]) or "."


def summarize(
    suites: dict[str, dict[str, FileCoverage] | None],
    combined: dict[str, FileCoverage],
) -> Summary:
    """Return the numbers of the summary.

    Example: ``suites`` holds the parse_lcov() result of each suite merged
    with the baseline, None for a suite without data; ``combined`` that of all
    of them. Returns the Summary of Summary's docstring.
    """
    # Files without code (empty __init__.py) have nothing to test and would
    # only add empty rows.
    files = {path: file for path, file in combined.items() if file.lines}
    packages: dict[str, list[FileCoverage]] = {}
    for path, file in files.items():
        packages.setdefault(package_of(path), []).append(file)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    ).stdout.strip()
    return Summary(
        commit=commit,
        suites={
            label: TotalCoverage.of(list(s.values())) if s else None
            for label, s in suites.items()
        },
        combined=TotalCoverage.of(list(combined.values())),
        packages={name: TotalCoverage.of(fs) for name, fs in packages.items()},
        files={path: TotalCoverage.of([file]) for path, file in files.items()},
    )


def _columns(totals: TotalCoverage | None) -> list[tuple[int, int] | None]:
    """Return the (hit, total) of each table column: lines, then branches.

    Example::

        TotalCoverage(3, 5, 1, 2)  -> [(3, 5), (1, 2)]
        None                -> [None, None]    a suite without data
    """
    if totals is None:
        return [None, None]
    return [
        (totals.lines_hit, totals.lines_total),
        (totals.branches_hit, totals.branches_total),
    ]


def _change(now: float | None, before: float | None) -> str:
    """Return the Δ cell: the change from ``before`` to ``now`` in points.

    Example::

        (80.0, 60.0)   -> "+20.0%"
        (60.0, 80.0)   -> "-20.0%"
        (60.0, 60.04)  -> ""         below 0.05 points
        (None, 60.0)   -> "–"        one side has no number
    """
    if now is None or before is None:
        return "–"
    change = now - before
    # Left empty so the rows that did change stand out. Below the rounding
    # precision, because "+0.0%" would read like a change.
    if abs(change) < 0.05:
        return ""
    return f"{change:+.1f}%"


def _header(first: str, compare: bool) -> list[str]:
    """Return the two header lines of a Markdown table.

    Example::

        ("Tests", True)   -> ["| Tests | Lines | Δ | Branches | Δ |",
                              "|---|---:|---:|---:|---:|"]
        ("Tests", False)  -> ["| Tests | Lines | Branches |",
                              "|---|---:|---:|"]
    """
    if compare:
        return [f"| {first} | Lines | Δ | Branches | Δ |", "|---|---:|---:|---:|---:|"]
    return [f"| {first} | Lines | Branches |", "|---|---:|---:|"]


def _row(
    label: str,
    totals: TotalCoverage | None,
    reference: Mapping[str, TotalCoverage | None] | None,
    key: str,
    show_counts: bool = False,
) -> str:
    """Render one table row; ``reference`` is the matching section of main's.

    Example, without main::

        _row("Unit tests", TotalCoverage(3, 5, 1, 2), None, "Unit tests",
             show_counts=True)
        -> "| Unit tests | 60.0% (3/5) | 50.0% (1/2) |"

    Compared with main, where the Unit tests ran 3 of 5 lines::

        _row("Unit tests", TotalCoverage(4, 5, 1, 2),
             {"Unit tests": TotalCoverage(3, 5, 1, 2)}, "Unit tests",
             show_counts=True)
        -> "| Unit tests | 80.0% (4/5) | +20.0% | 50.0% (1/2) |  |"

    A file main does not have, and a suite without data::

        _row("`src/new.py`", TotalCoverage(0, 2, 0, 0), {}, "src/new.py")
        -> "| `src/new.py` | 0.0% | new | – | new |"

        _row("docs.bzl scenarios", None, {"docs.bzl scenarios": None},
             "docs.bzl scenarios", show_counts=True)
        -> "| docs.bzl scenarios | no data | – | no data | – |"
    """
    main_columns = _columns(reference.get(key)) if reference else [None, None]
    cells = [label]
    for now, before in zip(_columns(totals), main_columns, strict=True):
        percent = _percent(now)
        if now is None:
            cells.append("no data")
        elif percent is None:
            cells.append("–")
        elif show_counts:
            cells.append(f"{percent:.1f}% ({now[0]}/{now[1]})")
        else:
            cells.append(f"{percent:.1f}%")
        if reference is not None:
            cells.append(
                _change(percent, _percent(before)) if key in reference else "new"
            )
    return "| " + " | ".join(cells) + " |"


def _changed(now: TotalCoverage, before: TotalCoverage | None) -> bool:
    """Return whether a file's percentages differ from main's by 0.05 or more.

    Example::

        (TotalCoverage(4, 5, 1, 2), TotalCoverage(3, 5, 1, 2))  -> True   80% vs. 60%
        (TotalCoverage(3, 5, 1, 2), TotalCoverage(3, 5, 1, 2))  -> False
        (TotalCoverage(3, 5, 0, 0), None)                       -> True   not on main
    """
    if before is None:
        return True
    for n, b in zip(_columns(now), _columns(before), strict=True):
        a, c = _percent(n), _percent(b)
        if (a is None) != (c is None) or (
            a is not None and c is not None and abs(a - c) >= 0.05
        ):
            return True
    return False


def markdown(summary: Summary, reference: Summary | None, note: str | None) -> str:
    """Render the summary posted on pull requests, compared with ``reference``.

    Example: ``summary`` as in Summary's docstring; ``reference`` is main's,
    where the Unit tests did not run line 3 (Unit tests 2 of 5 lines, combined
    3 of 5, src/app.py 3 of 4); ``note`` is None. Returns::

        <!-- python-coverage-report -->
        ### Python coverage

        | Tests | Lines | Δ | Branches | Δ |
        |---|---:|---:|---:|---:|
        | Unit tests | 60.0% (3/5) | +20.0% | 50.0% (1/2) |  |
        | docs.bzl scenarios | 60.0% (3/5) |  | 50.0% (1/2) |  |
        | **Combined** | 80.0% (4/5) | +20.0% | 100.0% (2/2) |  |

        Percentages cover every tracked non-test Python file; files that no ...
        Δ is the change in percentage points against main at `9f8e7d6c`.

        <details><summary>Files with changed coverage (1, biggest drop ...

        | File | Lines | Δ | Branches | Δ |
        |---|---:|---:|---:|---:|
        | `src/app.py` | 100.0% | +25.0% | 100.0% |  |

        </details>

        <details><summary>Per package (lowest line coverage first)</summary>

        | Package | Lines | Δ | Branches | Δ |
        |---|---:|---:|---:|---:|
        | `src` | 80.0% | +20.0% | 100.0% |  |

        </details>

        <details><summary>Files no test runs (1)</summary>

        - `src/unused.py` (1 lines)

        </details>

    With ``reference`` None there are no Δ columns and no "Files with changed
    coverage" section; a ``note`` is printed below the "Percentages" line.
    """
    compare = reference is not None
    out = [COMMENT_MARKER, "### Python coverage", "", *_header("Tests", compare)]
    for label, totals in summary.suites.items():
        main_suites = reference.suites if reference else None
        out.append(_row(label, totals, main_suites, label, show_counts=True))
    out.append(
        _row(
            "**Combined**",
            summary.combined,
            {"combined": reference.combined} if reference else None,
            "combined",
            show_counts=True,
        )
    )
    out += [
        "",
        "Percentages cover every tracked non-test Python file; "
        "files that no test imports count as 0%.",
    ]
    if reference:
        out.append(
            "Δ is the change in percentage points against main at "
            f"`{reference.commit[:8]}`."
        )
    if note:
        out.append(note)
    out.append("")

    if reference:
        files, main_files = summary.files, reference.files
        changed = [p for p, c in files.items() if _changed(c, main_files.get(p))]

        def biggest_drop_first(path: str) -> tuple[bool, float]:
            """Return the sort key of a changed file: drops first, new last.

            Example::

                "src/app.py", 75% on main, 100% now  -> (False, 25.0)
                "src/b.py",   90% on main, 50% now   -> (False, -40.0)
                "src/new.py", not on main            -> (True, 0.0)

            Sorted: src/b.py, src/app.py, src/new.py (False before True,
            then the most negative change first).
            """
            main_file = main_files.get(path)
            before = main_file.lines_percent if main_file else None
            now = files[path].lines_percent
            if before is None or now is None:
                return (True, 0.0)  # new files after the changed ones
            return (False, now - before)

        # Collapsed like the other details: the totals above are the overview,
        # the files are for whoever wants to know where it changed.
        if changed:
            out += [
                "<details><summary>Files with changed coverage "
                f"({len(changed)}, biggest drop first)</summary>",
                "",
                *_header("File", compare),
                *(
                    _row(f"`{path}`", files[path], main_files, path)
                    for path in sorted(changed, key=biggest_drop_first)
                ),
                "",
                "</details>",
            ]
        else:
            out.append("No file changed its coverage.")
        out.append("")

    packages = sorted(
        summary.packages.items(),
        key=lambda item: (item[1].lines_percent or 0.0, item[0]),
    )
    out += [
        "<details><summary>Per package (lowest line coverage first)</summary>",
        "",
        *_header("Package", compare),
        *(
            _row(f"`{name}`", totals, reference.packages if reference else None, name)
            for name, totals in packages
        ),
        "",
        "</details>",
        "",
    ]

    untested = sorted(
        (path, totals.lines_total)
        for path, totals in summary.files.items()
        if totals.lines_hit == 0
    )
    if untested:
        out += [
            f"<details><summary>Files no test runs ({len(untested)})</summary>",
            "",
            *(f"- `{path}` ({count} lines)" for path, count in untested),
            "",
            "</details>",
            "",
        ]
    return "\n".join(out)


def load_reports(args: list[str], tracked: set[str]) -> dict[str, str | None]:
    r"""Return the LCOV of each ``[LABEL=]PATH`` by label, None if it has no data.

    Example: ``["Unit tests=unit.lcov", "docs.bzl scenarios=cov_docs"]``, where
    unit.lcov has records for src/app.py and src/tests/test_app.py, and
    cov_docs/ holds the data file of coverage_data_lcov()'s example. Returns
    (the docs.bzl record's LF, LH, FN* and BRF/BRH lines left out)::

        {
            "Unit tests":
                "SF:src/app.py\nDA:1,1\nDA:2,1\nDA:3,1\nDA:4,0\n"
                "BRDA:2,0,jump to line 3,1\nBRDA:2,0,jump to line 4,0\n"
                "end_of_record\n",
            "docs.bzl scenarios":
                "SF:src/app.py\nDA:1,1\nDA:2,1\nDA:3,0\nDA:4,1\n"
                "BRDA:2,0,jump to line 3,0\nBRDA:2,0,jump to line 4,1\n"
                "end_of_record\n",
        }

    The test file's record is gone. Had cov_docs/ been missing or empty:
    ``"docs.bzl scenarios": None``.
    """
    suites: dict[str, str | None] = {}
    for arg in args:
        label, sep, path = arg.partition("=")
        if not sep:
            label, path = arg, arg
        report = Path(path)
        # A test job that failed early uploads no data; that must not hide
        # the coverage of the other suites.
        if not report.exists():
            print(f"warning: {path} does not exist; reporting '{label}' as no data")
            suites[label] = None
            continue
        text = coverage_data_lcov(report) if report.is_dir() else report.read_text()
        # Test code is not under test, and the merged LCOV must count the same
        # files as the Markdown summary so genhtml shows the same totals.
        records = "".join(r.text for r in lcov_records(text) if r.source in tracked)
        # An empty report means measuring failed (e.g. `bazel coverage` on a
        # Python version without a rules_python coverage tool). Shown as 0% it
        # would look like real, untested code.
        if not records:
            print(
                f"warning: {path} has no coverage data; reporting '{label}' as no data"
            )
            suites[label] = None
            continue
        suites[label] = records
    return suites


def load_reference(path: Path) -> tuple[Summary | None, str | None]:
    """Return main's numbers written by --json, or a note why there are none.

    A pull request without a comparison is still useful; one whose summary
    fails because of main's file is not.

    Example: main.json holding Summary.to_json()'s output with ``"schema": 1``
    returns ``(that Summary, None)``. Otherwise::

        main.json missing      -> None, "No coverage of main available to ..."
        not valid JSON         -> None, "... could not be read; no comparison."
        "schema" is not 1      -> None, "... has an older format; no comparison."
    """
    # Main has no report yet before its first run with this tool, or after
    # its artifact expired.
    if not path.exists():
        return None, "No coverage of main available to compare with."
    unreadable = "The coverage of main could not be read; no comparison."
    try:
        data = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"warning: cannot read {path}: {exc}; not comparing with main")
        return None, unreadable
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        print(f"warning: {path} is not in format {SCHEMA}; not comparing with main")
        return None, "The coverage of main has an older format; no comparison."
    try:
        return Summary.from_json(cast(dict[str, Any], data)), None
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        print(f"warning: {path} is malformed: {exc!r}; not comparing with main")
        return None, unreadable


def write_summary(
    summary: Summary,
    json_file: str | None,
    markdown_file: str | None,
    compare_with: str | None,
) -> None:
    """Write ``summary`` as JSON and/or as Markdown compared with main's JSON.

    Example: ``(summary, "coverage.json", "summary.md", "main/coverage.json")``
    writes Summary.to_json()'s dict to coverage.json, and markdown()'s text,
    compared with main/coverage.json, to summary.md. Returns nothing.
    """
    if json_file:
        Path(json_file).write_text(
            json.dumps(summary.to_json(), indent=2, sort_keys=True)
        )
        print(f"Wrote {Path(json_file).absolute()}")
    if not markdown_file:
        return
    reference, note = None, None
    if compare_with:
        reference, note = load_reference(Path(compare_with))
    Path(markdown_file).write_text(markdown(summary, reference, note))
    print(f"Wrote {Path(markdown_file).absolute()}")


def main() -> None:
    r"""Merge the reports named on the command line and write the results.

    Example::

        bazel run //tools:coverage_report -- \
            "Unit tests=unit.lcov" "docs.bzl scenarios=cov_docs" \
            --json coverage.json --markdown summary.md

    Writes coverage.lcov (both suites' src/app.py records, plus the baseline
    record of src/unused.py, which no suite has), coverage.json (see
    Summary.to_json()) and summary.md (see markdown()). Prints::

        Wrote /repo/coverage.lcov: 1 untested Python files added
        Wrote /repo/coverage.json
        Wrote /repo/summary.md
    """
    parser = argparse.ArgumentParser(
        description="Merge Python coverage reports and add untested files at 0%."
    )
    parser.add_argument(
        "reports",
        nargs="*",
        metavar="[LABEL=]PATH",
        help="LCOV file or directory of coverage.py data files, relative to the "
        "repository root. Missing paths are reported as 'no data'.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="coverage.lcov",
        help="merged LCOV file to write (default: %(default)s)",
    )
    parser.add_argument("--markdown", help="also write a Markdown summary to this file")
    parser.add_argument("--json", help="also write the summary's numbers to this file")
    parser.add_argument(
        "--compare-with",
        metavar="JSON",
        help="numbers written by --json for main; adds the change to the Markdown "
        "summary. A missing file is noted in the summary.",
    )
    args = parser.parse_args()

    # `bazel run` starts in the runfiles tree. Work from the checkout instead so
    # git sees the repository and LCOV paths are repo-relative (e.g. src/...),
    # matching the paths in Bazel's coverage report.
    os.chdir(os.environ.get("BUILD_WORKSPACE_DIRECTORY", "."))

    tracked = tracked_python_files()
    baseline = baseline_lcov(tracked)

    suites = load_reports(args.reports, set(tracked))

    reports = [text for text in suites.values() if text]
    covered = {r.source for text in reports for r in lcov_records(text)}
    missing = [r.text for r in lcov_records(baseline) if r.source not in covered]
    output = Path(args.output)
    output.write_text("".join(reports + missing))
    print(f"Wrote {output.absolute()}: {len(missing)} untested Python files added")

    if args.markdown or args.json:
        # Merging each suite with the baseline gives all of them the same
        # denominators: every line and branch of every tracked file.
        summary = summarize(
            {
                label: parse_lcov(baseline + text) if text else None
                for label, text in suites.items()
            },
            parse_lcov(baseline + "".join(reports)),
        )
        write_summary(summary, args.json, args.markdown, args.compare_with)


if __name__ == "__main__":
    main()
