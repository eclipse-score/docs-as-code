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

"""Compute requirement and test traceability coverage from sphinx-needs output."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def _is_non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return True


def _parse_need_id_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
        return out
    return []


def _safe_percent(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 100.0
    return (numerator / denominator) * 100.0


def _load_needs(needs_json: Path) -> list[dict[str, Any]]:
    raw = json.loads(needs_json.read_text(encoding="utf-8"))

    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]

    if isinstance(raw, dict):
        if "needs" in raw and isinstance(raw["needs"], dict):
            return [v for v in raw["needs"].values() if isinstance(v, dict)]

        versions = raw.get("versions")
        if isinstance(versions, dict) and versions:
            current_version = raw.get("current_version")
            selected: Any = None
            if isinstance(current_version, str) and current_version in versions:
                selected = versions[current_version]
            else:
                selected = next(iter(versions.values()))
            if isinstance(selected, dict):
                needs = selected.get("needs")
                if isinstance(needs, dict):
                    return [v for v in needs.values() if isinstance(v, dict)]

    raise ValueError(f"Unsupported needs.json format in {needs_json}")


def _default_needs_json_candidates() -> list[Path]:
    return [
        Path("_build/needs/needs.json"),
        Path("bazel-bin/needs_json/needs.json"),
    ]


def _find_needs_json(explicit: str | None) -> Path:
    if explicit:
        raw_path = Path(explicit)
        candidates: list[Path] = [raw_path]

        # Under `bazel run` the working directory may be a runfiles tree, so
        # also resolve relative paths from the workspace root when available.
        workspace_dir = os.environ.get("BUILD_WORKSPACE_DIRECTORY", "").strip()
        if not raw_path.is_absolute() and workspace_dir:
            candidates.append(Path(workspace_dir) / raw_path)

        for path in candidates:
            if path.exists():
                return path

        raise FileNotFoundError(f"needs.json not found: {raw_path}")

    for candidate in _default_needs_json_candidates():
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "Could not locate needs.json automatically. Use --needs-json with a valid path."
    )


def _apply_argument_shortcuts(args: argparse.Namespace) -> None:
    """Apply shortcut arguments like --require-all-links."""
    if args.require_all_links:
        args.min_req_code = 100.0
        args.min_req_test = 100.0
        args.min_req_fully_linked = 100.0
        args.min_tests_linked = 100.0
        args.fail_on_broken_test_refs = True


def _filter_requirements(
    all_needs: list[dict[str, Any]],
    requirement_types: set[str],
    include_not_implemented: bool,
) -> list[dict[str, Any]]:
    """Extract and filter requirements from needs."""
    requirements: list[dict[str, Any]] = []
    for need in all_needs:
        need_type = str(need.get("type", "")).strip()
        if need_type not in requirement_types:
            continue
        if not include_not_implemented:
            implemented = str(need.get("implemented", "")).upper().strip()
            if implemented not in {"YES", "PARTIAL"}:
                continue
        requirements.append(need)
    return requirements


def _calculate_requirement_metrics(
    requirements: list[dict[str, Any]],
) -> tuple[int, int, int, int, list[str], list[str], list[str]]:
    """Calculate traceability metrics for requirements."""
    req_total = len(requirements)
    req_with_code = sum(
        1 for need in requirements if _is_non_empty(need.get("source_code_link"))
    )
    req_with_test = sum(
        1 for need in requirements if _is_non_empty(need.get("testlink"))
    )
    req_fully_linked = sum(
        1
        for need in requirements
        if _is_non_empty(need.get("source_code_link"))
        and _is_non_empty(need.get("testlink"))
    )
    req_missing_code = [
        str(need.get("id", ""))
        for need in requirements
        if not _is_non_empty(need.get("source_code_link")) and need.get("id")
    ]
    req_missing_test = [
        str(need.get("id", ""))
        for need in requirements
        if not _is_non_empty(need.get("testlink")) and need.get("id")
    ]
    req_not_fully_linked = [
        str(need.get("id", ""))
        for need in requirements
        if (
            (
                not _is_non_empty(need.get("source_code_link"))
                or not _is_non_empty(need.get("testlink"))
            )
            and need.get("id")
        )
    ]
    return (
        req_total,
        req_with_code,
        req_with_test,
        req_fully_linked,
        req_missing_code,
        req_missing_test,
        req_not_fully_linked,
    )


def _calculate_test_metrics(
    all_needs: list[dict[str, Any]],
    requirement_ids: set[str],
    filtered_test_types: set[str],
) -> tuple[int, int, list[dict[str, str]]]:
    """Calculate test linkage metrics and find broken references."""
    testcases = [
        need for need in all_needs if str(need.get("type", "")).strip() == "testcase"
    ]
    if filtered_test_types:
        testcases = [
            need
            for need in testcases
            if str(need.get("test_type", need.get("TestType", ""))).strip()
            in filtered_test_types
        ]
    tests_total = len(testcases)

    tests_linked = 0
    broken_test_references: list[dict[str, str]] = []
    for test_need in testcases:
        test_id = str(test_need.get("id", "<unknown_testcase>"))
        partially = _parse_need_id_list(
            test_need.get("partially_verifies", test_need.get("PartiallyVerifies"))
        )
        fully = _parse_need_id_list(
            test_need.get("fully_verifies", test_need.get("FullyVerifies"))
        )
        refs = partially + fully
        if refs:
            tests_linked += 1
        for ref in refs:
            if ref not in requirement_ids:
                broken_test_references.append(
                    {"testcase": test_id, "missing_need": ref}
                )
    return tests_total, tests_linked, broken_test_references


def _print_summary(
    needs_json: Path,
    req_total: int,
    req_with_code: int,
    req_code_pct: float,
    req_with_test: int,
    req_test_pct: float,
    req_fully_linked: int,
    req_fully_linked_pct: float,
    req_missing_code: list[str],
    req_missing_test: list[str],
    req_not_fully_linked: list[str],
    print_unlinked: bool,
    tests_total: int,
    tests_linked: int,
    tests_linked_pct: float,
    broken_test_references: list[dict[str, str]],
) -> None:
    """Print human-readable summary."""
    print(f"Traceability input: {needs_json}")
    print("-" * 72)
    print(
        "Requirements with source links: "
        f"{req_with_code}/{req_total} ({req_code_pct:.2f}%)"
    )
    print(
        "Requirements with test links:   "
        f"{req_with_test}/{req_total} ({req_test_pct:.2f}%)"
    )
    print(
        "Requirements fully linked:      "
        f"{req_fully_linked}/{req_total} ({req_fully_linked_pct:.2f}%)"
    )
    if print_unlinked:
        print("Unlinked requirement details:")
        print(
            "  Missing source_code_link: "
            + (", ".join(sorted(req_missing_code)) if req_missing_code else "<none>")
        )
        print(
            "  Missing testlink:         "
            + (", ".join(sorted(req_missing_test)) if req_missing_test else "<none>")
        )
        print(
            "  Not fully linked:         "
            + (
                ", ".join(sorted(req_not_fully_linked))
                if req_not_fully_linked
                else "<none>"
            )
        )
    print(
        "Tests linked to requirements:   "
        f"{tests_linked}/{tests_total} ({tests_linked_pct:.2f}%)"
    )
    print(f"Broken test references:         {len(broken_test_references)}")

    if broken_test_references:
        print("Broken reference details:")
        for item in broken_test_references:
            print(f"  - {item['testcase']} -> {item['missing_need']}")


def _check_thresholds(
    req_code_pct: float,
    min_req_code: float,
    req_test_pct: float,
    min_req_test: float,
    req_fully_linked_pct: float,
    min_req_fully_linked: float,
    tests_linked_pct: float,
    min_tests_linked: float,
    broken_test_references: list[dict[str, str]],
    fail_on_broken_test_refs: bool,
) -> list[str]:
    """Check threshold violations and return failures."""
    failures: list[str] = []
    if req_code_pct < float(min_req_code):
        failures.append(
            f"requirements with code links {req_code_pct:.2f}% < {min_req_code:.2f}%"
        )
    if req_test_pct < float(min_req_test):
        failures.append(
            f"requirements with test links {req_test_pct:.2f}% < {min_req_test:.2f}%"
        )
    if req_fully_linked_pct < float(min_req_fully_linked):
        failures.append(
            "requirements fully linked "
            f"{req_fully_linked_pct:.2f}% < {min_req_fully_linked:.2f}%"
        )
    if tests_linked_pct < float(min_tests_linked):
        failures.append(
            f"tests linked to requirements {tests_linked_pct:.2f}% < {min_tests_linked:.2f}%"
        )
    if fail_on_broken_test_refs and broken_test_references:
        failures.append(
            f"broken testcase references found: {len(broken_test_references)}"
        )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compute requirement/test traceability coverage from sphinx-needs output "
            "and optionally fail on threshold violations."
        )
    )
    parser.add_argument(
        "--needs-json",
        default=None,
        help=(
            "Path to needs.json. If omitted, tries _build/needs/needs.json and "
            "bazel-bin/needs_json/needs.json"
        ),
    )
    parser.add_argument(
        "--requirement-types",
        default="tool_req",
        help="Comma separated need types treated as requirements (default: tool_req)",
    )
    parser.add_argument(
        "--test-types",
        default="",
        help=(
            "Optional comma separated testcase test_type filter (for example unit-test). "
            "If empty, all testcase types are included."
        ),
    )
    parser.add_argument(
        "--include-not-implemented",
        action="store_true",
        help=(
            "Include requirements with implemented == NO in requirement denominator. "
            "By default only YES/PARTIAL are counted."
        ),
    )
    parser.add_argument(
        "--min-req-code",
        type=float,
        default=0.0,
        help="Minimum required percentage for requirements with source code links",
    )
    parser.add_argument(
        "--min-req-test",
        type=float,
        default=0.0,
        help="Minimum required percentage for requirements with test links",
    )
    parser.add_argument(
        "--min-req-fully-linked",
        type=float,
        default=0.0,
        help=(
            "Minimum required percentage for requirements with both source code "
            "and test links"
        ),
    )
    parser.add_argument(
        "--min-tests-linked",
        type=float,
        default=0.0,
        help="Minimum required percentage for testcases linked to requirements",
    )
    parser.add_argument(
        "--require-all-links",
        action="store_true",
        help="Shortcut that enforces 100%% for all three minimum percentages",
    )
    parser.add_argument(
        "--fail-on-broken-test-refs",
        action="store_true",
        help="Fail if a testcase references an unknown requirement ID",
    )
    parser.add_argument(
        "--json-output",
        default=None,
        help="Optional path to write machine-readable JSON summary",
    )
    parser.add_argument(
        "--print-unlinked-requirements",
        action="store_true",
        help=(
            "Print IDs of requirements missing source_code_link and/or testlink. "
            "Useful when coverage thresholds fail."
        ),
    )

    args = parser.parse_args()
    _apply_argument_shortcuts(args)

    requirement_types = {
        item.strip() for item in str(args.requirement_types).split(",") if item.strip()
    }
    if not requirement_types:
        raise ValueError("--requirement-types must not be empty")

    filtered_test_types = {
        item.strip() for item in str(args.test_types).split(",") if item.strip()
    }

    needs_json = _find_needs_json(args.needs_json)
    all_needs = _load_needs(needs_json)

    requirements = _filter_requirements(
        all_needs, requirement_types, args.include_not_implemented
    )

    requirement_ids = {
        str(need.get("id", "")).strip() for need in requirements if need.get("id")
    }

    (
        req_total,
        req_with_code,
        req_with_test,
        req_fully_linked,
        req_missing_code,
        req_missing_test,
        req_not_fully_linked,
    ) = _calculate_requirement_metrics(requirements)

    tests_total, tests_linked, broken_test_references = _calculate_test_metrics(
        all_needs, requirement_ids, filtered_test_types
    )

    req_code_pct = _safe_percent(req_with_code, req_total)
    req_test_pct = _safe_percent(req_with_test, req_total)
    req_fully_linked_pct = _safe_percent(req_fully_linked, req_total)
    tests_linked_pct = _safe_percent(tests_linked, tests_total)

    summary = {
        "needs_json": str(needs_json),
        "requirement_types": sorted(requirement_types),
        "include_not_implemented": bool(args.include_not_implemented),
        "requirements": {
            "total": req_total,
            "with_code_link": req_with_code,
            "with_test_link": req_with_test,
            "fully_linked": req_fully_linked,
            "with_code_link_pct": req_code_pct,
            "with_test_link_pct": req_test_pct,
            "fully_linked_pct": req_fully_linked_pct,
            "missing_code_link_ids": sorted(req_missing_code),
            "missing_test_link_ids": sorted(req_missing_test),
            "not_fully_linked_ids": sorted(req_not_fully_linked),
        },
        "tests": {
            "total": tests_total,
            "filtered_test_types": sorted(filtered_test_types),
            "linked_to_requirements": tests_linked,
            "linked_to_requirements_pct": tests_linked_pct,
            "broken_references": broken_test_references,
        },
        "thresholds": {
            "min_req_code": float(args.min_req_code),
            "min_req_test": float(args.min_req_test),
            "min_req_fully_linked": float(args.min_req_fully_linked),
            "min_tests_linked": float(args.min_tests_linked),
            "fail_on_broken_test_refs": bool(args.fail_on_broken_test_refs),
        },
    }

    _print_summary(
        needs_json,
        req_total,
        req_with_code,
        req_code_pct,
        req_with_test,
        req_test_pct,
        req_fully_linked,
        req_fully_linked_pct,
        req_missing_code,
        req_missing_test,
        req_not_fully_linked,
        args.print_unlinked_requirements,
        tests_total,
        tests_linked,
        tests_linked_pct,
        broken_test_references,
    )

    if args.json_output:
        out_file = Path(args.json_output)
        out_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"JSON summary written to: {out_file}")

    failures = _check_thresholds(
        req_code_pct,
        args.min_req_code,
        req_test_pct,
        args.min_req_test,
        req_fully_linked_pct,
        args.min_req_fully_linked,
        tests_linked_pct,
        args.min_tests_linked,
        broken_test_references,
        args.fail_on_broken_test_refs,
    )

    if failures:
        print("Threshold check failed:")
        for msg in failures:
            print(f"  - {msg}")
        return 2

    print("Threshold check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
