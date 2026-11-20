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
from score_pytest.attribute_plugin import add_test_properties

import scripts_bazel.merge_sourcelinks
from src.helper_lib.repo_info import LOCAL_REPO

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
                {"repo_name": LOCAL_REPO, "hash": "", "url": ""},
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
                {"repo_name": LOCAL_REPO, "hash": "", "url": ""},
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
                {"repo_name": LOCAL_REPO, "hash": "", "url": ""},
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


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_merge_sourcelinks_basic(
    create_local_json_files: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch
):
    """Test merge sourcelinks basic."""
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


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_merge_sourcelinks_deduplicates_identical_references(
    create_local_json_files: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch
):
    """Test merge sourcelinks deduplicates identical references."""
    file1, _, output_file = create_local_json_files

    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(_MY_PATH.parent / "merge_sourcelinks.py"),
            "--output",
            str(output_file),
            str(file1),
            str(file1),
        ],
    )

    assert scripts_bazel.merge_sourcelinks.main() == 0
    assert json.loads(output_file.read_text()) == [
        {
            "file": "test1.py",
            "line": 10,
            "tag": "# req-Id:",
            "need": "tool_req__docs_arch_types",
            "full_line": "# req-Id: tool_req__docs_arch_types",
            "repo_name": LOCAL_REPO,
            "hash": "",
            "url": "",
        }
    ]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_merge_sourcelinks_with_one_empty_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Test merge sourcelinks with one empty file."""
    file1 = tmp_path / "links1.json"
    file1_text: list[dict[str, str | int]] = [
        {"repo_name": LOCAL_REPO, "hash": "", "url": ""},
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
            "repo_name": LOCAL_REPO,  # comes from first dict in input
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


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_merge_sourcelinks_wrong_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
):
    """Test merge sourcelinks wrong schema."""
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


@pytest.mark.parametrize("mixed_cache", [False, True], ids=["separate", "mixed"])
@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_merge_sourcelinks_with_known_good(
    tmp_path: Path,
    mixed_cache: bool,
    create_external_repo_json_files: tuple[Path, Path, Path],
    monkeypatch: pytest.MonkeyPatch,
):
    """Test merge sourcelinks with known good."""
    file1, file2, output_file = create_external_repo_json_files
    input_files = [file1, file2]
    if mixed_cache:
        external_metadata, external_link = json.loads(file1.read_text())
        local_metadata, local_link = json.loads(file2.read_text())
        file1.write_text(
            json.dumps(
                [
                    {"repo_name": "", "hash": "", "url": ""},
                    {**external_link, "repo_name": external_metadata["repo_name"]},
                    {**local_link, "repo_name": local_metadata["repo_name"]},
                ]
            )
        )
        input_files = [file1]
    known_good_file = tmp_path / "known_good.json"
    known_good_file.write_text(json.dumps(VALID_KNOWN_GOOD))

    test_args: list[Path | str] = [
        _MY_PATH.parent
        / "merge_sourcelinks.py",  # sys.argv[0] is always the script name
        "--output",
        str(output_file),
        "--known_good",
        str(known_good_file),
        *map(str, input_files),
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
        "repo_name": LOCAL_REPO,
        "hash": "",
        "url": "",
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


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_merge_sourcelinks_without_known_good_preserves_external_metadata(
    create_external_repo_json_files: tuple[Path, Path, Path],
    monkeypatch: pytest.MonkeyPatch,
):
    """Test merge sourcelinks without known good preserves external metadata."""
    file1, file2, output_file = create_external_repo_json_files
    test_args: list[Path | str] = [
        _MY_PATH.parent / "merge_sourcelinks.py",
        "--output",
        str(output_file),
        str(file1),
        str(file2),
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    assert scripts_bazel.merge_sourcelinks.main() == 0

    data: list[dict[str, str | int]] = json.loads(output_file.read_text())
    external_link = next(entry for entry in data if entry["file"] == "test1.py")
    assert external_link["repo_name"] == "score_baselibs"
    assert external_link["url"] == "https://github.com/eclipse-score/baselibs.git"
    assert external_link["hash"] == "158fe6a7b791c58f6eac5f7e4662b8db0cf9ac6e"


@pytest.mark.parametrize(
    "module_entry",
    [
        None,
        {"hash": "abc", "repo": None},
        {"repo": "https://github.com/example/vendor"},
    ],
    ids=["missing-module", "missing-url", "missing-revision"],
)
@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_merge_keeps_links_with_unresolved_external_repositories(
    tmp_path: Path,
    create_external_repo_json_files: tuple[Path, Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    module_entry: dict[str, str | None] | None,
):
    """A mixed bundle still merges when one repository cannot be resolved."""
    bundle_file, local_file, output_file = create_external_repo_json_files
    local_repo, local_link = json.loads(local_file.read_text())
    _, external_link = json.loads(bundle_file.read_text())
    missing_repo = {"repo_name": "vendor", "hash": "", "url": ""}
    bundle_file.write_text(
        json.dumps(
            [
                local_repo,
                {**local_link, **local_repo},
                {**external_link, **missing_repo},
                {**external_link, **missing_repo, "line": 42},
            ]
        )
    )
    modules: dict[str, dict[str, str | None]] = {
        "score_baselibs": {
            "repo": "https://github.com/eclipse-score/baselibs",
            "hash": "abc",
        }
    }
    if module_entry is not None:
        modules["vendor"] = module_entry
    known_good_file = tmp_path / "known_good.json"
    known_good_file.write_text(json.dumps({"modules": {"target_sw": modules}}))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "merge_sourcelinks.py",
            "--output",
            str(output_file),
            "--known_good",
            str(known_good_file),
            str(bundle_file),
        ],
    )

    assert scripts_bazel.merge_sourcelinks.main() == 0

    links = json.loads(output_file.read_text())
    assert links == [
        {**local_link, **local_repo},
        {**external_link, **missing_repo},
        {**external_link, **missing_repo, "line": 42},
    ]
    warnings = [
        record.getMessage()
        for record in caplog.records
        if record.levelno == logging.WARNING
    ]
    assert len(warnings) == 1
    assert "Module vendor" in warnings[0]
