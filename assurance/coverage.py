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

# Portions generated with OpenAI Codex; see the retained verification records.
"""Validate native schema-v2 metrics exported by Sphinx or public gate fixtures.

Consume schema-v2 exports or extract snapshot metrics using the native metric
functions and metamodel. Deployment-specific type/external scope is explicit.
"""

import argparse
import json
from pathlib import Path
from typing import Any, cast

from jsonschema_rs import Draft202012Validator
from score_metamodel.yaml_parser import load_metamodel_data
from score_metrics.traceability_metrics import (
    calculate_requirement_metrics,
    calculate_test_metrics,
    get_need_types_by_tags,
    safe_percent,
)
from sphinx_needs.data import NeedsView
from sphinx_needs.need_item import NeedItem

from assurance.impact import needs_map

SCHEMA = (
    Path(__file__).resolve().parents[1]
    / "scripts_bazel/traceability_metrics_schema.json"
)


def validate(metrics: dict[str, Any]) -> None:
    Draft202012Validator(json.loads(SCHEMA.read_text())).validate(metrics)
    for values in [metrics["overall_metrics"], *metrics["metrics_by_type"].values()]:
        total = values["total"]
        for count, percentage in (
            ("with_code_link", "with_code_link_pct"),
            ("with_test_link", "with_test_link_pct"),
            ("fully_linked", "fully_linked_pct"),
        ):
            if values[count] > total:
                raise ValueError(f"{count} exceeds total")
            expected = values[count] * 100.0 / total if total else 100.0
            if abs(expected - values[percentage]) > 0.011:
                raise ValueError(f"Inconsistent {count} count and percentage")
        if values["fully_linked"] > min(
            values["with_code_link"], values["with_test_link"]
        ):
            raise ValueError("Fully linked count exceeds either link count")
    tests = metrics["tests"]
    if tests["linked_to_requirements"] > tests["total"]:
        raise ValueError("Linked test count exceeds total")
    expected = (
        tests["linked_to_requirements"] * 100.0 / tests["total"]
        if tests["total"]
        else 100.0
    )
    if abs(expected - tests["linked_to_requirements_pct"]) > 0.011:
        raise ValueError("Inconsistent test linkage count and percentage")


def extract(
    snapshot: dict[str, Any],
    need_types: list[str] | None = None,
    include_external: bool = False,
) -> dict[str, Any]:
    """Apply the native metric functions to an exported needs snapshot.

    Requirements follow the native metamodel's requirement tags and external
    filtering. Test metrics include all testcase needs, matching the extension.
    The native test function only uses membership of its all_needs parameter.
    """
    needs = needs_map(snapshot)
    selected = (
        need_types
        if need_types is not None
        else get_need_types_by_tags(load_metamodel_data().needs_types, {"requirement"})
    )
    by_type: dict[str, Any] = {}
    for kind in sorted(set(selected)):
        requirements = [
            cast(NeedItem, need)
            for need in needs.values()
            if need.get("type") == kind
            and (include_external or not need.get("is_external", False))
        ]
        if requirements:
            by_type[kind] = calculate_requirement_metrics(requirements)
    if not by_type:
        raise ValueError("Snapshot has no requirements in the selected native scope")
    overall: dict[str, Any] = {
        name: sum(values[name] for values in by_type.values())
        for name in ("total", "with_code_link", "with_test_link", "fully_linked")
    }
    for field in ("with_code_link", "with_test_link", "fully_linked"):
        overall[field + "_pct"] = safe_percent(overall[field], overall["total"])
    tests = [
        cast(NeedItem, need)
        for need in needs.values()
        if need.get("type") == "testcase"
    ]
    test_metrics = calculate_test_metrics(tests, cast(NeedsView, needs))
    test_metrics["broken_references"] = sorted(
        cast(list[dict[str, str]], test_metrics["broken_references"]),
        key=lambda item: (item["testcase"], item["missing_need"]),
    )
    metrics: dict[str, Any] = {
        "schema_version": "2",
        "generated_by": "native_snapshot_metrics",
        "overall_metrics": overall,
        "metrics_by_type": by_type,
        "tests": test_metrics,
    }
    validate(metrics)
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--metrics-json")
    source.add_argument("--needs-json")
    parser.add_argument("--need-type", action="append")
    parser.add_argument("--include-external", action="store_true")
    parser.add_argument("--json-output", required=True)
    args = parser.parse_args()
    if args.needs_json:
        metrics = extract(
            json.loads(Path(args.needs_json).read_text()),
            args.need_type,
            args.include_external,
        )
    else:
        metrics = json.loads(Path(args.metrics_json).read_text())
        validate(metrics)
    Path(args.json_output).write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
