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

"""Tests for merge_sourcelinks.py"""

import json
import logging
import sys
from pathlib import Path

import pytest

import scripts_bazel.merge_sourcelinks

LOGGER = logging.getLogger(__name__)

_MY_PATH = Path(__file__).parent


def assert_json_internal_types(input: list[dict[str, str | int]]):
    for entry in input:
        assert "file" in entry
        assert "line" in entry
        assert "tag" in entry
        assert "need" in entry
        assert "full_line" in entry

        assert isinstance(entry["file"], str)
        assert isinstance(entry["line"], int)
        assert isinstance(entry["tag"], str)
        assert isinstance(entry["need"], str)
        assert isinstance(entry["full_line"], str)


@pytest.fixture
def create_local_json_files(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Test basic merge functionality."""
    # Create test JSON files with correct schema
    file1 = tmp_path / "links1.json"
    file1.write_text(
        json.dumps(
            [
                {"repo_name": "local_repo", "hash": "", "url": ""},
                {
                    "file": "test1.py",
                    "line": 10,
                    "tag": "# req-Id:",
                    "need": "tool_req__docs_arch_types",
                    "full_line": "# req-Id: tool_req__docs_arch_types",
                },
            ]
        )
    )

    file2 = tmp_path / "links2.json"
    file2.write_text(
        json.dumps(
            [
                {"repo_name": "local_repo", "hash": "", "url": ""},
                {
                    "file": "test2.py",
                    "line": 20,
                    "tag": "# req-Id:",
                    "need": "gd_req__req_validity",
                    "full_line": "# req-Id: gd_req__req_validity",
                },
            ]
        )
    )
    output_file = tmp_path / "merged.json"
    return file1, file2, output_file


@pytest.fixture
def create_external_repo_json_files(tmp_path: Path) -> tuple[Path, Path, Path]:
    file1 = tmp_path / "links1.json"
    file1.write_text(
        json.dumps(
            [
                {
                    "repo_name": "score_baselibs",
                    "url": "https://github.com/eclipse-score/baselibs.git",
                    "hash": "158fe6a7b791c58f6eac5f7e4662b8db0cf9ac6e",
                },
                {
                    "file": "test1.py",
                    "line": 10,
                    "tag": "# req-Id:",
                    "need": "tool_req__docs_arch_types",
                    "full_line": "# req-Id: tool_req__docs_arch_types",
                },
            ]
        )
    )

    file2 = tmp_path / "links2.json"
    file2.write_text(
        json.dumps(
            [
                {"repo_name": "local_repo", "hash": "", "url": ""},
                {
                    "file": "test2.py",
                    "line": 20,
                    "tag": "# req-Id:",
                    "need": "gd_req__req_validity",
                    "full_line": "# req-Id: gd_req__req_validity",
                },
            ]
        )
    )
    output_file = tmp_path / "merged.json"
    return file1, file2, output_file


def test_merge_sourcelinks_basic(
    create_local_json_files: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch
):
    file1, file2, output_file = create_local_json_files

    test_args: list[Path | str] = [
        _MY_PATH.parent
        / "merge_sourcelinks.py",  # sys.argv[0] is always the script name
        "--output",
        str(output_file),
        str(file1),
        str(file2),
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    result = scripts_bazel.merge_sourcelinks.main()

    assert result == 0
    assert output_file.exists()

    with open(output_file) as f:
        data: list[dict[str, str | int]] = json.load(f)
    assert isinstance(data, list)
    assert len(data) == 2

    # Verify schema of merged entries

    # Verify specific entries
    assert any(
        entry["need"] == "tool_req__docs_arch_types" and entry["file"] == "test1.py"
        for entry in data
    )
    assert any(
        entry["need"] == "gd_req__req_validity" and entry["file"] == "test2.py"
        for entry in data
    )


def test_merge_sourcelinks_with_one_empty_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    file1 = tmp_path / "links1.json"
    file1_text: list[dict[str, str | int]] = [
        {"repo_name": "local_repo", "hash": "", "url": ""},
        {
            "file": "test1.py",
            "line": 10,
            "tag": "# req-Id:",
            "need": "tool_req__docs_arch_types",
            "full_line": "# req-Id: tool_req__docs_arch_types",
        },
    ]
    file1.write_text(json.dumps(file1_text))
    file2 = tmp_path / "links2.json"
    file2.write_text(json.dumps([]))
    output_file = tmp_path / "merged.json"
    test_args: list[Path | str] = [
        _MY_PATH.parent
        / "merge_sourcelinks.py",  # sys.argv[0] is always the script name
        "--output",
        str(output_file),
        str(file1),
        str(file2),
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    result = scripts_bazel.merge_sourcelinks.main()
    assert result == 0
    with open(output_file) as f:
        data: list[dict[str, str | int]] = json.load(f)
    assert isinstance(data, list)
    assert len(data) == 1

    # It should only contain info of the NON empty file.
    # Empty file should be a no-op
    wanted_info: list[dict[str, str | int]] = [
        {
            "file": "test1.py",
            "line": 10,
            "tag": "# req-Id:",
            "need": "tool_req__docs_arch_types",
            "full_line": "# req-Id: tool_req__docs_arch_types",
            "repo_name": "local_repo",  # comes from first dict in input
            "hash": "",  # comes from first dict in input
            "url": "",  # comes from first dict in input
        }
    ]
    assert data == wanted_info
    # Verify schema of merged entries
    assert_json_internal_types(data)
    assert any(
        entry["need"] == "tool_req__docs_arch_types" and entry["file"] == "test1.py"
        for entry in data
    )


def test_merge_sourcelinks_wrong_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
):
    file1 = tmp_path / "links1.json"
    file1_text: list[dict[str, str | int]] = [
        {
            "file": "test1.py",
            "line": 10,
            "tag": "# req-Id:",
            "need": "tool_req__docs_arch_types",
            "full_line": "# req-Id: tool_req__docs_arch_types",
        },
    ]
    file1.write_text(json.dumps(file1_text))
    output_file = tmp_path / "merged.json"
    test_args: list[Path | str] = [
        _MY_PATH.parent
        / "merge_sourcelinks.py",  # sys.argv[0] is always the script name
        "--output",
        str(output_file),
        str(file1),
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    scripts_bazel.merge_sourcelinks.main()
    error_text = (
        f"Unexpected schema in sourcelinks file '{file1}': "
        "expected first element to be a metadata dict "
        "with a 'repo_name' key. "
    )
    assert error_text in caplog.text


# Taken from score_source_code_linker.test_helpers
VALID_KNOWN_GOOD = {
    "modules": {
        "target_sw": {
            "score_baselibs": {
                "repo": "https://github.com/eclipse-score/baselibs.git",
                "hash": "158fe6a7b791c58f6eac5f7e4662b8db0cf9ac6e",
            },
            "score_communication": {
                "repo": "https://github.com/eclipse-score/communication.git",
                "hash": "56448a5589a5f7d3921b873e8127b824a8c1ca95",
            },
        },
        "tooling": {
            "score_docs_as_code": {
                "repo": "https://github.com/eclipse-score/docs-as-code.git",
                "hash": "c1207676afe6cafd25c35d420e73279a799515d8",
            }
        },
    }
}


def test_merge_sourcelinks_with_known_good(
    tmp_path: Path,
    create_external_repo_json_files: tuple[Path, Path, Path],
    monkeypatch: pytest.MonkeyPatch,
):
    file1, file2, output_file = create_external_repo_json_files
    known_good_file = tmp_path / "known_good.json"
    known_good_file.write_text(json.dumps(VALID_KNOWN_GOOD))

    test_args: list[Path | str] = [
        _MY_PATH.parent
        / "merge_sourcelinks.py",  # sys.argv[0] is always the script name
        "--output",
        str(output_file),
        "--known_good",
        str(known_good_file),
        str(file1),
        str(file2),
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    result = scripts_bazel.merge_sourcelinks.main()
    assert result == 0
    assert output_file.exists()
    with open(output_file) as f:
        data: list[dict[str, str | int]] = json.load(f)
    assert isinstance(data, list)
    assert len(data) == 2
    assert_json_internal_types(data)
    expected_dict1: dict[str, str | int] = {
        "file": "test2.py",
        "line": 20,
        "tag": "# req-Id:",
        "need": "gd_req__req_validity",
        "full_line": "# req-Id: gd_req__req_validity",
        "repo_name": "local_repo",  # comes from first dict in input
        "hash": "",  # comes from first dict in input
        "url": "",  # comes from first dict in input
    }
    expected_dict2: dict[str, str | int] = {
        "file": "test1.py",
        "line": 10,
        "tag": "# req-Id:",
        "need": "tool_req__docs_arch_types",
        "full_line": "# req-Id: tool_req__docs_arch_types",
        "repo_name": "score_baselibs",
        "url": "https://github.com/eclipse-score/baselibs",  # gets filled via known_good
        "hash": "158fe6a7b791c58f6eac5f7e4662b8db0cf9ac6e",  # gets filled via known_good
    }
    assert expected_dict1 in data
    assert expected_dict2 in data
