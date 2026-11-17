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

"""Shared verification metrics helpers for use in both metrics calculation and filtering.

These helpers are used by:
- traceability_metrics.py for pre-calculating verification_metrics in metrics.json
- sphinx_filters.py for on-the-fly filtering in needpie directives
"""

from typing import Any

from sphinx_needs.need_item import NeedItem


def is_need_in_component(need: NeedItem, component_id: str, category: str) -> bool:
    """Check if a need belongs to a component for a given category.

    Args:
        need: The need item to check.
        component_id: The component ID (e.g., "comp__my_component").
        category: Either "requirements" or "architecture".

    Returns:
        True if the need belongs to the component for that category.
    """
    need_type = str(need.get("type", ""))

    if category == "requirements":
        if need_type != "comp_req":
            return False
        sat_by = need.get("satisfied_by", [])
        if isinstance(sat_by, str):
            sat_by = [sat_by]
        return component_id in sat_by

    # architecture
    if need_type not in ("comp_arc_sta", "comp_arc_dyn"):
        return False
    bel_to = need.get("belongs_to", [])
    if isinstance(bel_to, str):
        bel_to = [bel_to]
    return component_id in bel_to


def _in_scope(
    need: NeedItem,
    component_id: str,
    category: str,
    version: str | None,
    version_filter_func: Any,
    safety: str | None,
) -> bool:
    """Whether a need is counted for this component, category, version and safety."""
    if not is_need_in_component(need, component_id, category):
        return False
    if safety and need.get("safety") != safety:
        return False
    # Architecture elements have neither valid_from nor derived_from, so the
    # version scope applies to requirements only.
    return not (
        category == "requirements"
        and version
        and not version_filter_func(need, version)
    )


def count_status_filtered(
    needs: list[Any],
    component_id: str,
    category: str,
    version: str | None,
    version_filter_func: Any,
    safety: str | None = None,
) -> dict[str, int]:
    """Count status distribution with version filtering.

    Args:
        needs: List of need items.
        component_id: The component ID.
        category: Either "requirements" or "architecture".
        version: Version string for filtering (only applied to requirements).
        version_filter_func: Callable like req_in_report_version(need, version).
        safety: Optional safety class (e.g. "ASIL_B", "QM") to restrict to.

    Returns:
        Dict with status counts: {valid: int, valid_inspected: int, invalid: int}
    """
    status = {"valid": 0, "valid_inspected": 0, "invalid": 0}

    for need in needs:
        if not _in_scope(
            need, component_id, category, version, version_filter_func, safety
        ):
            continue

        need_status = str(need.get("status", ""))
        if need_status in status:
            status[need_status] += 1

    return status


def count_coverage_filtered(
    needs: list[Any],
    component_id: str,
    category: str,
    version: str | None,
    version_filter_func: Any,
    safety: str | None = None,
) -> dict[str, int]:
    """Count verification coverage with version filtering.

    Uses the verification coverage axis (fully_verifies_back / partially_verifies_back),
    not the link coverage axis (testlink / source_code_link).

    Args:
        needs: List of need items.
        component_id: The component ID.
        category: Either "requirements" or "architecture".
        version: Version string for filtering (only applied to requirements).
        version_filter_func: Callable like req_in_report_version(need, version).
        safety: Optional safety class (e.g. "ASIL_B", "QM") to restrict to.

    Returns:
        Dict with coverage counts: {fully_covered: int, partially_covered: int, not_covered: int}
    """
    coverage = {"fully_covered": 0, "partially_covered": 0, "not_covered": 0}

    for need in needs:
        if not _in_scope(
            need, component_id, category, version, version_filter_func, safety
        ):
            continue

        # Use verification coverage axis (not link coverage axis)
        has_fully = bool(need.get("fully_verifies_back"))
        has_partially = bool(need.get("partially_verifies_back"))

        if has_fully:
            coverage["fully_covered"] += 1
        elif has_partially:
            coverage["partially_covered"] += 1
        else:
            coverage["not_covered"] += 1

    return coverage
