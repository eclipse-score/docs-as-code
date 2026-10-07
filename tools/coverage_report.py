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
"""

import argparse
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import coverage

# Tests are not code under test; listing them would only add 0% noise.
TEST_FILE = re.compile(
    r"(^|/)tests?/|(^|/)test_[^/]*\.py$|_test\.py$|(^|/)conftest\.py$"
)
BRDA = re.compile(r"^BRDA:(\d+),(\d+),(.*),([^,]*)$")
RECORD = re.compile(r"^SF:(.*)\n(?:.*\n)*?end_of_record\n", re.M)
# Lets coverage_comment.yml find and update its earlier comment instead of
# adding a new one on every push.
COMMENT_MARKER = "<!-- python-coverage-report -->"


@dataclass
class FileCoverage:
    """Executed state of each line and branch of one source file."""

    lines: dict[int, bool] = field(default_factory=dict[int, bool])
    branches: dict[tuple[int, int, int], bool] = field(
        default_factory=dict[tuple[int, int, int], bool]
    )


def tracked_python_files() -> list[str]:
    """Return the non-test Python files git tracks below the current directory.

    Asking git instead of walking the tree never picks up virtualenvs, bazel-*
    symlinks or build output.
    """
    out = subprocess.check_output(["git", "ls-files", "*.py"], text=True)
    return [f for f in out.splitlines() if not TEST_FILE.search(f)]


def _coverage(tmp: str) -> coverage.Coverage:
    # config_file=False: pyproject.toml's [tool.coverage] is for measuring the
    # Sphinx runs and would hide every file outside src/ from the report.
    return coverage.Coverage(data_file=str(Path(tmp) / ".coverage"), config_file=False)


def _lcov_from_data(cov: coverage.Coverage, tmp: str) -> str:
    lcov_file = Path(tmp) / "report.lcov"
    cov.lcov_report(outfile=str(lcov_file), ignore_errors=True)
    return lcov_file.read_text()


def coverage_data_lcov(directory: Path) -> str:
    """Return LCOV for the coverage.py data files in ``directory``."""
    data_files = [str(p) for p in directory.glob(".coverage*")]
    with tempfile.TemporaryDirectory() as tmp:
        cov = _coverage(tmp)
        # keep=True so the report can be regenerated from the same data.
        cov.combine(data_paths=data_files, keep=True)
        return _lcov_from_data(cov, tmp)


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
        match = BRDA.match(line)
        if match:
            lineno, block, branch, taken = match.groups()
            known = names.setdefault((source, lineno, block), [])
            if branch not in known:
                known.append(branch)
            line = f"BRDA:{lineno},{block},{known.index(branch)},{taken}"
        lines.append(line)
    return "\n".join(lines) + "\n"


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


def _ratio(hit: int, total: int) -> str:
    return f"{100 * hit / total:.1f}% ({hit}/{total})" if total else "–"


def _totals(files: list[FileCoverage]) -> tuple[str, str]:
    lines = [hit for f in files for hit in f.lines.values()]
    branches = [hit for f in files for hit in f.branches.values()]
    return _ratio(sum(lines), len(lines)), _ratio(sum(branches), len(branches))


def markdown(
    suites: list[tuple[str, dict[str, FileCoverage] | None]],
    combined: dict[str, FileCoverage],
) -> str:
    """Render the coverage summary posted on pull requests."""
    out = [
        COMMENT_MARKER,
        "### Python coverage",
        "",
        "| Tests | Lines | Branches |",
        "|---|---:|---:|",
    ]
    for label, files in suites:
        lines, branches = _totals(list(files.values())) if files else ("no data",) * 2
        out.append(f"| {label} | {lines} | {branches} |")
    lines, branches = _totals(list(combined.values()))
    out += [
        f"| **Combined** | **{lines}** | **{branches}** |",
        "",
        "Percentages cover every tracked non-test Python file; "
        "files that no test imports count as 0%.",
        "",
    ]

    packages: dict[str, list[FileCoverage]] = {}
    for path, file in combined.items():
        # Files without code (empty __init__.py) have nothing to test and
        # would only add empty rows.
        if file.lines:
            packages.setdefault(package_of(path), []).append(file)
    rows = sorted(
        (
            sum(h for f in files for h in f.lines.values())
            / max(1, sum(len(f.lines) for f in files)),
            name,
            files,
        )
        for name, files in packages.items()
    )
    out += [
        "<details><summary>Per package (lowest line coverage first)</summary>",
        "",
        "| Package | Lines | Branches |",
        "|---|---:|---:|",
    ]
    for _, name, files in rows:
        lines, branches = _totals(files)
        out.append(f"| `{name}` | {lines} | {branches} |")
    out += ["", "</details>", ""]

    untested = sorted(
        (path, len(file.lines))
        for path, file in combined.items()
        if file.lines and not any(file.lines.values())
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
    args = parser.parse_args()

    # `bazel run` starts in the runfiles tree. Work from the checkout instead so
    # git sees the repository and LCOV paths are repo-relative (e.g. src/...),
    # matching the paths in Bazel's coverage report.
    os.chdir(os.environ.get("BUILD_WORKSPACE_DIRECTORY", "."))

    tracked = tracked_python_files()
    names: dict[tuple[str, str, str], list[str]] = {}
    baseline = numeric_branches(baseline_lcov(tracked), names)

    def tracked_records(text: str) -> str:
        """Keep only tracked non-test files.

        Test code is not under test, and the merged LCOV must count the same
        files as the Markdown summary so genhtml shows the same totals.
        """
        return "".join(m.group(0) for m in RECORD.finditer(text) if m[1] in tracked)

    suites: list[tuple[str, str | None]] = []
    for arg in args.reports:
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
        suites.append((label, tracked_records(numeric_branches(text, names))))

    reports = [text for _, text in suites if text]
    covered = {sf for text in reports for sf in re.findall(r"^SF:(.*)$", text, re.M)}
    missing = [m[0] for m in RECORD.finditer(baseline) if m[1] not in covered]
    output = Path(args.output)
    output.write_text("".join(reports + missing))
    print(f"Wrote {output.absolute()}: {len(missing)} untested Python files added")

    if args.markdown:
        # Merging each suite with the baseline gives all of them the same
        # denominators: every line and branch of every tracked file.
        summary = markdown(
            [
                (label, parse_lcov(baseline + text) if text else None)
                for label, text in suites
            ],
            parse_lcov(baseline + "".join(reports)),
        )
        Path(args.markdown).write_text(summary)
        print(f"Wrote {Path(args.markdown).absolute()}")


if __name__ == "__main__":
    main()
