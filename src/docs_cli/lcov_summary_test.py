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
"""Coverage identity, metric and cache contracts for LCOV summaries."""

import json
import os
from pathlib import Path

import pytest

from src.docs_cli.lcov_summary import (
    CodeFileList,
    CoverageError,
    FileIdentity,
    file_identity,
    load_code_file_lists,
    parse_lcov,
    summarize,
    summary_json,
    write_summary,
)


def code_files(*paths: str, name: str = "comp__example") -> CodeFileList:
    return CodeFileList(name, frozenset(file_identity(path) for path in paths))


def test_repeated_records_union_line_and_branch_identities():
    text = (
        "SF:src/a.cc\nDA:1,4\nDA:2,0\nBRDA:1,0,0,4\nBRDA:1,0,1,-\nend_of_record\n"
        "SF:src/a.cc\nDA:1,0\nDA:2,8\nBRDA:1,0,0,0\nBRDA:1,0,1,2\nend_of_record\n"
    )
    files = parse_lcov(text + text)
    summary = summarize([code_files("src/a.cc")], files)[0]
    assert summary["lines"] == {"total": 2, "percent": 100}
    assert summary["branches"] == {"total": 2, "percent": 100}


def test_aggregate_before_rounding_and_round_halves_up():
    # An average of file percentages would be 50%; the selected files cover 1/3.
    files = parse_lcov("SF:a\nDA:1,1\nSF:b\nDA:1,0\nDA:2,0\n")
    assert summarize([code_files("a", "b")], files)[0]["lines"]["percent"] == 33
    halves = parse_lcov(
        "SF:a\n" + "".join(f"DA:{n},{int(n <= 1)}\n" for n in range(1, 9))
    )
    assert summarize([code_files("a")], halves)[0]["lines"]["percent"] == 13


def test_missing_uninstrumented_and_measured_zero_are_distinct():
    files = parse_lcov("SF:empty\nLF:0\nBRF:0\nSF:zero\nDA:1,0\nBRDA:1,0,0,-\n")
    summaries = summarize(
        [
            code_files("absent", name="missing"),
            code_files("empty", name="uninstrumented"),
            code_files("zero", name="zero"),
            code_files(name="no_files"),
        ],
        files,
    )
    by_id = {summary["primary_need_id"]: summary for summary in summaries}
    assert by_id["missing"]["files"] == {"total": 1, "measured": 0}
    assert by_id["missing"]["lines"] == {"total": None, "percent": None}
    assert by_id["uninstrumented"]["files"] == {"total": 1, "measured": 1}
    assert by_id["uninstrumented"]["lines"] == {"total": 0, "percent": None}
    assert by_id["zero"]["lines"] == {"total": 1, "percent": 0}
    assert by_id["zero"]["branches"] == {"total": 1, "percent": 0}
    assert by_id["no_files"]["files"] == {"total": 0, "measured": 0}


def test_partial_result_counts_absent_records_without_inventing_instrumented_lines():
    files = parse_lcov("SF:measured\nDA:1,1\n")
    summary = summarize([code_files("measured", "rust.rs", "api.h", "unknown")], files)[
        0
    ]
    assert summary["files"] == {"total": 4, "measured": 1}
    assert summary["lines"] == {"total": 1, "percent": 100}
    assert summary["branches"] == {"total": 0, "percent": None}


def test_exact_file_membership_excludes_siblings_and_retains_explicit_shared_files():
    files = parse_lcov("SF:src/a\nDA:1,1\nSF:src/sibling/b\nDA:1,0\n")
    summaries = summarize(
        [code_files("src/a", name="parent"), code_files("src/a", name="shared")],
        files,
    )
    assert len(summaries) == 2
    assert all(
        summary["lines"] == {"total": 1, "percent": 100} for summary in summaries
    )


def test_canonical_bazel_paths_preserve_repository_identity():
    assert file_identity(
        "./bazel-out/k8-fastbuild/bin/pkg/generated.h"
    ) == FileIdentity("_main", "pkg/generated.h")
    assert file_identity("../dep+/include/x.h") == FileIdentity("dep+", "include/x.h")
    assert file_identity("external/dep+/include/x.h") == FileIdentity(
        "dep+", "include/x.h"
    )
    files = parse_lcov("SF:src/a\nDA:1,1\nSF:external/other/src/a\nDA:1,0\n")
    assert summarize([code_files("src/a")], files)[0]["lines"]["percent"] == 100
    assert len(files) == 2


@pytest.mark.parametrize(
    "path",
    [
        "/other/execroot/src/a",
        "../repo/../../a",
        "a/../b",
        "",
        "C:/build/a",
        "pkg/_virtual_includes/api/a.h",
    ],
)
def test_unsupported_paths_do_not_fall_back_to_suffix_matching(path: str):
    with pytest.raises(CoverageError):
        file_identity(path)


def test_source_items_determine_metric_even_when_llvm_summary_differs():
    files = parse_lcov("SF:a\nDA:1,1\nDA:2,1\nLF:3\nLH:2\nBRDA:1,0,0,1\nBRF:2\nBRH:1\n")
    summary = summarize([code_files("a")], files)[0]
    assert summary["lines"] == {"total": 2, "percent": 100}
    assert summary["branches"] == {"total": 1, "percent": 100}


@pytest.mark.parametrize(
    "text",
    [
        "SF:a\nLF:2\nLH:1\n",
        "SF:a\nBRF:1\n",
        "SF:a\nDA:1,-1\n",
        "SF:a\nBRDA:1,0,1,invalid\n",
        "DA:1,0\n",
        "SF:a\nDA:0,1\n",
        "SF:a\nBRDA:1,U0,0,0\n",
    ],
)
def test_unsupported_or_invalid_measurements_are_diagnosed(text: str):
    with pytest.raises(CoverageError):
        parse_lcov(text)


def test_equivalent_rounded_summaries_preserve_bytes_and_modification_time(
    tmp_path: Path,
):
    output = tmp_path / "summary.json"

    def summary_for(hits: int, counter: int):
        text = "SF:a\n" + "".join(
            f"DA:{n},{counter if n <= hits else 0}\n" for n in range(1, 1001)
        )
        return summarize([code_files("a")], parse_lcov(text))

    assert write_summary(output, summary_json(summary_for(501, 1)))
    os.utime(output, ns=(123456789000, 123456789000))
    original = output.read_bytes()
    # Both 50.1% and 50.2% round to 50%, regardless of execution counters.
    assert not write_summary(output, summary_json(summary_for(502, 9999)))
    assert output.read_bytes() == original
    assert output.stat().st_mtime_ns == 123456789000
    assert write_summary(output, summary_json(summary_for(510, 1)))
    assert output.read_bytes() != original
    assert output.stat().st_mtime_ns != 123456789000


def test_changed_totals_and_availability_update_output_even_at_same_percentage(
    tmp_path: Path,
):
    output = tmp_path / "summary.json"
    files = parse_lcov("SF:a\nDA:1,1\nSF:b\nDA:1,1\n")
    assert write_summary(output, summary_json(summarize([code_files("a")], files)))
    assert write_summary(output, summary_json(summarize([code_files("a", "b")], files)))
    assert write_summary(
        output, summary_json(summarize([code_files("a", "b", "missing")], files))
    )


def test_code_file_lists_validate_and_deduplicate_file_membership(tmp_path: Path):
    path = tmp_path / "code_file_lists.json"
    entry: dict[str, object] = {
        "primary_need_id": "comp",
        "files": [{"repository": "repo+", "path": "src/a"}] * 2,
    }
    path.write_text(json.dumps({"version": 1, "code_file_lists": [entry]}))
    assert load_code_file_lists(path) == [
        CodeFileList("comp", frozenset({FileIdentity("repo+", "src/a")}))
    ]
    path.write_text(json.dumps({"version": 1, "code_file_lists": [entry, entry]}))
    with pytest.raises(CoverageError, match="duplicate primary Need ID"):
        load_code_file_lists(path)


@pytest.mark.parametrize(
    ("backend", "total", "percent"), [("llvm", 9, 89), ("gcov", 6, 83)]
)
def test_coverage_tool_golden_excerpts_preserve_backend_item_counts(
    backend: str, total: int, percent: int
):
    """Both report layouts work; backend line definitions remain intentionally distinct."""
    text = (Path(__file__).parent / "fixtures" / f"{backend}.info").read_text()
    summary = summarize([code_files("src/coverable.cpp")], parse_lcov(text))[0]
    assert summary["lines"] == {"total": total, "percent": percent}
    assert summary["branches"] == {"total": 4, "percent": 75}


def test_record_and_code_file_list_order_do_not_change_output(tmp_path: Path):
    output = tmp_path / "summary.json"
    a = "SF:a\nDA:1,1\nBRDA:1,0,0,1\nend_of_record\n"
    b = "SF:b\nDA:1,0\nBRDA:1,1,0,0\nend_of_record\n"
    code_file_lists = [
        code_files("a", name="second"),
        code_files("b", name="first"),
    ]
    assert write_summary(
        output, summary_json(summarize(code_file_lists, parse_lcov(a + b)))
    )
    assert not write_summary(
        output,
        summary_json(summarize(list(reversed(code_file_lists)), parse_lcov(b + a))),
    )


def test_branch_expressions_with_commas_retain_identity_across_records():
    text = (
        "SF:a\nBRDA:1,0,check(x,y),1\nBRDA:1,1,check(x,y),-\nend_of_record\n"
        "SF:a\nBRDA:1,0,check(x,y),0\nBRDA:1,1,check(x,y),2\nend_of_record\n"
    )
    summary = summarize([code_files("a")], parse_lcov(text))[0]
    assert summary["branches"] == {"total": 2, "percent": 100}


def test_canonical_external_path_forms_merge_before_aggregation():
    text = (
        "SF:external/repo+/src/a\nDA:1,1\nDA:2,0\nend_of_record\n"
        "SF:../repo+/src/a\nDA:1,0\nDA:2,1\nend_of_record\n"
    )
    summary = summarize([code_files("external/repo+/src/a")], parse_lcov(text))[0]
    assert summary["files"] == {"total": 1, "measured": 1}
    assert summary["lines"] == {"total": 2, "percent": 100}


def test_explicit_repository_keeps_an_external_named_source_directory(tmp_path: Path):
    """An exported path is already scoped; only LCOV paths carry repository prefixes."""
    path = tmp_path / "code_file_lists.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "code_file_lists": [
                    {
                        "primary_need_id": "mod__example",
                        "files": [
                            {"repository": "dep+", "path": "external/vendor/header.h"}
                        ],
                    }
                ],
            }
        )
    )
    selected = load_code_file_lists(path)
    report = parse_lcov("SF:external/dep+/external/vendor/header.h\nDA:1,1\n")
    summary = summarize(selected, report)[0]
    assert summary["files"] == {"total": 1, "measured": 1}
    assert summary["lines"] == {"total": 1, "percent": 100}


@pytest.mark.parametrize("path", ["../dep+/a", "/tmp/a", "C:/build/a"])
def test_exported_source_paths_must_stay_inside_their_repository(
    tmp_path: Path, path: str
):
    file_lists = tmp_path / "code_file_lists.json"
    file_lists.write_text(
        json.dumps(
            {
                "version": 1,
                "code_file_lists": [
                    {
                        "primary_need_id": "mod__example",
                        "files": [{"repository": "dep+", "path": path}],
                    }
                ],
            }
        )
    )
    with pytest.raises(CoverageError):
        load_code_file_lists(file_lists)
