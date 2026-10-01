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

from __future__ import annotations

from typing import Any, cast
from unittest.mock import MagicMock

import pytest

# Adjust this import path if your project layout differs.
import score_metamodel.checks.graph_checks as graph_checks
from score_metamodel.tests import fake_check_logger, need as test_need
from sphinx_needs.config import NeedType
from sphinx_needs.data import NeedsView
from sphinx_needs.need_item import NeedItem


class DummyNeedsView:
    """Minimal NeedsView-like test double."""

    def __init__(self, needs: list[NeedItem]) -> None:
        """Create a view over the given needs."""
        self._needs = needs

    def values(self) -> list[NeedItem]:
        """Return all needs."""
        return self._needs

    def filter_ids(self, ids: list[str]) -> DummyNeedsView:
        """Filter needs by id. Unknown ids are dropped, like in sphinx-needs."""
        return DummyNeedsView([n for n in self._needs if n["id"] in ids])

    def filter_is_external(self, is_external: bool) -> DummyNeedsView:
        """Filter needs by their is_external flag."""
        return DummyNeedsView(
            [n for n in self._needs if n.get("is_external", False) == is_external]
        )


def test_eval_need_check_invalid_check_parts_raises_value_error() -> None:
    """Raise error when a check does not contain exactly three parts."""
    log = fake_check_logger()
    need = test_need(status="valid")

    with pytest.raises(ValueError, match="Invalid check defined"):
        graph_checks.eval_need_check(need, "status==valid", log)


def test_eval_need_check_unknown_operator_raises_value_error() -> None:
    """Raise error when an unsupported binary operator is used."""
    log = fake_check_logger()
    need = test_need(status="valid")

    with pytest.raises(ValueError, match="Binary Operator not defined"):
        graph_checks.eval_need_check(need, "status <> valid", log)


def test_eval_need_check_missing_attribute_logs_and_returns_false() -> None:
    """Return False and log warning when referenced attribute is not present."""
    log = fake_check_logger()
    need = test_need(status="valid")

    result = graph_checks.eval_need_check(need, "priority == high", log)

    assert result is False
    log.assert_warning("Attribute not defined: priority")

    result2 = graph_checks.eval_need_condition(need, {"not": ["status == valid"]}, log)

    assert result2 is False
    # assert "Attribute not defined: priority" in msg


def test_eval_need_condition_invalid_type_raises_value_error() -> None:
    """Raise error for condition values that are neither string nor dict."""
    log = fake_check_logger()
    need = test_need(status="valid")

    with pytest.raises(ValueError, match="Invalid condition type"):
        graph_checks.eval_need_condition(need, 123, log)  # type: ignore[arg-type]


def test_eval_need_condition_not_with_wrong_operand_count_raises_value_error() -> None:
    """Raise error when 'not' does not receive exactly one operand."""
    log = fake_check_logger()
    need = test_need(status="valid")

    with pytest.raises(ValueError, match="requires exactly one operand"):
        graph_checks.eval_need_condition(
            need,
            {"not": ["status == valid", "status != invalid"]},
            log,
        )


def test_eval_need_condition_and_or_xor_branches() -> None:
    """Evaluate logical combination branches and, or and xor."""
    log = fake_check_logger()
    need = test_need(status="valid", kind="req")

    and_result = graph_checks.eval_need_condition(
        need,
        {"and": ["status == valid", "kind == req"]},
        log,
    )
    or_result = graph_checks.eval_need_condition(
        need,
        {"or": ["status == invalid", "kind == req"]},
        log,
    )
    xor_result = graph_checks.eval_need_condition(
        need,
        {"xor": ["status == valid", "kind == req"]},
        log,
    )

    assert and_result is True
    assert or_result is True
    assert xor_result is False

    with pytest.raises(ValueError, match="Unsupported condition operator: blah"):
        graph_checks.eval_need_condition(
            need,
            {"blah": ["status == valid", "kind == req"]},
            log,
        )


def test_filter_needs_by_criteria_invalid() -> None:
    """Raise error when include/exclude selector key is invalid."""
    log = fake_check_logger()
    test_need()
    needs_types = [NeedType({"title": "testtype", "prefix": "t", "directive": "req"})]
    needs = [test_need(id="N1", type="testtype", status="valid")]

    with pytest.raises(ValueError, match="Invalid need selection"):
        graph_checks.filter_needs_by_criteria(
            needs_types,
            needs,
            {"invalid": "req", "condition": "status == valid"},
            log,
        )

    with pytest.raises(ValueError, match="Invalid selection"):
        graph_checks.filter_needs_by_criteria(
            needs_types,
            needs,
            {"exclude": "req"},
            log,
        )
    with pytest.raises(
        ValueError, match="Invalid need selection: both include and exclude are set"
    ):
        graph_checks.filter_needs_by_criteria(
            needs_types,
            needs,
            {"include": "req", "exclude": "req"},
            log,
        )


def test_filter_needs_by_criteria_unknown_type_logs_warning() -> None:
    """Log warning when selected pattern contains unknown need type."""
    log = fake_check_logger()
    needs_types = [NeedType({"title": "testtype", "prefix": "t", "directive": "req"})]
    needs = [test_need(id="N1", type="whasxd", status="valid")]

    selected = graph_checks.filter_needs_by_criteria(
        needs_types,
        needs,
        {"include": "unknown", "condition": "status == valid"},
        log,
    )
    assert selected == []
    assert log.warnings == 1
    log.assert_warning(
        "Unknown need type `unknown` in graph check.", expect_location=False
    )


NEEDS_TYPES = [NeedType({"title": "testtype", "prefix": "t", "directive": "req"})]
PARENTS = [
    test_need(id="safe_1", type="parent", safety="ASIL_B"),
    test_need(id="qm_1", type="parent", safety="QM"),
    test_need(id="qm_2", type="parent", safety="QM"),
]


def graph_check_config(*check_keys: str) -> dict[str, Any]:
    """Graph check that requires linked `implements` needs to be safety relevant."""
    return {
        "needs": {"include": "req", "condition": "status == valid"},
        **{key: {"implements": "safety != QM"} for key in check_keys},
        "explanation": "Test explanation.",
    }


def run_graph_check(check_config: dict[str, Any], parent_ids: list[str]):
    """Run the graph check on one child need linking to the given parents."""
    log = fake_check_logger()
    app = MagicMock()
    app.config.graph_checks = {"test_check": check_config}
    app.config.needs_types = NEEDS_TYPES
    child = test_need(id="child", type="req", status="valid", implements=parent_ids)
    all_needs = cast(NeedsView, DummyNeedsView([child, *PARENTS]))

    graph_checks.check_metamodel_graph(app, all_needs, log)
    return log


@pytest.mark.parametrize(
    ("check_keys", "error"),
    [
        ((), "test_check. Either `check_all` or `check_one` are mandatory"),
        (("check",), "test_check. Either `check_all` or `check_one` are mandatory"),
        (
            ("check_all", "check_one"),
            "Both `check_one` and `check_all` are present in graph_check: test_check",
        ),
    ],
    ids=["missing", "old_check_key", "both"],
)
def test_invalid_check_keys_raise_value_error(
    check_keys: tuple[str, ...], error: str
) -> None:
    """Fail unless exactly one of check_all / check_one is defined."""
    with pytest.raises(ValueError, match=error):
        run_graph_check(graph_check_config(*check_keys), ["qm_1"])


def test_check_all_warns_once_per_failing_parent() -> None:
    """Report every linked need that does not fulfill the condition."""
    log = run_graph_check(graph_check_config("check_all"), ["safe_1", "qm_1", "qm_2"])
    assert log.warnings == 2

    log = run_graph_check(graph_check_config("check_all"), ["safe_1", "qm_1"])
    log.assert_warning(
        "Parent need `qm_1` does not fulfill condition `safety != QM`."
        " Explanation: Test explanation."
    )


@pytest.mark.parametrize(
    ("parent_ids", "expected_warnings"),
    [
        (["qm_1", "safe_1"], 0),
        (["qm_1", "qm_2"], 1),
        ([], 0),
        (["unknown_parent"], 0),
    ],
    ids=["one_fulfills", "none_fulfill", "no_parents", "unknown_parent"],
)
def test_check_one(parent_ids: list[str], expected_warnings: int) -> None:
    """Pass if at least one linked need fulfills the condition."""
    log = run_graph_check(graph_check_config("check_one"), parent_ids)

    assert log.warnings == expected_warnings
    if expected_warnings:
        log.assert_warning(
            "No linked need in `implements` fulfills condition `safety != QM`."
            " Explanation: Test explanation."
        )
