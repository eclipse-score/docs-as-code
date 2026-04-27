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

"""Unit tests for traceability_metrics include_external handling."""

from src.extensions.score_metamodel.traceability_metrics import (
    compute_traceability_summary,
    filter_requirements,
)


def _needs() -> list[dict[str, object]]:
    return [
        {
            "id": "LOCAL_REQ",
            "type": "tool_req",
            "implemented": "YES",
            "source_code_link": "src/local.py:1",
            "testlink": "tests/test_local.py::test_ok",
            "is_external": False,
        },
        {
            "id": "EXT_REQ",
            "type": "tool_req",
            "implemented": "YES",
            "source_code_link": "src/external.py:9",
            "testlink": "tests/test_external.py::test_ok",
            "is_external": True,
        },
        {
            "id": "TC_1",
            "type": "testcase",
            "partially_verifies": "LOCAL_REQ",
            "fully_verifies": "",
            "is_external": False,
        },
    ]


def test_filter_requirements_defaults_to_local_only() -> None:
    filtered = filter_requirements(
        _needs(),
        requirement_types={"tool_req"},
        include_not_implemented=True,
    )

    assert [need["id"] for need in filtered] == ["LOCAL_REQ"]


def test_filter_requirements_can_include_external_needs() -> None:
    filtered = filter_requirements(
        _needs(),
        requirement_types={"tool_req"},
        include_not_implemented=True,
        include_external=True,
    )

    assert sorted(need["id"] for need in filtered) == ["EXT_REQ", "LOCAL_REQ"]


def test_compute_traceability_summary_propagates_include_external() -> None:
    summary_local = compute_traceability_summary(
        all_needs=_needs(),
        requirement_types={"tool_req"},
        include_not_implemented=True,
        filtered_test_types=set(),
        include_external=False,
    )
    summary_all = compute_traceability_summary(
        all_needs=_needs(),
        requirement_types={"tool_req"},
        include_not_implemented=True,
        filtered_test_types=set(),
        include_external=True,
    )

    assert summary_local["include_external"] is False
    assert summary_local["requirements"]["total"] == 1
    assert summary_all["include_external"] is True
    assert summary_all["requirements"]["total"] == 2


def test_compute_traceability_summary_process_requirements_summary() -> None:
    summary = compute_traceability_summary(
        all_needs=[
            {
                "id": "TOOL_REQ_1",
                "type": "tool_req",
                "implemented": "YES",
                "source_code_link": "src/req.py:10",
                "testlink": "tests/test_req.py::test_ok",
                "satisfies": "PR_LOCAL_1,OTHER_REQ",
                "is_external": False,
            },
            {
                "id": "TOOL_REQ_2",
                "type": "tool_req",
                "implemented": "YES",
                "source_code_link": "src/req.py:20",
                "testlink": "tests/test_req.py::test_ok_2",
                "satisfies": ["PR_LOCAL_1", "PR_LOCAL_2"],
                "is_external": False,
            },
            {
                "id": "PR_LOCAL_1",
                "type": "process_req",
                "is_external": False,
            },
            {
                "id": "PR_LOCAL_2",
                "type": "gd_req",
                "is_external": False,
            },
            {
                "id": "PR_LOCAL_3",
                "type": "gd_req",
                "is_external": False,
            },
        ],
        requirement_types={"tool_req"},
        include_not_implemented=True,
        filtered_test_types=set(),
        include_external=False,
    )

    process_requirements = summary["process_requirements"]

    assert process_requirements["total"] == 3
    assert process_requirements["linked_by_tool_requirements"] == 2
    assert process_requirements["linked_by_tool_requirements_pct"] == (2 / 3) * 100
    assert process_requirements["unlinked_ids"] == ["PR_LOCAL_3"]


def test_compute_traceability_summary_process_requirements_respects_include_external() -> None:
    all_needs = [
        {
            "id": "TOOL_REQ_LOCAL",
            "type": "tool_req",
            "implemented": "YES",
            "source_code_link": "src/local.py:1",
            "testlink": "tests/test_local.py::test_ok",
            "satisfies": "PR_LOCAL",
            "is_external": False,
        },
        {
            "id": "TOOL_REQ_EXTERNAL",
            "type": "tool_req",
            "implemented": "YES",
            "source_code_link": "src/external.py:1",
            "testlink": "tests/test_external.py::test_ok",
            "satisfies": "PR_EXTERNAL",
            "is_external": True,
        },
        {
            "id": "PR_LOCAL",
            "type": "gd_req",
            "is_external": False,
        },
        {
            "id": "PR_EXTERNAL",
            "type": "gd_req",
            "is_external": True,
        },
    ]

    summary_local = compute_traceability_summary(
        all_needs=all_needs,
        requirement_types={"tool_req"},
        include_not_implemented=True,
        filtered_test_types=set(),
        include_external=False,
    )
    summary_all = compute_traceability_summary(
        all_needs=all_needs,
        requirement_types={"tool_req"},
        include_not_implemented=True,
        filtered_test_types=set(),
        include_external=True,
    )

    assert summary_local["process_requirements"] == {
        "total": 1,
        "linked": 1,
        "linked_by_tool_requirements": 1,
        "linked_by_tool_requirements_pct": 100.0,
        "unlinked_ids": [],
    }
    assert summary_all["process_requirements"] == {
        "total": 2,
        "linked": 2,
        "linked_by_tool_requirements": 2,
        "linked_by_tool_requirements_pct": 100.0,
        "unlinked_ids": [],
    }
