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
import json
from pathlib import Path
from typing import Any

from src.docs_cli.sarif_summary import generate_summary


def test_findings_are_assigned_and_classified(tmp_path: Path) -> None:
    lists = tmp_path / "lists.json"
    lists.write_text(
        json.dumps(
            {
                "version": 1,
                "code_file_lists": [
                    {
                        "primary_need_id": "comp__a",
                        "files": [
                            {"repository": "_main", "path": "src/a.cc"},
                            {"repository": "_main", "path": "src/b.cc"},
                        ],
                    }
                ],
            }
        )
    )
    reports = tmp_path / "static-analysis-report"
    reports.mkdir()

    def result(path: str, rule: str, **extra: object) -> dict[str, object]:
        location = {"physicalLocation": {"artifactLocation": {"uri": path}}}
        return {"ruleId": rule, "locations": [location], **extra}

    (reports / "lint.sarif").write_text(
        json.dumps(
            {
                "version": "2.1.0",
                "runs": [
                    {
                        "tool": {"driver": {"name": "ClangTidy"}},
                        "results": [
                            result("src/a.cc", "bugprone-branch-clone"),
                            result("src/a.cc", "modernize-use-nodiscard"),
                            result("src/a.cc", "readability-x", suppressions=[{}]),
                            result("other/c.cc", "bugprone-branch-clone"),
                        ],
                    },
                    {
                        "tool": {
                            "driver": {
                                "name": "CodeQL",
                                "semanticVersion": "2.21.4",
                                "rules": [
                                    {
                                        "id": "cpp/misra/x",
                                        "properties": {
                                            "tags": [
                                                "external/misra/obligation/required"
                                            ]
                                        },
                                    }
                                ],
                            }
                        },
                        "results": [result("src/b.cc", "cpp/misra/x", level="error")],
                    },
                ],
            }
        )
    )

    output = generate_summary(lists, reports, tmp_path / "summary.json")

    data = json.loads(output.read_text())
    assert data["unassigned"] == 1
    assert data["tools"][1] == {"name": "CodeQL", "version": "2.21.4", "results": 1}
    (summary,) = data["static_analysis_summaries"]
    assert summary["findings"] == {"critical": 0, "high": 1, "medium": 1, "low": 1}
    assert summary["suppressed"] == 1
    assert summary["files"] == {"total": 2, "with_findings": 2}


def test_indexed_artifacts_rules_and_result_kinds(tmp_path: Path) -> None:
    lists = tmp_path / "lists.json"
    lists.write_text(
        json.dumps(
            {
                "version": 1,
                "code_file_lists": [
                    {
                        "primary_need_id": "comp__a",
                        "files": [{"repository": "_main", "path": "src/a.cc"}],
                    }
                ],
            }
        )
    )
    reports = tmp_path / "static-analysis-report"
    reports.mkdir()
    location = {"physicalLocation": {"artifactLocation": {"index": 0}}}
    second = {
        "physicalLocation": {
            "artifactLocation": {"index": 0},
            "region": {"startLine": 2},
        }
    }
    (reports / "lint.sarif").write_text(
        json.dumps(
            {
                "version": "2.1.0",
                "runs": [
                    {
                        "tool": {
                            "driver": {
                                "name": "ClangTidy",
                                "rules": [{"id": "modernize-use-nodiscard"}],
                            }
                        },
                        "artifacts": [{"location": {"uri": "src/a.cc"}}],
                        "results": [
                            {"ruleIndex": 0, "locations": [location]},
                            {
                                "ruleIndex": 0,
                                "locations": [second],
                                "suppressions": [{"status": "underReview"}],
                            },
                            {"ruleIndex": 0, "kind": "pass", "locations": [location]},
                        ],
                    }
                ],
            }
        )
    )

    output = generate_summary(lists, reports, tmp_path / "summary.json")

    data = json.loads(output.read_text())
    assert data["unassigned"] == 0
    (summary,) = data["static_analysis_summaries"]
    assert summary["findings"] == {"critical": 0, "high": 0, "medium": 0, "low": 2}
    assert summary["suppressed"] == 0
    assert summary["top_rules"] == [
        {
            "tool": "ClangTidy",
            "rule": "modernize-use-nodiscard",
            "classification": "low",
            "count": 2,
        }
    ]


def test_rules_lint_reports(tmp_path: Path) -> None:
    """rules_lint writes one SARIF run per target, without rule ids for clang-tidy and ruff."""
    lists = tmp_path / "lists.json"
    lists.write_text(
        json.dumps(
            {
                "version": 1,
                "code_file_lists": [
                    {
                        "primary_need_id": "comp__a",
                        "files": [
                            {"repository": "_main", "path": "src/a.h"},
                            {"repository": "_main", "path": "tools/x.py"},
                        ],
                    }
                ],
            }
        )
    )
    reports = tmp_path / "static-analysis-report"
    reports.mkdir()

    def finding(path: str, line: int, text: str, level: str) -> dict[str, object]:
        region = {"startLine": line, "startColumn": 1}
        location: dict[str, object] = {
            "physicalLocation": {"artifactLocation": {"uri": path}, "region": region}
        }
        return {"level": level, "message": {"text": text}, "locations": [location]}

    header = finding("src/a.h", 3, "bad [bugprone-macro-parentheses]", "warning")
    style = finding(
        "src/a.h", 4, "x [readability-braces,-warnings-as-errors]", "warning"
    )
    runs: list[dict[str, object]] = [
        {"tool": {"driver": {"name": "ClangTidy"}}, "results": [header, style]},
        {"tool": {"driver": {"name": "ClangTidy"}}, "results": [header]},
        {"tool": {"driver": {"name": "ClangTidy"}}, "results": []},
        {
            "tool": {"driver": {"name": "Ruff"}},
            "results": [
                finding("tools/x.py", 1, "F401 [*] `os` imported but unused", "error"),
                finding("tools/x.py", 9, "E501 Line too long (130 > 120)", "error"),
            ],
        },
    ]
    (reports / "lint.sarif").write_text(json.dumps({"version": "2.1.0", "runs": runs}))

    output = generate_summary(lists, reports, tmp_path / "summary.json")

    data = json.loads(output.read_text())
    assert data["tools"] == [
        {"name": "ClangTidy", "version": None, "results": 2},
        {"name": "Ruff", "version": None, "results": 2},
    ]
    (summary,) = data["static_analysis_summaries"]
    assert summary["findings"] == {"critical": 0, "high": 1, "medium": 1, "low": 2}
    assert {(r["rule"], r["classification"]) for r in summary["top_rules"]} == {
        ("bugprone-macro-parentheses", "high"),
        ("readability-braces", "low"),
        ("F401", "medium"),
        ("E501", "low"),
    }


def _lists(tmp_path: Path, *paths: str) -> Path:
    lists = tmp_path / "lists.json"
    files = [{"repository": "_main", "path": path} for path in paths]
    lists.write_text(
        json.dumps(
            {
                "version": 1,
                "code_file_lists": [{"primary_need_id": "comp__a", "files": files}],
            }
        )
    )
    return lists


def test_uri_base_ids_and_absolute_paths_resolve_to_the_workspace(
    tmp_path: Path,
) -> None:
    lists = _lists(tmp_path, "src/a.cc", "src/b.cc")
    reports = tmp_path / "static-analysis-report"
    reports.mkdir()

    def result(line: int, **location: str) -> dict[str, object]:
        physical: dict[str, Any] = {
            "artifactLocation": location,
            "region": {"startLine": line},
        }
        return {"ruleId": "r", "locations": [{"physicalLocation": physical}]}

    run: dict[str, Any] = {
        "tool": {"driver": {"name": "CodeQL"}},
        "originalUriBaseIds": {
            "%SRCROOT%": {"uri": "file:///work/project/"},
            "SRC": {"uri": "src/", "uriBaseId": "%SRCROOT%"},
        },
        "results": [
            result(1, uri="a.cc", uriBaseId="SRC"),
            result(2, uri="src/b.cc", uriBaseId="%SRCROOT%"),
            result(3, uri="file:///work/project/src/a.cc"),
            result(4, uri="file:///elsewhere/src/a.cc"),
            result(5, uri="src/b.cc", uriBaseId="UNKNOWN"),
        ],
    }
    (reports / "codeql.sarif").write_text(json.dumps({"runs": [run]}))

    output = generate_summary(
        lists, reports, tmp_path / "summary.json", source_root=Path("/work/project")
    )

    data = json.loads(output.read_text())
    assert data["unassigned"] == 1
    (summary,) = data["static_analysis_summaries"]
    assert summary["files"] == {"total": 2, "with_findings": 2}
    assert sum(summary["findings"].values()) == 4


def test_duplicate_stays_open_if_any_copy_is_open(tmp_path: Path) -> None:
    lists = _lists(tmp_path, "src/a.h")
    location = {"physicalLocation": {"artifactLocation": {"uri": "src/a.h"}}}
    open_copy: dict[str, Any] = {"ruleId": "r", "locations": [location]}
    suppressed_copy: dict[str, Any] = {
        **open_copy,
        "suppressions": [{"status": "accepted"}],
    }

    orders: list[list[dict[str, Any]]] = [
        [suppressed_copy, open_copy],
        [open_copy, suppressed_copy],
    ]
    for order in orders:
        reports = tmp_path / f"reports_{len(list(tmp_path.iterdir()))}"
        reports.mkdir()
        runs: list[dict[str, Any]] = [
            {"tool": {"driver": {"name": "ClangTidy"}}, "results": [r]} for r in order
        ]
        (reports / "lint.sarif").write_text(json.dumps({"runs": runs}))

        data = json.loads(
            generate_summary(lists, reports, tmp_path / "summary.json").read_text()
        )
        (summary,) = data["static_analysis_summaries"]
        assert sum(summary["findings"].values()) == 1
        assert summary["suppressed"] == 0

    both_suppressed: dict[str, Any] = {
        "runs": [
            {
                "tool": {"driver": {"name": "ClangTidy"}},
                "results": [suppressed_copy, suppressed_copy],
            }
        ]
    }
    reports = tmp_path / "reports_suppressed"
    reports.mkdir()
    (reports / "lint.sarif").write_text(json.dumps(both_suppressed))
    data = json.loads(
        generate_summary(lists, reports, tmp_path / "summary.json").read_text()
    )
    (summary,) = data["static_analysis_summaries"]
    assert sum(summary["findings"].values()) == 0
    assert summary["suppressed"] == 1
