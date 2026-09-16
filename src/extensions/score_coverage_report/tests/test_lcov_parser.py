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
"""Unit tests for the LCOV parser and per-component aggregation."""

from src.extensions.score_coverage_report.lcov_parser import (
    FileCoverage,
    assign_files_to_components,
    parse_lcov,
)

LCOV_TWO_FILES = """\
TN:
SF:src/parser/reader.cpp
DA:1,1
DA:2,0
DA:3,3
BRDA:2,0,0,1
BRDA:2,0,1,0
LF:3
LH:2
BRF:2
BRH:1
end_of_record
SF:src/logging/sink.cpp
DA:1,5
DA:2,5
LF:2
LH:2
end_of_record
"""


def test_parse_lcov_computes_line_and_branch_totals_from_records():
    files = parse_lcov(LCOV_TWO_FILES)

    assert set(files) == {"src/parser/reader.cpp", "src/logging/sink.cpp"}

    reader = files["src/parser/reader.cpp"]
    assert reader.lines_found == 3
    assert reader.lines_hit == 2
    assert reader.branches_found == 2
    assert reader.branches_hit == 1
    assert reader.line_percent == 66.7
    assert reader.branch_percent == 50.0

    sink = files["src/logging/sink.cpp"]
    assert sink.lines_found == 2
    assert sink.lines_hit == 2
    assert sink.branches_found == 0
    assert sink.branches_hit == 0
    assert sink.line_percent == 100.0
    assert sink.branch_percent is None


def test_parse_lcov_ignores_unknown_record_types():
    text = """\
SF:src/parser/reader.cpp
FN:1,foo
FNDA:4,foo
FNF:1
FNH:1
DA:1,4
end_of_record
"""
    files = parse_lcov(text)
    assert files["src/parser/reader.cpp"].lines_found == 1
    assert files["src/parser/reader.cpp"].lines_hit == 1


def test_parse_lcov_tolerates_missing_trailing_end_of_record():
    text = "SF:src/parser/reader.cpp\nDA:1,1\n"
    files = parse_lcov(text)
    assert files["src/parser/reader.cpp"].lines_found == 1


def test_parse_lcov_empty_text_returns_no_files():
    assert parse_lcov("") == {}


def test_assign_files_to_components_matches_relative_prefix():
    files = parse_lcov(LCOV_TWO_FILES)

    result = assign_files_to_components(files, {"comp__example_parser": "src/parser"})

    coverage = result["comp__example_parser"]
    assert coverage.component_id == "comp__example_parser"
    assert [f.path for f in coverage.files] == ["src/parser/reader.cpp"]
    assert coverage.lines_found == 3
    assert coverage.lines_hit == 2
    assert coverage.line_percent == 66.7


def test_assign_files_to_components_matches_prefix_embedded_in_absolute_path():
    sandbox_path = (
        "/root/.cache/bazel/exec/sandbox/1/execroot/_main/src/parser/reader.cpp"
    )
    files = {
        sandbox_path: FileCoverage(path=sandbox_path, lines_found=10, lines_hit=5),
    }

    result = assign_files_to_components(files, {"comp__example_parser": "src/parser"})

    assert result["comp__example_parser"].lines_found == 10
    assert result["comp__example_parser"].lines_hit == 5


def test_assign_files_to_components_does_not_match_sibling_directory():
    # "src/parser" must not match "src/parserx/..." or similar look-alikes.
    result = assign_files_to_components(
        {"src/parserx/other.cpp": FileCoverage(path="src/parserx/other.cpp")},
        {"comp__example_parser": "src/parser"},
    )

    assert result == {}


def test_assign_files_to_components_omits_components_without_matches():
    files = parse_lcov(LCOV_TWO_FILES)

    result = assign_files_to_components(
        files, {"comp__example_missing": "src/does_not_exist"}
    )

    assert "comp__example_missing" not in result


def test_assign_files_to_components_sums_multiple_files():
    all_files = dict(parse_lcov(LCOV_TWO_FILES))
    all_files["src/parser/writer.cpp"] = FileCoverage(
        path="src/parser/writer.cpp", lines_found=4, lines_hit=4
    )

    result = assign_files_to_components(
        all_files, {"comp__example_parser": "src/parser"}
    )

    coverage = result["comp__example_parser"]
    assert sorted(f.path for f in coverage.files) == [
        "src/parser/reader.cpp",
        "src/parser/writer.cpp",
    ]
    assert coverage.lines_found == 7
    assert coverage.lines_hit == 6


def test_assign_files_to_components_gives_nested_file_to_most_specific_component():
    # comp__example_parser "consists_of" comp__example_parser_detail, so their
    # source roots nest. The child must claim its own file exclusively, or the
    # parent would count the same lines a second time.
    files = {
        "src/parser/reader.cpp": FileCoverage(
            path="src/parser/reader.cpp", lines_found=10, lines_hit=10
        ),
        "src/parser/detail/adapter.cpp": FileCoverage(
            path="src/parser/detail/adapter.cpp",
            lines_found=4,
            lines_hit=1,
        ),
    }

    result = assign_files_to_components(
        files,
        {
            "comp__example_parser": "src/parser",
            "comp__example_parser_detail": "src/parser/detail",
        },
    )

    assert [f.path for f in result["comp__example_parser"].files] == [
        "src/parser/reader.cpp"
    ]
    assert result["comp__example_parser"].lines_found == 10
    assert [f.path for f in result["comp__example_parser_detail"].files] == [
        "src/parser/detail/adapter.cpp"
    ]
    assert result["comp__example_parser_detail"].lines_found == 4


def test_assign_files_to_components_ignores_components_without_source_root():
    files = parse_lcov(LCOV_TWO_FILES)

    result = assign_files_to_components(files, {"comp__example_no_root": ""})

    assert result == {}
