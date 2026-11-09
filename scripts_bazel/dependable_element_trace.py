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
"""Traceability of a dependable element based on Sphinx-Needs inventories.

Replaces the LOBSTER report of ``rules_score``: requirements come from the
``needs.json`` exports of documentation bundles, verification evidence from the
``test.xml`` files of tests executed by the ``component`` rule. The result is a
``needs.json`` with one ``testcase`` Need per executed test case plus a report
of the traceability checks.
"""

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, cast

from src.extensions.score_source_code_linker.testlink import DataOfTestCase
from src.extensions.score_source_code_linker.xml_parser import (
    read_test_xml_file,
    short_hash,
)

# Requirement types a unit test of a component has to verify.
VERIFIED_TYPES = ("comp_req",)
INTEGRITY_ORDER = ("QM", "A", "B", "C", "D")
NEEDS_JSON_VERSION = "1.0"


@dataclass
class Finding:
    severity: str  # "error" | "warning"
    check: str
    message: str


@dataclass
class ComponentResult:
    label: str
    requirements: list[str] = field(default_factory=list)
    testcases: int = 0
    covered: list[str] = field(default_factory=list)
    uncovered: list[str] = field(default_factory=list)


def load_needs(path: Path) -> dict[str, dict[str, Any]]:
    """Return the Needs of the current version of a Sphinx-Needs export."""
    data = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    versions = cast(dict[str, Any], data.get("versions", {}))
    if not versions:
        return {}
    version = data.get("current_version", "")
    selected = versions.get(version) or versions[sorted(versions)[-1]]
    return cast(dict[str, dict[str, Any]], selected.get("needs", {}))


def testcase_id(tc: DataOfTestCase) -> str:
    """Use the ID scheme of the docs-as-code test.xml parser."""
    file = tc.file if tc.file is not None else "<placeholder_file>"
    assert tc.name is not None
    return f"testcase__{tc.name}_{short_hash(file + tc.name)}"


def _split(value: str | None) -> list[str]:
    return [v.strip() for v in (value or "").split(",") if v.strip()]


def testcase_need(tc: DataOfTestCase, component: str) -> dict[str, Any]:
    return {
        "id": testcase_id(tc),
        "type": "testcase",
        "title": tc.name,
        "tags": ["TEST"],
        "name": tc.name,
        "file": tc.file or "",
        "line": tc.line or "",
        "result": tc.result or "",
        "result_text": tc.result_text or "",
        "test_type": tc.TestType or "",
        "derivation_technique": tc.DerivationTechnique or "",
        "partially_verifies": _split(tc.PartiallyVerifies),
        "fully_verifies": _split(tc.FullyVerifies),
        "repo_name": tc.repo_name or "",
        "component": component,
    }


def _integrity_of(safety: str) -> str:
    return "QM" if safety in ("", "QM") else safety.removeprefix("ASIL_")


def _check_testcases(
    label: str,
    testcases: list[DataOfTestCase],
    known_needs: dict[str, dict[str, Any]],
    findings: list[Finding],
) -> set[str]:
    """Check the test cases and return the IDs of the Needs they verify."""
    verified: set[str] = set()
    for tc in testcases:
        refs = _split(tc.PartiallyVerifies) + _split(tc.FullyVerifies)
        if not refs:
            findings.append(
                Finding(
                    "warning",
                    "test_traces_to_requirement",
                    f"{label}: test case {tc.name} verifies no requirement",
                )
            )
        for ref in refs:
            if ref not in known_needs:
                findings.append(
                    Finding(
                        "error",
                        "test_reference_exists",
                        f"{label}: test case {tc.name} references unknown Need {ref}",
                    )
                )
            verified.add(ref)
        if tc.result == "failed":
            findings.append(
                Finding(
                    "error",
                    "test_passed",
                    f"{label}: test case {tc.name} failed: {tc.result_text}",
                )
            )
        elif tc.result in ("skipped", "disabled"):
            findings.append(
                Finding(
                    "warning",
                    "test_passed",
                    f"{label}: test case {tc.name} is {tc.result}",
                )
            )
    return verified


def check_component(
    component: dict[str, Any],
    known_needs: dict[str, dict[str, Any]],
    release: bool,
    findings: list[Finding],
) -> tuple[ComponentResult, list[dict[str, Any]]]:
    label = cast(str, component["label"])
    own_needs: dict[str, dict[str, Any]] = {}
    for path in component["requirements"]:
        own_needs.update(load_needs(Path(path)))
    requirements = sorted(
        need_id
        for need_id, need in own_needs.items()
        if need.get("type") in VERIFIED_TYPES and need.get("status") != "invalid"
    )

    testcases: list[DataOfTestCase] = []
    for report in component["test_reports"]:
        cases, _, _ = read_test_xml_file(Path(report), None)
        testcases.extend(cases)
    verified = _check_testcases(label, testcases, known_needs, findings)
    result = ComponentResult(
        label=label, requirements=requirements, testcases=len(testcases)
    )
    for req in requirements:
        (result.covered if req in verified else result.uncovered).append(req)
    for req in result.uncovered:
        findings.append(
            Finding(
                "error" if release else "warning",
                "requirement_verified",
                f"{label}: {req} is not verified by any test case",
            )
        )
    return result, [testcase_need(tc, label) for tc in testcases]


def check_integrity(
    known_needs: dict[str, dict[str, Any]],
    integrity_level: str,
    findings: list[Finding],
) -> None:
    allowed = INTEGRITY_ORDER.index(integrity_level)
    for need_id, need in sorted(known_needs.items()):
        if need.get("type") not in VERIFIED_TYPES:
            continue
        level = _integrity_of(cast(str, need.get("safety", "")))
        if level in INTEGRITY_ORDER and INTEGRITY_ORDER.index(level) > allowed:
            findings.append(
                Finding(
                    "error",
                    "integrity_level",
                    f"{need_id} requires {need.get('safety')}, the dependable "
                    f"element is only qualified for {integrity_level}",
                )
            )


def run(manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return ``(needs_json, report)`` for a dependable element manifest."""
    findings: list[Finding] = []
    known_needs: dict[str, dict[str, Any]] = {}
    for path in manifest.get("requirements", []):
        known_needs.update(load_needs(Path(path)))
    for component in manifest["components"]:
        for path in component["requirements"]:
            known_needs.update(load_needs(Path(path)))

    check_integrity(known_needs, manifest["integrity_level"], findings)

    components: list[ComponentResult] = []
    needs: dict[str, dict[str, Any]] = {}
    for component in manifest["components"]:
        result, testcase_needs = check_component(
            component, known_needs, manifest["release"], findings
        )
        components.append(result)
        needs.update({n["id"]: n for n in testcase_needs})

    passed = not any(f.severity == "error" for f in findings)
    report: dict[str, Any] = {
        "dependable_element": manifest["label"],
        "integrity_level": manifest["integrity_level"],
        "release": manifest["release"],
        "result": "PASSED" if passed else "FAILED",
        "components": [asdict(c) for c in components],
        "findings": [asdict(f) for f in findings],
    }
    needs_json: dict[str, Any] = {
        "current_version": NEEDS_JSON_VERSION,
        "project": manifest["label"],
        "versions": {NEEDS_JSON_VERSION: {"needs": needs, "needs_amount": len(needs)}},
    }
    return needs_json, report


def summary(report: dict[str, Any]) -> str:
    lines = [
        f"Dependable element {report['dependable_element']} "
        f"(integrity level {report['integrity_level']}, "
        f"{'release' if report['release'] else 'development'} mode)",
    ]
    for c in report["components"]:
        lines.append(
            f"  {c['label']}: {len(c['covered'])}/{len(c['requirements'])} "
            f"requirements verified by {c['testcases']} test cases"
        )
    for f in report["findings"]:
        lines.append(f"  {f['severity'].upper()} [{f['check']}] {f['message']}")
    lines.append(f"RESULT: {report['result']}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--needs-out", type=Path, required=True)
    parser.add_argument("--report-out", type=Path, required=True)
    parser.add_argument("--summary-out", type=Path, required=True)
    args = parser.parse_args(argv)

    manifest = cast(dict[str, Any], json.loads(args.manifest.read_text()))
    needs_json, report = run(manifest)
    args.needs_out.write_text(json.dumps(needs_json, indent=2, sort_keys=True))
    args.report_out.write_text(json.dumps(report, indent=2))
    args.summary_out.write_text(summary(report))
    # Findings are reported by the dependable element test, not by the build.
    return 0


if __name__ == "__main__":
    sys.exit(main())
