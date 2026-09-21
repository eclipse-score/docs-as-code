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


def test_parse_version_pads_missing_patch() -> None:
    """A two-component milestone implies patch ``0`` for comparison purposes."""
    parse_version = vars(templates)["_parse_version"]

    assert parse_version("v0.8") == (0, 8, 0)
    assert parse_version("v1.0.1") == (1, 0, 1)
    assert parse_version("V2.3") == (2, 3, 0)


def test_req_in_report_version_unscoped_report_version_always_true() -> None:
    """No ``report_version`` means the report is unscoped ("latest")."""
    req_in_report_version = vars(templates)["_RequirementInReportVersion"]()
    need = FakeNeed("feat_req__x")

    assert req_in_report_version(need, None) is True
    assert req_in_report_version(need, "") is True


def test_req_in_report_version_direct_valid_from_boundary() -> None:
    """``valid_from`` is inclusive: equal or later report_version is in scope."""
    req_in_report_version = vars(templates)["_RequirementInReportVersion"]()
    need = FakeNeed("feat_req__x")
    need["valid_from"] = "v0.8"

    assert req_in_report_version(need, "v0.7") is False
    assert req_in_report_version(need, "v0.8") is True
    assert req_in_report_version(need, "v0.9") is True


def test_req_in_report_version_malformed_valid_from_is_excluded() -> None:
    """An unparsable ``valid_from`` must not raise; it just excludes the need."""
    req_in_report_version = vars(templates)["_RequirementInReportVersion"]()
    need = FakeNeed("feat_req__x")
    need["valid_from"] = "not-a-version"

    assert req_in_report_version(need, "v1.0") is False


def test_req_in_report_version_missing_valid_from_without_derived_from_is_excluded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A requirement with no ``valid_from`` and nothing to inherit from is out."""
    req_in_report_version = vars(templates)["_RequirementInReportVersion"]()
    comp_req = FakeNeed("comp_req__x")
    monkeypatch.setattr(
        templates, "_get_available_needs", lambda: {"comp_req__x": comp_req}
    )

    assert req_in_report_version(comp_req, "v1.0") is False


def test_req_in_report_version_comp_req_inherits_via_derived_from(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``comp_req`` has no ``valid_from`` of its own; it inherits its scope from
    the ``feat_req`` it is ``derived_from``."""
    req_in_report_version = vars(templates)["_RequirementInReportVersion"]()
    feat_req = FakeNeed("feat_req__x")
    feat_req["valid_from"] = "v0.8"
    comp_req = FakeNeed("comp_req__x", links=[FakeLink("feat_req__x")])
    needs = {"feat_req__x": feat_req, "comp_req__x": comp_req}
    monkeypatch.setattr(templates, "_get_available_needs", lambda: needs)

    assert req_in_report_version(comp_req, "v0.7") is False
    assert req_in_report_version(comp_req, "v0.8") is True


def test_any_req_in_report_version_unscoped_true_even_for_empty_list() -> None:
    """Unscoped ("latest") reports keep Features/Components with no requirement."""
    any_req_in_report_version = vars(templates)["_AnyRequirementInReportVersion"]()

    assert any_req_in_report_version([], None) is True


def test_any_req_in_report_version_scoped_empty_list_is_excluded() -> None:
    """A scoped report has nothing to show for a Feature/Component with no reqs."""
    any_req_in_report_version = vars(templates)["_AnyRequirementInReportVersion"]()

    assert any_req_in_report_version([], "v1.0") is False


def test_any_req_in_report_version_true_if_at_least_one_requirement_matches() -> None:
    any_req_in_report_version = vars(templates)["_AnyRequirementInReportVersion"]()
    out_of_scope = FakeNeed("feat_req__a")
    out_of_scope["valid_from"] = "v2.0"
    in_scope = FakeNeed("feat_req__b")
    in_scope["valid_from"] = "v0.8"

    assert any_req_in_report_version([out_of_scope, in_scope], "v1.0") is True


def test_any_req_in_report_version_false_if_no_requirement_matches() -> None:
    any_req_in_report_version = vars(templates)["_AnyRequirementInReportVersion"]()
    a = FakeNeed("feat_req__a")
    a["valid_from"] = "v2.0"
    b = FakeNeed("feat_req__b")
    b["valid_from"] = "v3.0"

    assert any_req_in_report_version([a, b], "v1.0") is False
