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
import subprocess
import sys
from pathlib import Path

_MY_PATH = Path(__file__).parent


def test_merge_sourcelinks_basic(tmp_path: Path) -> None:
    """Test basic merge functionality."""
    # Create test JSON files with correct schema
    file1 = tmp_path / "links1.json"
    file1.write_text(
        json.dumps(
            [
                {
                    "file": "test1.py",
                    "line": 10,
                    "tag": "# req-Id:",
                    "need": "tool_req__docs_arch_types",
                    "full_line": "# req-Id: tool_req__docs_arch_types",
                }
            ]
        )
    )

    file2 = tmp_path / "links2.json"
    file2.write_text(
        json.dumps(
            [
                {
                    "file": "test2.py",
                    "line": 20,
                    "tag": "# req-Id:",
                    "need": "gd_req__req_validity",
                    "full_line": "# req-Id: gd_req__req_validity",
                }
            ]
        )
    )

    output_file = tmp_path / "merged.json"

    result = subprocess.run(
        [
            sys.executable,
            _MY_PATH.parent / "merge_sourcelinks.py",
            "--output",
            str(output_file),
            str(file1),
            str(file2),
        ],
    )

    assert result.returncode == 0
    assert output_file.exists()

    with open(output_file) as f:
        data: list[dict[str, str | int]] = json.load(f)
    assert isinstance(data, list)
    assert len(data) == 2

    # Verify schema of merged entries
    for entry in data:
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

    # Verify specific entries
    assert any(
        entry["need"] == "tool_req__docs_arch_types" and entry["file"] == "test1.py"
        for entry in data
    )
    assert any(
        entry["need"] == "gd_req__req_validity" and entry["file"] == "test2.py"
        for entry in data
    )
