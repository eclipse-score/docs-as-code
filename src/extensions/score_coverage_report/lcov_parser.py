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
"""Parse LCOV ``.info`` text and aggregate it per component.

The parser is intentionally independent of any specific coverage producer
(``llvm-cov export --format=lcov``, ``gcov``/``lcov``, ``grcov``, ...): LCOV's
tracefile format (https://ltp.sourceforge.net/coverage/lcov/geninfo.1.php) is a
long-standing, widely emitted plain-text interchange format, so this module
only depends on that format, not on any particular toolchain.

Per-file totals are recomputed from the ``DA``/``BRDA`` records rather than
trusted from the ``LF``/``LH``/``BRF``/``BRH`` summary records some producers
emit, because those summary records are optional and inconsistently present.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FileCoverage:
    """Line and branch totals for one source file, as recorded in an LCOV
    ``SF:``/``end_of_record`` block."""

    path: str
    lines_found: int = 0
    lines_hit: int = 0
    branches_found: int = 0
    branches_hit: int = 0

    @property
    def line_percent(self) -> float | None:
        if not self.lines_found:
            return None
        return round(100 * self.lines_hit / self.lines_found, 1)

    @property
    def branch_percent(self) -> float | None:
        if not self.branches_found:
            return None
        return round(100 * self.branches_hit / self.branches_found, 1)


@dataclass(frozen=True)
class ComponentCoverage:
    """Coverage totals for every LCOV file record attributed to one component."""

    component_id: str
    files: tuple[FileCoverage, ...] = field(default_factory=tuple)

    @property
    def lines_found(self) -> int:
        return sum(f.lines_found for f in self.files)

    @property
    def lines_hit(self) -> int:
        return sum(f.lines_hit for f in self.files)

    @property
    def branches_found(self) -> int:
        return sum(f.branches_found for f in self.files)

    @property
    def branches_hit(self) -> int:
        return sum(f.branches_hit for f in self.files)

    @property
    def line_percent(self) -> float | None:
        if not self.lines_found:
            return None
        return round(100 * self.lines_hit / self.lines_found, 1)

    @property
    def branch_percent(self) -> float | None:
        if not self.branches_found:
            return None
        return round(100 * self.branches_hit / self.branches_found, 1)


def _parse_int(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


@dataclass
class _LcovRecordState:
    current_path: str | None = None
    lines_found: int = 0
    lines_hit: int = 0
    branches_found: int = 0
    branches_hit: int = 0


def _reset_lcov_record(state: _LcovRecordState) -> None:
    state.current_path = None
    state.lines_found = 0
    state.lines_hit = 0
    state.branches_found = 0
    state.branches_hit = 0


def _flush_lcov_record(
    files: dict[str, FileCoverage], state: _LcovRecordState
) -> None:
    if state.current_path is not None:
        files[state.current_path] = FileCoverage(
            path=state.current_path,
            lines_found=state.lines_found,
            lines_hit=state.lines_hit,
            branches_found=state.branches_found,
            branches_hit=state.branches_hit,
        )
    _reset_lcov_record(state)


def _count_lcov_line(state: _LcovRecordState, line: str) -> None:
    parts = line[len("DA:") :].split(",")
    if len(parts) >= 2:
        hits = _parse_int(parts[1])
        if hits is not None:
            state.lines_found += 1
            if hits > 0:
                state.lines_hit += 1


def _count_lcov_branch(state: _LcovRecordState, line: str) -> None:
    parts = line[len("BRDA:") :].split(",")
    if len(parts) >= 4:
        taken = parts[3]
        state.branches_found += 1
        # ``-`` means the branch was never reached at all (as opposed to
        # reached-but-not-taken, which is recorded as "0").
        hits = _parse_int(taken) if taken != "-" else 0
        if hits:
            state.branches_hit += 1


def _consume_lcov_line(files: dict[str, FileCoverage], state: _LcovRecordState, line: str) -> None:
    if line.startswith("SF:"):
        # A new ``SF:`` without a preceding ``end_of_record`` would indicate
        # a malformed tracefile; flush defensively so no data is dropped.
        _flush_lcov_record(files, state)
        state.current_path = line[len("SF:") :].strip()
    elif line.startswith("DA:"):
        _count_lcov_line(state, line)
    elif line.startswith("BRDA:"):
        _count_lcov_branch(state, line)
    elif line == "end_of_record":
        _flush_lcov_record(files, state)


def parse_lcov(text: str) -> dict[str, FileCoverage]:
    """Parse LCOV tracefile text into per-file coverage, keyed by ``SF:`` path.

    Unknown or malformed record lines are ignored rather than raising, since a
    tracefile may contain record types (``FN``, ``FNDA``, ``BRA``, ``VER``, ...)
    this module does not need and different producers are not perfectly
    consistent about optional summary lines.
    """

    files: dict[str, FileCoverage] = {}
    state = _LcovRecordState()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        _consume_lcov_line(files, state, line)
    # Tolerate a missing trailing ``end_of_record`` on the last block.
    _flush_lcov_record(files, state)
    return files


def _normalized(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _matches_prefix(path: str, prefix: str) -> bool:
    """Whether ``path`` is attributable to a component owning ``prefix``.

    LCOV ``SF:`` paths are sometimes repo-relative (``src/parser/reader.cpp``)
    and sometimes absolute host/execroot paths that merely *contain* the
    repo-relative directory as a suffix (e.g. under a Bazel sandbox root).
    Both forms are matched so callers do not need to normalize the tracefile
    themselves.
    """

    normalized_path = _normalized(path)
    normalized_prefix = prefix.strip("/")
    if not normalized_prefix:
        return False
    return (
        normalized_path == normalized_prefix
        or normalized_path.startswith(f"{normalized_prefix}/")
        or f"/{normalized_prefix}/" in normalized_path
    )


def assign_files_to_components(
    files_by_path: Mapping[str, FileCoverage],
    source_roots: Mapping[str, str],
) -> dict[str, ComponentCoverage]:
    """Attribute every LCOV file record to at most one component.

    Components nest: a ``comp`` Need may ``consists_of`` further ``comp`` Needs,
    and their source roots nest accordingly. A file below ``src/parser/detail``
    therefore matches both the child's root and its parent's ``src/parser``. The
    most specific declared root wins, so every line is counted exactly once
    across the report instead of being added to an ancestor as well.

    Components without a matching record are absent from the result, which lets
    callers distinguish "no coverage data available" from "0% covered".
    """

    # Longest root first, so the most specific component claims a file. The
    # component ID breaks ties to keep the attribution deterministic when two
    # components declare equally specific roots.
    ordered_roots = sorted(
        (
            (component_id, root.strip("/"))
            for component_id, root in source_roots.items()
            if root.strip("/")
        ),
        key=lambda item: (-len(item[1]), item[0]),
    )

    claimed: dict[str, list[FileCoverage]] = {}
    for _, coverage in sorted(files_by_path.items()):
        for component_id, root in ordered_roots:
            if _matches_prefix(coverage.path, root):
                claimed.setdefault(component_id, []).append(coverage)
                break

    return {
        component_id: ComponentCoverage(
            component_id=component_id, files=tuple(covered_files)
        )
        for component_id, covered_files in claimed.items()
    }
