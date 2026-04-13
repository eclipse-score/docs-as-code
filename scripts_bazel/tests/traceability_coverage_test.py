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

"""Tests for traceability_coverage.py."""

import json
import os
import subprocess
import sys
from pathlib import Path

_MY_PATH = Path(__file__).parent


def _write_needs_json(tmp_path: Path) -> Path:
    needs_json = tmp_path / "needs.json"
    payload = {
        "current_version": "main",
        "versions": {
            "main": {
                "needs": {
                    "REQ_1": {
                        "id": "REQ_1",
                        "type": "tool_req",
                        "implemented": "YES",
                        "source_code_link": "src/foo.py:10",
                        "testlink": "",
                    },
                    "REQ_2": {
                        "id": "REQ_2",
                        "type": "tool_req",
                        "implemented": "PARTIAL",
                        "source_code_link": "",
                        "testlink": "tests/test_foo.py::test_bar",
                    },
                    "REQ_3": {
                        "id": "REQ_3",
                        "type": "tool_req",
                        "implemented": "NO",
                        "source_code_link": "",
                        "testlink": "",
                    },
                    "TC_1": {
                        "id": "TC_1",
                        "type": "testcase",
                        "partially_verifies": "REQ_1, REQ_2",
                        "fully_verifies": "",
                    },
                    "TC_2": {
                        "id": "TC_2",
                        "type": "testcase",
                        "partially_verifies": "",
                        "fully_verifies": "",
                    },
                    "TC_3": {
                        "id": "TC_3",
                        "type": "testcase",
                        "partially_verifies": "",
                        "fully_verifies": "REQ_UNKNOWN",
                    },
                }
            }
        },
    }
    needs_json.write_text(json.dumps(payload), encoding="utf-8")
    return needs_json


def test_traceability_coverage_thresholds_pass(tmp_path: Path) -> None:
    needs_json = _write_needs_json(tmp_path)
    output_json = tmp_path / "summary.json"

    result = subprocess.run(
        [
            sys.executable,
            _MY_PATH.parent / "traceability_coverage.py",
            "--needs-json",
            str(needs_json),
            "--min-req-code",
            "50",
            "--min-req-test",
            "50",
            "--min-req-fully-linked",
            "0",
            "--min-tests-linked",
            "60",
            "--json-output",
            str(output_json),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Threshold check passed." in result.stdout
    assert output_json.exists()

    summary = json.loads(output_json.read_text(encoding="utf-8"))
    assert summary["requirements"]["total"] == 2
    assert summary["requirements"]["with_code_link"] == 1
    assert summary["requirements"]["with_test_link"] == 1
    assert summary["requirements"]["fully_linked"] == 0
    assert summary["tests"]["total"] == 3
    assert summary["tests"]["linked_to_requirements"] == 2
    assert len(summary["tests"]["broken_references"]) == 1


def test_traceability_coverage_thresholds_fail(tmp_path: Path) -> None:
    needs_json = _write_needs_json(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            _MY_PATH.parent / "traceability_coverage.py",
            "--needs-json",
            str(needs_json),
            "--min-req-code",
            "80",
            "--min-req-test",
            "80",
            "--min-req-fully-linked",
            "80",
            "--min-tests-linked",
            "80",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "Threshold check failed:" in result.stdout


def test_traceability_coverage_fails_on_broken_refs(tmp_path: Path) -> None:
    needs_json = _write_needs_json(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            _MY_PATH.parent / "traceability_coverage.py",
            "--needs-json",
            str(needs_json),
            "--min-req-code",
            "0",
            "--min-req-test",
            "0",
            "--min-req-fully-linked",
            "0",
            "--min-tests-linked",
            "0",
            "--fail-on-broken-test-refs",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "broken testcase references found:" in result.stdout


def test_traceability_coverage_prints_unlinked_requirements(tmp_path: Path) -> None:
    needs_json = _write_needs_json(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            _MY_PATH.parent / "traceability_coverage.py",
            "--needs-json",
            str(needs_json),
            "--min-req-code",
            "0",
            "--min-req-test",
            "0",
            "--min-req-fully-linked",
            "0",
            "--min-tests-linked",
            "0",
            "--print-unlinked-requirements",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Unlinked requirement details:" in result.stdout
    assert "Missing source_code_link: REQ_2" in result.stdout
    assert "Missing testlink:         REQ_1" in result.stdout
    assert "Not fully linked:         REQ_1, REQ_2" in result.stdout


def test_traceability_coverage_accepts_workspace_relative_needs_json(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    needs_json = _write_needs_json(workspace)

    env = dict(os.environ)
    env["BUILD_WORKSPACE_DIRECTORY"] = str(workspace)

    result = subprocess.run(
        [
            sys.executable,
            _MY_PATH.parent / "traceability_coverage.py",
            "--needs-json",
            "needs.json",
            "--min-req-code",
            "0",
            "--min-req-test",
            "0",
            "--min-req-fully-linked",
            "0",
            "--min-tests-linked",
            "0",
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=env,
    )

    assert result.returncode == 0
    assert f"Traceability input: {needs_json}" in result.stdout
