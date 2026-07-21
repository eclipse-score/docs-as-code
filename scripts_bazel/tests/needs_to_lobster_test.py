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

"""Tests for the needs.json -> LOBSTER lobster-req-trace converter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import scripts_bazel.needs_to_lobster as conv


def _needs_doc() -> dict[str, Any]:
    return {
        "current_version": "1.0",
        "project": "test",
        "versions": {
            "1.0": {
                "needs": {
                    "tool_req__example": {
                        "id": "tool_req__example",
                        "type": "tool_req",
                        "title": "Example tool requirement",
                        "status": "valid",
                        "docname": "internals/requirements/requirements",
                        "lineno": 42,
                        "content": "The tool shall do the thing.",
                        "satisfies": ["gd_req__process_one", "gd_req__process_two"],
                    },
                    "gd_req__process_one": {
                        "id": "gd_req__process_one",
                        "type": "gd_req",
                        "title": "Process requirement one",
                        "status": "valid",
                        "docname": "process/reqs",
                        "lineno": 7,
                    },
                }
            }
        },
    }


def test_convert_emits_req_trace_envelope() -> None:
    report = conv.convert(_needs_doc())
    assert report["schema"] == "lobster-req-trace"
    assert report["version"] == 3
    assert report["generator"] == "needs_to_lobster"
    assert len(report["data"]) == 2


def test_satisfies_becomes_refs() -> None:
    report = conv.convert(_needs_doc())
    items = {item["tag"]: item for item in report["data"]}
    tool = items["req tool_req__example"]
    assert tool["refs"] == ["req gd_req__process_one", "req gd_req__process_two"]
    assert tool["kind"] == "tool_req"
    assert tool["framework"] == "sphinx-needs"
    assert tool["status"] == "valid"
    assert tool["text"] == "The tool shall do the thing."


def test_location_is_file_reference() -> None:
    report = conv.convert(_needs_doc())
    items = {item["tag"]: item for item in report["data"]}
    tool = items["req tool_req__example"]
    assert tool["location"] == {
        "kind": "file",
        "file": "internals/requirements/requirements.rst",
        "line": 42,
        "column": None,
    }


def test_custom_namespace() -> None:
    report = conv.convert(_needs_doc(), namespace="sn")
    tags = {item["tag"] for item in report["data"]}
    assert "sn tool_req__example" in tags
    tool = next(i for i in report["data"] if i["tag"] == "sn tool_req__example")
    assert tool["refs"] == ["sn gd_req__process_one", "sn gd_req__process_two"]


def test_type_filter() -> None:
    report = conv.convert(_needs_doc(), include_types={"tool_req"})
    assert [item["tag"] for item in report["data"]] == ["req tool_req__example"]


def test_up_links_configurable() -> None:
    doc = _needs_doc()
    doc["versions"]["1.0"]["needs"]["tool_req__example"]["implements"] = ["arch__x"]
    report = conv.convert(doc, up_links=("satisfies", "implements"))
    tool = next(i for i in report["data"] if i["tag"] == "req tool_req__example")
    assert "req arch__x" in tool["refs"]


def test_comma_separated_links_are_normalised() -> None:
    doc = _needs_doc()
    doc["versions"]["1.0"]["needs"]["tool_req__example"]["satisfies"] = (
        "gd_req__a, gd_req__b"
    )
    report = conv.convert(doc)
    tool = next(i for i in report["data"] if i["tag"] == "req tool_req__example")
    assert tool["refs"] == ["req gd_req__a", "req gd_req__b"]


def test_missing_optional_fields_are_tolerated() -> None:
    doc = {
        "current_version": "1.0",
        "versions": {"1.0": {"needs": {"n": {"id": "n", "type": "feat_req"}}}},
    }
    report = conv.convert(doc)
    item = report["data"][0]
    assert item["name"] == "n"
    assert item["refs"] == []
    assert item["text"] is None
    assert item["location"]["file"] == "unknown"
    assert item["location"]["line"] is None


def test_select_version_explicit_and_fallback() -> None:
    doc = {
        "versions": {
            "0.9": {"needs": {"a": {"id": "a", "type": "t"}}},
            "1.0": {"needs": {"b": {"id": "b", "type": "t"}}},
        }
    }
    # No current_version -> last key wins.
    report = conv.convert(doc)
    assert report["data"][0]["tag"] == "req b"
    # Explicit version selection.
    report_09 = conv.convert(doc, version="0.9")
    assert report_09["data"][0]["tag"] == "req a"
    with pytest.raises(ValueError):
        conv.convert(doc, version="2.0")


def test_relative_paths_resolve_against_build_working_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workdir = tmp_path / "workdir"
    workdir.mkdir()
    (workdir / "needs.json").write_text(json.dumps(_needs_doc()), encoding="utf-8")

    # Simulate `bazel run`: process cwd differs from the invocation directory.
    elsewhere = tmp_path / "runfiles"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    monkeypatch.setenv("BUILD_WORKING_DIRECTORY", str(workdir))

    rc = conv.main(["--needs-json", "needs.json", "--output", "out.lobster"])
    assert rc == 0
    assert (workdir / "out.lobster").is_file()
    assert not (elsewhere / "out.lobster").exists()


def test_main_writes_output_file(tmp_path: Path) -> None:
    needs_path = tmp_path / "needs.json"
    needs_path.write_text(json.dumps(_needs_doc()), encoding="utf-8")
    out_path = tmp_path / "out.lobster"
    rc = conv.main(
        [
            "--needs-json",
            str(needs_path),
            "--output",
            str(out_path),
            "--types",
            "tool_req",
        ]
    )
    assert rc == 0
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["schema"] == "lobster-req-trace"
    assert [item["tag"] for item in report["data"]] == ["req tool_req__example"]
