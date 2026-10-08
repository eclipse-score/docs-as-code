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

Branch names are rewritten to numbers: recent coverage.py versions name them
("jump to line 45"), which lcov/genhtml 1.x silently drop.

To show what a change does to coverage, write the numbers of main with
``--json main.json`` and pass them to a later run with ``--compare-with
main.json``. The Markdown summary then shows the change per suite, package and
file. CI takes main.json from the latest run on main.
"""

import argparse
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath
from typing import Any, cast

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


@dataclass
class FileCoverage:
    """Executed state of each line and branch of one source file."""

    lines: dict[int, bool] = field(default_factory=dict[int, bool])
    branches: dict[tuple[int, int, int], bool] = field(
        default_factory=dict[tuple[int, int, int], bool]
    )


def is_test_file(path: str) -> bool:
    """Return whether ``path`` lies in a test directory or is named like a test."""
    *directories, name = PurePosixPath(path).parts
    in_test_directory = any(part in TEST_DIRECTORIES for part in directories)
    named_like_test = any(fnmatchcase(name, p) for p in TEST_FILE_PATTERNS)
    return in_test_directory or named_like_test


def tracked_python_files() -> list[str]:
    """Return the non-test Python files git tracks below the current directory.

    Asking git instead of walking the tree never picks up virtualenvs, bazel-*
    symlinks or build output.
    """
    out = subprocess.check_output(["git", "ls-files", "*.py"], text=True)
    return [f for f in out.splitlines() if not is_test_file(f)]


def _coverage(tmp: str) -> coverage.Coverage:
    # config_file=False: pyproject.toml's [tool.coverage] is for measuring the
    # Sphinx runs and would hide every file outside src/ from the report.
    return coverage.Coverage(data_file=str(Path(tmp) / ".coverage"), config_file=False)


def _lcov_from_data(cov: coverage.Coverage, tmp: str) -> str:
    lcov_file = Path(tmp) / "report.lcov"
    cov.lcov_report(outfile=str(lcov_file), ignore_errors=True)
    return lcov_file.read_text()


def coverage_data_lcov(directory: Path) -> str:
    """Return LCOV for the coverage.py data files in ``directory``.

    Empty if there are none, or none of them can be read, so the caller reports
    the suite as having no data.
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
    """Return LCOV records listing ``files`` with no line or branch executed."""
    with tempfile.TemporaryDirectory() as tmp:
        cov = _coverage(tmp)
        data = cov.get_data()
        # Branch data, so untested files add their branches to the totals too.
        # touch_files() refuses data that is neither line nor branch data yet.
        data.add_arcs({})
        data.touch_files([os.path.abspath(f) for f in files])
        return _lcov_from_data(cov, tmp)


def numeric_branches(lcov: str, names: dict[tuple[str, str, str], list[str]]) -> str:
    """Replace BRDA branch names with their index per source line and block.

    lcov/genhtml 1.x silently drop branches whose name is not a number.
    ``names`` is shared across reports so the same branch of the same file gets
    the same number in every report; otherwise merging would count it twice.
    """
    lines: list[str] = []
    source = ""
    for line in lcov.splitlines():
        if line.startswith("SF:"):
            source = line[3:]
        if line.startswith("BRDA:"):
            # BRDA:<line>,<block>,<branch>,<taken>; split from both ends, as
            # the branch name is free text.
            lineno, block, rest = line[5:].split(",", 2)
            branch, taken = rest.rsplit(",", 1)
            known = names.setdefault((source, lineno, block), [])
            if branch not in known:
                known.append(branch)
            line = f"BRDA:{lineno},{block},{known.index(branch)},{taken}"
        lines.append(line)
    return "\n".join(lines) + "\n"


def lcov_records(lcov: str) -> list[tuple[str, str]]:
    """Split LCOV text into its records, as (source file, record text) pairs.

    A record runs from its SF: line to its end_of_record line.
    """
    records: list[tuple[str, str]] = []
    record: list[str] = []
    for line in lcov.splitlines():
        if line.startswith("SF:"):
            record = [line]
        elif record:
            record.append(line)
            if line == "end_of_record":
                records.append((record[0][3:], "\n".join(record) + "\n"))
                record = []
    return records


def parse_lcov(lcov: str) -> dict[str, FileCoverage]:
    """Merge all records of numbered LCOV text: executed anywhere wins.

    A line counts as tested if any suite ran it, so files that appear in
    several reports are not counted more than once.
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
            lineno, block, branch, taken = line[5:].split(",")
            bkey = (int(lineno), int(block), int(branch))
            executed = taken not in ("-", "0")
            current.branches[bkey] = current.branches.get(bkey, False) or executed
        elif line == "end_of_record":
            current = None
    return files


def package_of(path: str) -> str:
    """Group files per extension below src/extensions, else per directory.

    Extensions are what reviewers reason about; grouping by directory would
    split one extension across its subdirectories such as checks/.
    """
    parts = path.split("/")
    if parts[:2] == ["src", "extensions"] and len(parts) > 2:
        return "/".join(parts[:3])
    return "/".join(parts[:-1]) or "."


# (hit, total) per kind ("lines", "branches") of a file, package or suite.
Counts = dict[str, list[int]]
KINDS = ("lines", "branches")


def _counts(files: list[FileCoverage]) -> Counts:
    lines = [hit for f in files for hit in f.lines.values()]
    branches = [hit for f in files for hit in f.branches.values()]
    return {
        "lines": [sum(lines), len(lines)],
        "branches": [sum(branches), len(branches)],
    }


def summarize(
    suites: list[tuple[str, dict[str, FileCoverage] | None]],
    combined: dict[str, FileCoverage],
) -> dict[str, Any]:
    """Return the numbers of the summary.

    Also written as JSON: a pull request compares its numbers with the ones
    the latest main run stored.
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
    return {
        "schema": SCHEMA,
        "commit": commit,
        "suites": {
            label: _counts(list(s.values())) if s else None for label, s in suites
        },
        "combined": _counts(list(combined.values())),
        "packages": {name: _counts(fs) for name, fs in packages.items()},
        "files": {path: _counts([file]) for path, file in files.items()},
    }


def _percent(counts: Counts | None, kind: str) -> float | None:
    if not counts or not counts[kind][1]:
        return None
    hit, total = counts[kind]
    return 100 * hit / total


def _change(now: float | None, before: float | None) -> str:
    if now is None or before is None:
        return "–"
    change = now - before
    # Left empty so the rows that did change stand out. Below the rounding
    # precision, because "+0.0%" would read like a change.
    if abs(change) < 0.05:
        return ""
    return f"{change:+.1f}%"


def _header(first: str, compare: bool) -> list[str]:
    if compare:
        return [f"| {first} | Lines | Δ | Branches | Δ |", "|---|---:|---:|---:|---:|"]
    return [f"| {first} | Lines | Branches |", "|---|---:|---:|"]


def _row(
    label: str,
    counts: Counts | None,
    reference: dict[str, Any] | None,
    key: str,
    show_counts: bool = False,
) -> str:
    """Render one table row; ``reference`` is the matching section of main's."""
    cells = [label]
    for kind in KINDS:
        now = _percent(counts, kind)
        if counts is None:
            cells.append("no data")
        elif now is None:
            cells.append("–")
        elif show_counts:
            hit, total = counts[kind]
            cells.append(f"{now:.1f}% ({hit}/{total})")
        else:
            cells.append(f"{now:.1f}%")
        if reference is not None:
            before = _percent(reference[key], kind) if key in reference else None
            cells.append(_change(now, before) if key in reference else "new")
    return "| " + " | ".join(cells) + " |"


def _changed(now: Counts, before: Counts | None) -> bool:
    if before is None:
        return True
    for kind in KINDS:
        a, b = _percent(now, kind), _percent(before, kind)
        if (a is None) != (b is None) or (
            a is not None and b is not None and abs(a - b) >= 0.05
        ):
            return True
    return False


def markdown(
    summary: dict[str, Any], reference: dict[str, Any] | None, note: str | None
) -> str:
    """Render the summary posted on pull requests, compared with ``reference``."""
    compare = reference is not None
    ref: dict[str, Any] = reference or {}
    out = [COMMENT_MARKER, "### Python coverage", "", *_header("Tests", compare)]
    for label, counts in summary["suites"].items():
        out.append(_row(label, counts, ref.get("suites"), label, show_counts=True))
    out.append(
        _row(
            "**Combined**",
            summary["combined"],
            {"combined": ref["combined"]} if compare else None,
            "combined",
            show_counts=True,
        )
    )
    out += [
        "",
        "Percentages cover every tracked non-test Python file; "
        "files that no test imports count as 0%.",
    ]
    if compare:
        out.append(
            f"Δ is the change in percentage points against main at `{ref['commit'][:8]}`."
        )
    if note:
        out.append(note)
    out.append("")

    if compare:
        files = summary["files"]
        changed = [p for p, c in files.items() if _changed(c, ref["files"].get(p))]

        def biggest_drop_first(path: str) -> tuple[bool, float]:
            before = _percent(ref["files"].get(path), "lines")
            now = _percent(files[path], "lines")
            if path not in ref["files"] or before is None or now is None:
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
                    _row(f"`{path}`", files[path], ref["files"], path)
                    for path in sorted(changed, key=biggest_drop_first)
                ),
                "",
                "</details>",
            ]
        else:
            out.append("No file changed its coverage.")
        out.append("")

    packages = sorted(
        summary["packages"].items(),
        key=lambda item: (_percent(item[1], "lines") or 0.0, item[0]),
    )
    out += [
        "<details><summary>Per package (lowest line coverage first)</summary>",
        "",
        *_header("Package", compare),
        *(
            _row(f"`{name}`", counts, ref.get("packages"), name)
            for name, counts in packages
        ),
        "",
        "</details>",
        "",
    ]

    untested = sorted(
        (path, counts["lines"][1])
        for path, counts in summary["files"].items()
        if counts["lines"][0] == 0
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


def load_reports(
    args: list[str], tracked: set[str], names: dict[tuple[str, str, str], list[str]]
) -> list[tuple[str, str | None]]:
    """Return the numbered LCOV of each ``[LABEL=]PATH``, or None if it has no data."""
    suites: list[tuple[str, str | None]] = []
    for arg in args:
        label, sep, path = arg.partition("=")
        if not sep:
            label, path = arg, arg
        report = Path(path)
        # A test job that failed early uploads no data; that must not hide
        # the coverage of the other suites.
        if not report.exists():
            print(f"warning: {path} does not exist; reporting '{label}' as no data")
            suites.append((label, None))
            continue
        text = coverage_data_lcov(report) if report.is_dir() else report.read_text()
        # Test code is not under test, and the merged LCOV must count the same
        # files as the Markdown summary so genhtml shows the same totals.
        records = "".join(
            record
            for source, record in lcov_records(numeric_branches(text, names))
            if source in tracked
        )
        # An empty report means measuring failed (e.g. `bazel coverage` on a
        # Python version without a rules_python coverage tool). Shown as 0% it
        # would look like real, untested code.
        if not records:
            print(
                f"warning: {path} has no coverage data; reporting '{label}' as no data"
            )
            suites.append((label, None))
            continue
        suites.append((label, records))
    return suites


def load_reference(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Return main's numbers written by --json, or a note why there are none.

    A pull request without a comparison is still useful; one whose summary
    fails because of main's file is not.
    """
    # Main has no report yet before its first run with this tool, or after
    # its artifact expired.
    if not path.exists():
        return None, "No coverage of main available to compare with."
    try:
        reference = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"warning: cannot read {path}: {exc}; not comparing with main")
        return None, "The coverage of main could not be read; no comparison."
    if not isinstance(reference, dict) or reference.get("schema") != SCHEMA:
        print(f"warning: {path} is not in format {SCHEMA}; not comparing with main")
        return None, "The coverage of main has an older format; no comparison."
    return cast(dict[str, Any], reference), None


def write_summary(
    summary: dict[str, Any],
    json_file: str | None,
    markdown_file: str | None,
    compare_with: str | None,
) -> None:
    if json_file:
        Path(json_file).write_text(json.dumps(summary, indent=2, sort_keys=True))
        print(f"Wrote {Path(json_file).absolute()}")
    if not markdown_file:
        return
    reference, note = None, None
    if compare_with:
        reference, note = load_reference(Path(compare_with))
    Path(markdown_file).write_text(markdown(summary, reference, note))
    print(f"Wrote {Path(markdown_file).absolute()}")


def main() -> None:
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
    names: dict[tuple[str, str, str], list[str]] = {}
    baseline = numeric_branches(baseline_lcov(tracked), names)

    suites = load_reports(args.reports, set(tracked), names)

    reports = [text for _, text in suites if text]
    covered = {source for text in reports for source, _ in lcov_records(text)}
    missing = [
        record for source, record in lcov_records(baseline) if source not in covered
    ]
    output = Path(args.output)
    output.write_text("".join(reports + missing))
    print(f"Wrote {output.absolute()}: {len(missing)} untested Python files added")

    if args.markdown or args.json:
        # Merging each suite with the baseline gives all of them the same
        # denominators: every line and branch of every tracked file.
        summary = summarize(
            [
                (label, parse_lcov(baseline + text) if text else None)
                for label, text in suites
            ],
            parse_lcov(baseline + "".join(reports)),
        )
        write_summary(summary, args.json, args.markdown, args.compare_with)


if __name__ == "__main__":
    main()
