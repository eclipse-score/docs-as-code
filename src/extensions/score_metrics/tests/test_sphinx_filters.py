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

from typing import cast

from sphinx_needs.need_item import NeedItem

from score_metrics.sphinx_filters import (
    generic_pie_items_by_tag,
    generic_pie_linked_items,
)


def test_generic_pie_linked_items_matches_source_by_id_prefix() -> None:
    needs = cast(
        list[NeedItem],
        [
            {"id": "std_req__iso26262__001", "type": "std_req"},
            # Type intentionally does not match selector prefix, id does.
            {
                "id": "gd_guidl__xyz",
                "type": "guideline",
                "complies": ["std_req__iso26262__001"],
            },
        ],
    )

    results: list[int] = []
    generic_pie_linked_items(
        needs,
        results,
        kwargs={"arg1": "std_req__iso26262__", "arg2": "gd_", "arg3": "complies"},
    )

    assert results == [1, 0]


def test_generic_pie_items_by_tag_matches_source_by_id_prefix() -> None:
    needs = cast(
        list[NeedItem],
        [
            {"id": "REQ_A", "type": "tool_req", "tags": ["aspice40_man5"]},
            {"id": "REQ_B", "type": "tool_req", "tags": ["aspice40_man5"]},
            # Type intentionally does not match selector prefix, id does.
            {
                "id": "gd_req__abc",
                "type": "process_requirement",
                "complies": ["REQ_A"],
            },
        ],
    )

    results: list[int] = []
    generic_pie_items_by_tag(
        needs,
        results,
        kwargs={"arg1": "aspice40_man5", "arg2": "gd_", "arg3": "complies"},
    )

    assert results == [1, 1]
