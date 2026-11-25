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
import re
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urljoin, urlparse

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
# Preliminary mappings; rules_lint reports every clang-tidy check as warning and every
# ruff rule as error, so the level alone says nothing for these tools.
_CLANG_TIDY_FAMILIES = {
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
_RUFF_PREFIXES = {
    "S": "high",
    "B": "high",
    "F": "medium",
    "PL": "medium",
    "E": "low",
    "W": "low",
    "I": "low",
    "N": "low",
    "D": "low",
    "UP": "low",
    "SIM": "low",
    "RUF": "low",
}
# rules_lint's SARIF has no ruleId for these tools, only the linter's message line.
_CLANG_TIDY_CHECK = re.compile(r"\[([\w.-]+)(?:,[\w.,-]*)?\]\s*$")
_RUFF_CODE = re.compile(r"^([A-Z]+\d+)\b")


def _security_class(score: float) -> str:
    if score >= 9.0:
        return "critical"
    if score >= 7.0:
        return "high"
    if score >= 4.0:
        return "medium"
    return "low"


def _tool_kind(tool_name: str) -> str:
    """Normalize tool names: rules_lint's "ClangTidy" is "clang-tidy" elsewhere."""
    return re.sub(r"[^a-z]", "", tool_name.lower())


def _longest_prefix(value: str, mapping: dict[str, str], separator: str) -> str | None:
    for prefix in sorted(mapping, key=len, reverse=True):
        if value.startswith(prefix + separator):
            return mapping[prefix]
    return None


def classify(result: dict[str, Any], rule: dict[str, Any], tool_name: str = "") -> str:
    """Map a SARIF result to critical/high/medium/low, most specific source first."""
    properties = rule.get("properties", {})
    if "security-severity" in properties:
        return _security_class(float(properties["security-severity"]))
    for tag in properties.get("tags", []):
        if tag.startswith("external/misra/obligation/"):
            obligation = tag.rsplit("/", 1)[-1]
            if obligation in _MISRA_OBLIGATIONS:
                return _MISRA_OBLIGATIONS[obligation]
    kind = _tool_kind(tool_name)
    rule_id = _rule_id(result, rule, tool_name)
    if kind == "clangtidy":
        family = _longest_prefix(rule_id, _CLANG_TIDY_FAMILIES, "-")
        if family:
            return family
    elif kind == "ruff":
        letters = re.match(r"[A-Z]*", rule_id)
        return (
            _longest_prefix(letters.group() if letters else "", _RUFF_PREFIXES, "")
            or "medium"
        )
    level = result.get("level") or rule.get("defaultConfiguration", {}).get("level")
    if level in _LEVELS:
        return _LEVELS[level]
    # SARIF's default level is "warning".
    return "medium"


def _rule(run: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    tool = run.get("tool", {})
    reference = result.get("rule", {})
    component = reference.get("toolComponent", {})
    rules: list[dict[str, Any]] = tool.get("driver", {}).get("rules", [])
    if "index" in component:
        rules = tool.get("extensions", [])[component["index"]].get("rules", [])
    index = reference.get("index", result.get("ruleIndex"))
    if isinstance(index, int) and 0 <= index < len(rules):
        return rules[index]
    rule_id = result.get("ruleId", reference.get("id"))
    return next((rule for rule in rules if rule.get("id") == rule_id), {})


def _rule_id(result: dict[str, Any], rule: dict[str, Any], tool_name: str = "") -> str:
    explicit = (
        result.get("ruleId") or result.get("rule", {}).get("id") or rule.get("id")
    )
    if explicit:
        return str(explicit)
    text = str(result.get("message", {}).get("text", ""))
    pattern = {"clangtidy": _CLANG_TIDY_CHECK, "ruff": _RUFF_CODE}.get(
        _tool_kind(tool_name)
    )
    match = pattern.search(text) if pattern else None
    return match.group(1) if match else "unknown"


def _resolve_uri(
    uri: str, base_id: str | None, bases: dict[str, Any], depth: int = 0
) -> str:
    """Apply the `uriBaseId` chain of `run.originalUriBaseIds`; unknown bases keep the URI."""
    if not base_id or base_id not in bases or depth > len(bases):
        return uri
    base: dict[str, Any] = bases[base_id]
    prefix = _resolve_uri(
        str(base.get("uri", "")), base.get("uriBaseId"), bases, depth + 1
    )
    if not prefix:
        return uri
    return urljoin(prefix if prefix.endswith("/") else prefix + "/", uri)


def _source_path(uri: str, source_root: Path | None) -> str:
    """File path of a URI, relative to `source_root` when it lies below it."""
    path = unquote(urlparse(uri).path if uri.startswith("file:") else uri)
    if source_root is not None and Path(path).is_absolute():
        try:
            return Path(path).relative_to(source_root).as_posix()
        except ValueError:
            return path
    return path


def _location(
    run: dict[str, Any], result: dict[str, Any], source_root: Path | None = None
) -> tuple[str, int | None, int | None]:
    """Return the file path, start line and start column of the primary location."""
    locations: list[dict[str, Any]] = result.get("locations") or []
    if not locations:
        return "", None, None
    physical: dict[str, Any] = locations[0].get("physicalLocation", {})
    artifact: dict[str, Any] = physical.get("artifactLocation", {})
    artifacts: list[dict[str, Any]] = run.get("artifacts", [])
    index = artifact.get("index")
    if "uri" not in artifact and isinstance(index, int) and 0 <= index < len(artifacts):
        artifact = artifacts[index].get("location", {})
    uri = _resolve_uri(
        str(artifact.get("uri", "")),
        artifact.get("uriBaseId"),
        run.get("originalUriBaseIds", {}),
    )
    region: dict[str, Any] = physical.get("region", {})
    return (
        _source_path(uri, source_root) if uri else "",
        region.get("startLine"),
        region.get("startColumn"),
    )


def _file(path: str) -> FileIdentity | None:
    """Return the repository-relative file of a location path, if any."""
    if not path:
        return None
    try:
        return file_identity(path)
    except CoverageError:
        return None


def _suppressed(result: dict[str, Any]) -> bool:
    # Pending (underReview) and rejected suppressions keep the finding open.
    return any(
        suppression.get("status", "accepted") == "accepted"
        for suppression in result.get("suppressions", [])
    )


def _unique_results(
    reports: list[Path],
    tools: Counter[tuple[str, str | None]],
    source_root: Path | None = None,
) -> Iterator[tuple[str, dict[str, Any], dict[str, Any], str, str, bool]]:
    """Yield (tool, result, rule, rule id, path, suppressed) once per distinct finding."""
    findings: dict[tuple[object, ...], list[Any]] = {}
    for report in reports:
        sarif = json.loads(report.read_text(encoding="utf-8"))
        for run in sarif.get("runs", []):
            driver = run.get("tool", {}).get("driver", {})
            tool_name = str(driver.get("name", "unknown"))
            tool = (tool_name, driver.get("semanticVersion") or driver.get("version"))
            tools.setdefault(tool, 0)
            for result in run.get("results", []):
                # Successful or inapplicable checks are not findings.
                if result.get("kind", "fail") in ("pass", "notApplicable"):
                    continue
                rule = _rule(run, result)
                rule_id = _rule_id(result, rule, tool_name)
                path, line, column = _location(run, result, source_root)
                message = result.get("message", {}).get("text")
                key = (tool_name, rule_id, path, line, column, message)
                # Linters run per target, e.g. report a header once per including target;
                # such a finding stays open if any of its copies is open.
                if key in findings:
                    findings[key][5] = findings[key][5] and _suppressed(result)
                    continue
                tools[tool] += 1
                findings[key] = [
                    tool_name,
                    result,
                    rule,
                    rule_id,
                    path,
                    _suppressed(result),
                ]
    for tool_name, result, rule, rule_id, path, suppressed in findings.values():
        yield tool_name, result, rule, rule_id, path, suppressed


def summarize(
    code_file_lists_path: Path, reports: list[Path], source_root: Path | None = None
) -> dict[str, Any]:
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
    tools = Counter[tuple[str, str | None]]()
    unassigned = 0

    for tool_name, result, rule, rule_id, path, is_suppressed in _unique_results(
        reports, tools, source_root
    ):
        file = _file(path)
        if file is None or not owners.get(file):
            unassigned += 1
            continue
        classification = classify(result, rule, tool_name)
        for need_id in owners[file]:
            if is_suppressed:
                suppressed[need_id] += 1
                continue
            findings[need_id][classification] += 1
            files_with_findings[need_id].add(file)
            rules[need_id][(tool_name, rule_id, classification)] += 1

    summaries: list[dict[str, Any]] = [
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
        "tools": [
            {"name": name, "version": version, "results": count}
            for (name, version), count in sorted(
                tools.items(), key=lambda item: (item[0][0], str(item[0][1]))
            )
        ],
        "unassigned": unassigned,
        "static_analysis_summaries": summaries,
    }


def generate_summary(
    code_file_lists: Path,
    report_dir: Path,
    output: Path,
    source_root: Path | None = None,
) -> Path:
    """Write the summary for all ``*.sarif`` files below ``report_dir``.

    Absolute file locations below ``source_root`` count as workspace-relative.
    """
    reports = sorted(report_dir.glob("*.sarif")) if report_dir.is_dir() else []
    summary = summarize(code_file_lists, reports, source_root)
    content = (json.dumps(summary, sort_keys=True, indent=2) + "\n").encode()
    write_summary(output, content)
    return output
