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


def test_absolute_output_base_paths_map_to_external_repositories(
    tmp_path: Path,
) -> None:
    lists = tmp_path / "lists.json"
    lists.write_text(
        json.dumps(
            {
                "version": 1,
                "code_file_lists": [
                    {
                        "primary_need_id": "comp__x",
                        "files": [{"repository": "score_x+", "path": "src/x.cc"}],
                    }
                ],
            }
        )
    )
    reports = tmp_path / "static-analysis-report"
    reports.mkdir()
    uri = (
        "file:///home/runner/.cache/bazel/_bazel_runner/abc/external/score_x+/src/x.cc"
    )
    location = {"physicalLocation": {"artifactLocation": {"uri": uri}}}
    (reports / "a.sarif").write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "tool": {"driver": {"name": "CodeQL"}},
                        "results": [
                            {"ruleId": "r", "level": "error", "locations": [location]}
                        ],
                    }
                ]
            }
        )
    )

    data = json.loads(generate_summary(lists, reports, tmp_path / "s.json").read_text())

    assert data["unassigned"] == 0
    assert data["static_analysis_summaries"][0]["findings"]["high"] == 1
