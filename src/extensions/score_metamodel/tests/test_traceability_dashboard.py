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

"""Tests that dashboard filters follow local/external settings."""

from src.extensions.score_metamodel.checks import traceability_dashboard
from src.extensions.score_metamodel.checks.traceability_dashboard import (
    pie_process_requirements_linked,
    pie_requirements_fully_linked,
    pie_requirements_with_test_links,
    pie_requirements_with_code_links,
    set_default_include_external,
)
from src.extensions.score_metamodel.traceability_metrics import (
    compute_traceability_summary,
)


def _needs() -> list[dict[str, object]]:
    return [
        {
            "id": "LOCAL_REQ",
            "type": "tool_req",
            "implemented": "YES",
            "source_code_link": "",
            "testlink": "",
            "is_external": False,
        },
        {
            "id": "LOCAL_SYS_REQ",
            "type": "sys_req",
            "implemented": "YES",
            "source_code_link": "",
            "testlink": "T_LOCAL",
            "is_external": False,
        },
        {
            "id": "EXT_REQ",
            "type": "tool_req",
            "implemented": "YES",
            "source_code_link": "src/ext.py:10",
            "testlink": "T_EXT",
            "is_external": True,
        },
    ]


def test_dashboard_defaults_to_local_only() -> None:
    set_default_include_external(False)

    results: list[int] = []
    pie_requirements_with_code_links(_needs(), results, arg1="tool_req")

    summary = compute_traceability_summary(
        all_needs=_needs(),
        requirement_types={"tool_req"},
        include_not_implemented=True,
        filtered_test_types=set(),
        include_external=False,
    )

    assert results == [1, 0]
    assert results == [
        summary["requirements"]["total"] - summary["requirements"]["with_code_link"],
        summary["requirements"]["with_code_link"],
    ]


def test_dashboard_can_include_external_via_default_flag() -> None:
    set_default_include_external(True)

    results: list[int] = []
    pie_requirements_with_code_links(_needs(), results, arg1="tool_req")

    summary = compute_traceability_summary(
        all_needs=_needs(),
        requirement_types={"tool_req"},
        include_not_implemented=True,
        filtered_test_types=set(),
        include_external=True,
    )

    assert results == [1, 1]
    assert results == [
        summary["requirements"]["total"] - summary["requirements"]["with_code_link"],
        summary["requirements"]["with_code_link"],
    ]


def test_dashboard_filter_arg_can_override_default() -> None:
    set_default_include_external(True)

    results: list[int] = []
    pie_requirements_with_code_links(_needs(), results, arg1="tool_req", arg2="false")

    assert results == [1, 0]


def test_requirements_with_test_links_default_local_only() -> None:
    set_default_include_external(False)

    results: list[int] = []
    pie_requirements_with_test_links(_needs(), results, arg1="tool_req")

    summary = compute_traceability_summary(
        all_needs=_needs(),
        requirement_types={"tool_req"},
        include_not_implemented=True,
        filtered_test_types=set(),
        include_external=False,
    )

    assert results == [1, 0]
    assert results == [
        summary["requirements"]["total"] - summary["requirements"]["with_test_link"],
        summary["requirements"]["with_test_link"],
    ]


def test_requirements_with_test_links_can_override_include_external() -> None:
    set_default_include_external(False)

    results: list[int] = []
    pie_requirements_with_test_links(_needs(), results, arg1="tool_req", arg2="true")

    assert results == [1, 1]


def test_requirements_with_test_links_parses_multiple_types() -> None:
    set_default_include_external(False)

    results: list[int] = []
    pie_requirements_with_test_links(_needs(), results, arg1="tool_req,sys_req")

    assert results == [1, 1]


def test_requirements_fully_linked_uses_shared_summary() -> None:
    set_default_include_external(False)

    results: list[int] = []
    pie_requirements_fully_linked(_needs(), results, arg1="tool_req")

    summary = compute_traceability_summary(
        all_needs=_needs(),
        requirement_types={"tool_req"},
        include_not_implemented=True,
        filtered_test_types=set(),
        include_external=False,
    )

    assert results == [1, 0]
    assert results == [
        summary["requirements"]["total"] - summary["requirements"]["fully_linked"],
        summary["requirements"]["fully_linked"],
    ]


def test_requirements_fully_linked_can_include_external() -> None:
    set_default_include_external(True)

    results: list[int] = []
    pie_requirements_fully_linked(_needs(), results, arg1="tool_req")

    assert results == [1, 1]


def test_process_requirements_linked_uses_stream_a_process_requirement_totals(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    def _fake_summary(
        all_needs,
        requirement_types,
        include_not_implemented,
        filtered_test_types,
        include_external,
    ):
        captured["all_needs"] = all_needs
        captured["requirement_types"] = requirement_types
        captured["include_not_implemented"] = include_not_implemented
        captured["filtered_test_types"] = filtered_test_types
        captured["include_external"] = include_external
        return {
            "requirements": {"total": 99, "linked": 0},
            "process_requirements": {"total": 4, "linked": 3},
        }

    monkeypatch.setattr(traceability_dashboard, "compute_traceability_summary", _fake_summary)

    results: list[int] = []
    pie_process_requirements_linked(_needs(), results, arg1="tool_req,sys_req", arg2="true")

    assert results == [1, 3]
    assert captured["requirement_types"] == {"tool_req", "sys_req"}
    assert captured["include_not_implemented"] is True
    assert captured["filtered_test_types"] == set()
    assert captured["include_external"] is True
