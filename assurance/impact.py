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
"""Classify changes using the old and new argument graphs, retaining rule causes."""

from collections import deque
from typing import Any

RELATIONS = (
    "complies",
    "tests",
    "testlink",
    "implements",
    "source_code_link",
    "links",
    "fully_verifies",
    "partially_verifies",
)


def needs_map(snapshot: dict[str, Any]) -> dict[str, Any]:
    if "versions" in snapshot:
        version = snapshot["versions"][snapshot["current_version"]]
        return version["needs"]
    return snapshot.get("needs", snapshot)


def references(need: dict[str, Any], relation: str) -> list[str]:
    value = need.get(relation, [])
    return [value] if isinstance(value, str) and value else list(value or [])


Impact = tuple[str, str, str, str]


def reverse_graph(old: dict[str, Any], new: dict[str, Any]) -> dict[str, set[str]]:
    reverse: dict[str, set[str]] = {}
    for snapshot in (old, new):
        for identifier, need in snapshot.items():
            for relation in RELATIONS:
                for target in references(need, relation):
                    reverse.setdefault(target, set()).add(identifier)
    return reverse


def dependent_impacts(
    identifier: str,
    old_need: dict[str, Any],
    new_need: dict[str, Any],
    dependent: str,
    need: dict[str, Any],
    removed: bool,
) -> list[Impact]:
    old_type, new_type = old_need.get("type"), new_need.get("type")
    complies = identifier in references(need, "complies")
    impacts: list[Impact] = []
    if removed and complies:
        impacts.append((dependent, "direct_recheck", "CR-001", identifier))
    if (
        old_type != new_type
        and old_type in ("tool_req", "std_req", "process_requirement")
        and need.get("type") in ("gd_guidl", "gd_req", "guideline")
        and complies
    ):
        impacts.append((dependent, "indirect_propagation", "CR-002", identifier))
    if (
        old_type == "std_req"
        and old_need.get("content") != new_need.get("content")
        and complies
        and need.get("type") in ("gd_guidl", "gd_req", "guideline")
    ):
        impacts.append((dependent, "revision_required", "CR-004", identifier))
    if (
        old_type in ("testcase", "test_link")
        and removed
        and identifier in references(need, "tests") + references(need, "testlink")
    ):
        impacts.append((dependent, "revision_required", "CR-003", identifier))
    return impacts


def propagate(impacts: set[Impact], reverse: dict[str, set[str]]) -> None:
    seeds = {(identifier, rule, cause) for identifier, _, rule, cause in impacts}
    queue = deque(sorted(seeds))
    visited = set(seeds)
    while queue:
        identifier, rule, cause = queue.popleft()
        for dependent in sorted(reverse.get(identifier, set())):
            item = (dependent, rule, cause)
            if item not in visited:
                visited.add(item)
                impacts.add((dependent, "indirect_propagation", rule, cause))
                queue.append(item)


def classify(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, str]]:
    old, new = needs_map(before), needs_map(after)
    changed = {key for key in old.keys() | new.keys() if old.get(key) != new.get(key)}
    reverse = reverse_graph(old, new)
    impacts: set[Impact] = set()
    for identifier in sorted(changed):
        old_need, new_need = old.get(identifier, {}), new.get(identifier, {})
        for dependent in sorted(reverse.get(identifier, set())):
            previous, current = old.get(dependent, {}), new.get(dependent, {})
            need = {**previous, **current}
            for relation in ("complies", "tests", "testlink"):
                need[relation] = sorted(
                    set(references(previous, relation) + references(current, relation))
                )
            impacts.update(
                dependent_impacts(
                    identifier,
                    old_need,
                    new_need,
                    dependent,
                    need,
                    identifier not in new,
                )
            )
        for target in references(new_need, "tests") + references(new_need, "testlink"):
            if target not in new:
                impacts.add((identifier, "revision_required", "CR-003", target))
        if identifier in new and old_need != new_need:
            impacts.add((identifier, "direct_recheck", "CHANGE", identifier))
    propagate(impacts, reverse)
    return [
        {
            "need_id": identifier,
            "impact_class": impact,
            "rule_id": rule,
            "changed_artifact": cause,
        }
        for identifier, impact, rule, cause in sorted(impacts)
    ]
