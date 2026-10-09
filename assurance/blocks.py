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
"""Reusable, deterministic argument-and-check fragments for Lane A."""

from typing import Any

from assurance.impact import needs_map, references


def check_blocks(
    after: dict[str, Any], metrics: dict[str, Any], instances: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    needs = needs_map(after)
    results: list[dict[str, Any]] = []
    for block in instances:
        identifier = block["element"]
        need = needs.get(identifier, {})
        relation = block["relation"]
        targets = references(need, relation)
        failures = [
            f"missing reference: {target}" for target in targets if target not in needs
        ]
        if not need or not targets:
            failures.append("element or supporting references absent")
        failures.extend(
            f"invalid supporting status: {target}"
            for target in targets
            if needs.get(target, {}).get("status") in ("failed", "rejected", "invalid")
        )
        if block["pattern"] == "requirements_breakdown":
            scope = metrics["metrics_by_type"].get(block["need_type"])
            if scope is None or scope["fully_linked_pct"] < block["minimum_coverage"]:
                failures.append("requirement breakdown coverage below threshold")
        results.append(
            {
                "element": identifier,
                "pattern": block["pattern"],
                "status": "fail" if failures else "pass",
                "failures": sorted(failures),
            }
        )
    return results
