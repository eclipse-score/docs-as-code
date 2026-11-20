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
"""Summarize SARIF static-analysis findings per code-file list (proof of concept).

Findings are assigned to components through the same code-file lists that the
LCOV summary uses, and classified into the categories required by
``gd_req__verification_sca_classification`` (critical, high, medium, low).
"""

import json
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from src.docs_cli.lcov_summary import (
    CoverageError,
    FileIdentity,
    file_identity,
    load_code_file_lists,
    write_summary,
)

CLASSES = ("critical", "high", "medium", "low")
TOP_RULES = 10

_LEVELS = {"error": "high", "warning": "medium", "note": "low", "none": "low"}
_MISRA_OBLIGATIONS = {"mandatory": "high", "required": "medium", "advisory": "low"}
# Preliminary mapping for tools such as clang-tidy that report no level at all.
_RULE_FAMILIES = {
    "bugprone": "high",
    "cert": "high",
    "clang-analyzer": "high",
    "concurrency": "high",
    "clang-diagnostic": "medium",
    "cppcoreguidelines": "medium",
    "hicpp": "medium",
    "misc": "medium",
    "performance": "medium",
    "google": "low",
    "modernize": "low",
    "portability": "low",
    "readability": "low",
}


def _security_class(score: float) -> str:
    if score >= 9.0:
        return "critical"
    if score >= 7.0:
        return "high"
    if score >= 4.0:
        return "medium"
    return "low"


def classify(result: dict[str, Any], rule: dict[str, Any]) -> str:
    """Map a SARIF result to critical/high/medium/low, most specific source first."""
    properties = rule.get("properties", {})
    if "security-severity" in properties:
        return _security_class(float(properties["security-severity"]))
    for tag in properties.get("tags", []):
        if tag.startswith("external/misra/obligation/"):
            obligation = tag.rsplit("/", 1)[-1]
            if obligation in _MISRA_OBLIGATIONS:
                return _MISRA_OBLIGATIONS[obligation]
    level = result.get("level") or rule.get("defaultConfiguration", {}).get("level")
    if level in _LEVELS:
        return _LEVELS[level]
    rule_id = str(result.get("ruleId", ""))
    for family in sorted(_RULE_FAMILIES, key=len, reverse=True):
        if rule_id.startswith(family + "-"):
            return _RULE_FAMILIES[family]
    # SARIF's default level is "warning".
    return "medium"


def _rule(run: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    tool = run.get("tool", {})
    reference = result.get("rule", {})
    component = reference.get("toolComponent", {})
    rules = tool.get("driver", {}).get("rules", [])
    if "index" in component:
        rules = tool.get("extensions", [])[component["index"]].get("rules", [])
    index = reference.get("index", result.get("ruleIndex"))
    if isinstance(index, int) and 0 <= index < len(rules):
        return rules[index]
    rule_id = result.get("ruleId", reference.get("id"))
    return next((rule for rule in rules if rule.get("id") == rule_id), {})


def _file(result: dict[str, Any]) -> FileIdentity | None:
    """Return the repository-relative file of the primary location, if any."""
    locations = result.get("locations") or []
    if not locations:
        return None
    uri = (
        locations[0]
        .get("physicalLocation", {})
        .get("artifactLocation", {})
        .get("uri", "")
    )
    uri = unquote(uri.removeprefix("file://"))
    parts = uri.split("/")
    if "external" in parts and (uri.startswith("/") or parts[0] == "execroot"):
        # Analysed from a Bazel workspace: external sources live below the output base.
        uri = "/".join(parts[parts.index("external") :])
    try:
        return file_identity(uri)
    except CoverageError:
        return None


def _suppressed(result: dict[str, Any]) -> bool:
    return any(
        suppression.get("status", "accepted") != "rejected"
        for suppression in result.get("suppressions", [])
    )


def summarize(code_file_lists_path: Path, reports: list[Path]) -> dict[str, Any]:
    code_file_lists = load_code_file_lists(code_file_lists_path)
    owners: dict[FileIdentity, list[str]] = {}
    for code_file_list in code_file_lists:
        for file in code_file_list.files:
            owners.setdefault(file, []).append(code_file_list.primary_need_id)

    findings = {c.primary_need_id: Counter[str]() for c in code_file_lists}
    suppressed = Counter[str]()
    files_with_findings = {
        c.primary_need_id: set[FileIdentity]() for c in code_file_lists
    }
    rules = {
        c.primary_need_id: Counter[tuple[str, str, str]]() for c in code_file_lists
    }
    tools: list[dict[str, Any]] = []
    unassigned = 0

    for report in reports:
        sarif = json.loads(report.read_text(encoding="utf-8"))
        for run in sarif.get("runs", []):
            driver = run.get("tool", {}).get("driver", {})
            tool_name = str(driver.get("name", "unknown"))
            results = run.get("results", [])
            tools.append(
                {
                    "name": tool_name,
                    "version": driver.get("semanticVersion") or driver.get("version"),
                    "results": len(results),
                }
            )
            for result in results:
                file = _file(result)
                need_ids = owners.get(file, []) if file is not None else []
                if not need_ids:
                    unassigned += 1
                    continue
                classification = classify(result, _rule(run, result))
                rule_id = str(result.get("ruleId", "unknown"))
                for need_id in need_ids:
                    if _suppressed(result):
                        suppressed[need_id] += 1
                        continue
                    findings[need_id][classification] += 1
                    files_with_findings[need_id].add(file)
                    rules[need_id][(tool_name, rule_id, classification)] += 1

    summaries = [
        {
            "primary_need_id": c.primary_need_id,
            "files": {
                "total": len(c.files),
                "with_findings": len(files_with_findings[c.primary_need_id]),
            },
            "findings": {cls: findings[c.primary_need_id][cls] for cls in CLASSES},
            "suppressed": suppressed[c.primary_need_id],
            "top_rules": [
                {"tool": tool, "rule": rule, "classification": cls, "count": count}
                for (tool, rule, cls), count in sorted(
                    rules[c.primary_need_id].items(),
                    key=lambda item: (CLASSES.index(item[0][2]), -item[1], item[0]),
                )[:TOP_RULES]
            ],
        }
        for c in sorted(code_file_lists, key=lambda c: c.primary_need_id)
    ]
    return {
        "version": 1,
        "tools": tools,
        "unassigned": unassigned,
        "static_analysis_summaries": summaries,
    }


def generate_summary(code_file_lists: Path, report_dir: Path, output: Path) -> Path:
    """Write the summary for all ``*.sarif`` files below ``report_dir``."""
    reports = sorted(report_dir.glob("*.sarif")) if report_dir.is_dir() else []
    content = (
        json.dumps(summarize(code_file_lists, reports), sort_keys=True, indent=2) + "\n"
    ).encode()
    write_summary(output, content)
    return output
