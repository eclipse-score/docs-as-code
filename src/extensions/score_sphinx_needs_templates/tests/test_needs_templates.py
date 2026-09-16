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
"""Tests for graph traversal helpers used by Sphinx-Needs templates."""

from collections.abc import Iterable

import pytest
import score_sphinx_needs_templates as templates


class FakeLink:
    """Small test double for the Sphinx-Needs link objects."""

    def __init__(self, target: str):
        self.target = target

    def to_link_string(self) -> str:
        return self.target


class FakeNeed(dict[str, str]):
    """Need-shaped test double with independently controlled link indexes."""

    def __init__(
        self,
        need_id: str,
        *,
        backlinks: Iterable[FakeLink] = (),
        links: Iterable[FakeLink] = (),
    ):
        super().__init__(id=need_id, type="test")
        self._backlinks = list(backlinks)
        self._links = list(links)

    def get_backlinks(self, link_name: str, *, as_str: bool) -> list[FakeLink]:
        del link_name, as_str
        return self._backlinks

    def get_links(self, link_name: str, *, as_str: bool) -> list[FakeLink]:
        del link_name, as_str
        return self._links


def test_backlinks_merge_indexed_and_new_outgoing_links(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A stale non-empty backlink index must not hide links added later."""
    requirement = FakeNeed(
        "REQ",
        backlinks=[FakeLink("TC-old")],
    )
    old_testcase = FakeNeed("TC-old", links=[FakeLink("REQ")])
    new_testcase = FakeNeed("TC-new", links=[FakeLink("REQ")])
    needs = {need["id"]: need for need in (requirement, old_testcase, new_testcase)}
    monkeypatch.setattr(templates, "_get_available_needs", lambda: needs)

    linked_needs_class = vars(templates)["_LinkedNeeds"]
    linked = linked_needs_class()("REQ", "fully_verifies_back")

    assert [need["id"] for need in linked] == ["TC-old", "TC-new"]
