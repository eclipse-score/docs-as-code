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
"""Summarize LCOV for selected code-file lists with stable JSON output."""

import json
import os
import re
import tempfile
from collections.abc import Collection
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypedDict, cast


class CoverageError(ValueError):
    """Invalid code-file lists or unsupported LCOV data."""


@dataclass(frozen=True, order=True)
class FileIdentity:
    repository: str
    path: str


@dataclass(frozen=True)
class CodeFileList:
    primary_need_id: str
    files: frozenset[FileIdentity]


@dataclass
class FileCoverage:
    # Item identities, rather than record totals, make duplicate test records
    # idempotent while retaining complementary hits from different tests.
    lines: dict[int, bool] = field(default_factory=dict)
    branches: dict[tuple[int, str, str], bool] = field(default_factory=dict)


def _relative_source_path(raw: str) -> str:
    """Validate a path within an already identified repository."""
    path = raw.replace("\\", "/")
    if path.startswith("/") or re.match(r"^[A-Za-z]:", path):
        raise CoverageError(
            f"unsupported path {raw!r}; expected a repository-relative source path"
        )
    if ".." in path.split("/"):
        raise CoverageError(f"parent traversal in source path: {raw!r}")
    path = "/".join(part for part in path.split("/") if part and part != ".")
    if not path:
        raise CoverageError(f"empty source path: {raw!r}")
    if "_virtual_includes" in path.split("/"):
        raise CoverageError(f"virtual-include path is not canonical: {raw!r}")
    return path


def file_identity(raw: str) -> FileIdentity:
    """Interpret LCOV's Bazel path prefixes and retain repository identity."""
    path = raw.replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    path = re.sub(r"^bazel-out/[^/]+/bin/", "", path)
    repository = "_main"
    if path.startswith("../"):
        repository, separator, path = path[3:].partition("/")
        if not separator:
            raise CoverageError(f"external path has no file: {raw!r}")
    elif path.startswith("external/"):
        repository, separator, path = path[len("external/") :].partition("/")
        if not separator:
            raise CoverageError(f"external path has no file: {raw!r}")
    if not repository:
        raise CoverageError(f"external path has no repository: {raw!r}")
    return FileIdentity(repository, _relative_source_path(path))


def _string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise CoverageError(f"{name} must be a nonempty string")
    return value


def load_code_file_lists(path: Path) -> list[CodeFileList]:
    """Load code-file lists and validate unique primary Need IDs."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != 1:
        raise CoverageError("code-file lists must have version 1")
    data = cast(dict[str, object], data)
    entries = data.get("code_file_lists")
    if not isinstance(entries, list):
        raise CoverageError("code-file lists must contain a code_file_lists list")
    code_file_lists: dict[str, CodeFileList] = {}
    for entry in cast(list[object], entries):
        if not isinstance(entry, dict) or not isinstance(entry.get("files"), list):
            raise CoverageError(
                "each code file list must contain a primary_need_id and a files list"
            )
        entry = cast(dict[str, object], entry)
        primary_need_id = _string(entry.get("primary_need_id"), "primary_need_id")
        files: set[FileIdentity] = set()
        for item in cast(list[object], entry["files"]):
            if not isinstance(item, dict):
                raise CoverageError(
                    "code file lists must contain repository/path objects"
                )
            item = cast(dict[str, object], item)
            repository = _string(item.get("repository"), "file repository")
            file_path = _string(item.get("path"), "file path")
            # The export already identifies the repository. A directory named
            # "external" inside it is an ordinary directory, not an LCOV prefix.
            files.add(FileIdentity(repository, _relative_source_path(file_path)))
        if primary_need_id in code_file_lists:
            raise CoverageError(f"duplicate primary Need ID: {primary_need_id}")
        code_file_lists[primary_need_id] = CodeFileList(
            primary_need_id, frozenset(files)
        )
    return list(code_file_lists.values())


def _number(value: str, *, positive: bool = False) -> int:
    number = int(value)
    if number < (1 if positive else 0):
        raise CoverageError(
            f"invalid {'line number' if positive else 'counter'}: {value!r}"
        )
    return number


@dataclass
class _Record:
    coverage: FileCoverage
    line_items: bool = False
    branch_items: bool = False
    totals: dict[str, int] = field(default_factory=dict)

    def feed(self, tag: str, value: str) -> None:
        if tag == "DA":
            parts = value.split(",")
            line, count = _number(parts[0], positive=True), _number(parts[1])
            self.coverage.lines[line] = (
                self.coverage.lines.get(line, False) or count > 0
            )
            self.line_items = True
        elif tag == "BRDA":
            # Branch expressions may themselves contain commas. Only the first
            # two separators and the final separator delimit structural fields.
            line, block, rest = value.split(",", 2)
            branch, taken = rest.rsplit(",", 1)
            if not block or not branch:
                raise CoverageError("branch identity must include block and branch")
            key = (_number(line, positive=True), str(_number(block)), branch)
            hit = taken != "-" and _number(taken) > 0
            self.coverage.branches[key] = self.coverage.branches.get(key, False) or hit
            self.branch_items = True
        elif tag in ("LF", "LH", "BRF", "BRH"):
            self.totals[tag] = _number(value)

    def finish(self) -> None:
        # A summary cannot recover the item identities needed to combine records.
        # A different metric must not be substituted just for these files.
        for found, hit, present in (
            ("LF", "LH", self.line_items),
            ("BRF", "BRH", self.branch_items),
        ):
            if not present and (self.totals.get(found, 0) or self.totals.get(hit, 0)):
                raise CoverageError(
                    f"{found}/{hit} without item records is unsupported"
                )


def parse_lcov(text: str) -> dict[FileIdentity, FileCoverage]:
    """Union source items; summary counters never override DA/BRDA semantics."""
    files: dict[FileIdentity, FileCoverage] = {}
    record: _Record | None = None
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        tag, _, value = line.partition(":")
        try:
            if tag == "SF":
                if record is not None:
                    record.finish()
                identity = file_identity(value)
                record = _Record(files.setdefault(identity, FileCoverage()))
            elif line == "end_of_record":
                if record is not None:
                    record.finish()
                record = None
            elif tag in ("DA", "BRDA", "LF", "LH", "BRF", "BRH"):
                if record is None:
                    raise CoverageError(f"{tag} outside a source record")
                record.feed(tag, value)
        except (ValueError, IndexError) as error:
            raise CoverageError(f"LCOV line {number}: {error}") from error
    if record is not None:
        record.finish()
    return files


class Dimension(TypedDict):
    total: int | None
    percent: int | None


class Summary(TypedDict):
    primary_need_id: str
    files: dict[str, int]
    lines: Dimension
    branches: Dimension


def _dimension(records: list[Collection[bool]], measured: bool) -> Dimension:
    total = sum(len(record) for record in records)
    hit = sum(sum(record) for record in records)
    # Integer arithmetic gives a defined round-half-up result without float
    # precision loss. Aggregation happens before rounding, never per file.
    percent = (200 * hit + total) // (2 * total) if total else None
    return {"total": total if measured else None, "percent": percent}


def summarize(
    code_file_lists: list[CodeFileList],
    files: dict[FileIdentity, FileCoverage],
) -> list[Summary]:
    """Aggregate available source items for each primary Need before rounding.

    Missing files contribute to availability counts, but their instrumentation
    is unknown and therefore cannot contribute to line or branch totals.
    """
    summaries: list[Summary] = []
    for code_file_list in sorted(
        code_file_lists, key=lambda code_file_list: code_file_list.primary_need_id
    ):
        records = [files[file] for file in code_file_list.files if file in files]
        measured = len(records)
        total = len(code_file_list.files)
        summaries.append(
            {
                "primary_need_id": code_file_list.primary_need_id,
                "files": {"total": total, "measured": measured},
                "lines": _dimension(
                    [record.lines.values() for record in records], bool(measured)
                ),
                "branches": _dimension(
                    [record.branches.values() for record in records], bool(measured)
                ),
            }
        )
    return summaries


def summary_json(summaries: list[Summary]) -> bytes:
    """Encode the rounded summaries as stable JSON for the Docs CLI."""
    return (
        json.dumps(
            {"version": 1, "coverage_summaries": summaries}, sort_keys=True, indent=2
        )
        + "\n"
    ).encode()


def write_summary(output: Path, content: bytes) -> bool:
    """Atomically publish encoded JSON when its content differs."""
    if output.is_file() and output.read_bytes() == content:
        return False
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as stream:
            temporary = stream.name
            stream.write(content)
        os.replace(temporary, output)
    finally:
        if temporary is not None and os.path.exists(temporary):
            os.unlink(temporary)
    return True


def generate_summary(
    code_file_lists: Path, coverage_report: Path, output: Path
) -> Path:
    """Write coverage summaries for the exported files and return the JSON path.

    An absent report yields unavailable measurements. Parsing finishes before
    writing, so invalid input leaves an existing summary intact.
    """
    selected_files = load_code_file_lists(code_file_lists)
    lcov = (
        coverage_report.read_text(encoding="utf-8") if coverage_report.exists() else ""
    )
    content = summary_json(summarize(selected_files, parse_lcov(lcov)))
    write_summary(output, content)
    return output
