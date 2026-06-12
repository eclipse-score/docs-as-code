# *******************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
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
import operator
from collections.abc import Callable
from functools import reduce
from itertools import chain
from typing import Any, cast

from score_metamodel import (
    CheckLogger,
    graph_check,
)
from sphinx.application import Sphinx
from sphinx_needs import logging
from sphinx_needs.config import NeedType
from sphinx_needs.data import NeedsView
from sphinx_needs.need_item import NeedItem

# This is the normal logger for this module, not for warnings on specific needs.
# Use CheckLogger for that, which allows us to log the need id and location together with the warning message.
logger = logging.get_logger(__name__)


def eval_need_check(need: NeedItem, check: str, log: CheckLogger) -> bool:
    """
    Perform a single check on a need:
    1. Split the check into its parts
       (e.g. "status == valid" -> ["status", "==", "valid"])
    2. Perform the check with the operator specified in the yaml file.
    """
    oper: dict[str, Callable[[Any, Any], bool]] = {
        "==": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "contains": lambda a, b: b in a if isinstance(a, str) else False,
    }

    parts = check.split(" ")

    if len(parts) != 3:
        raise ValueError(f"Invalid check defined: {check}")

    if parts[1] not in oper:
        raise ValueError(f"Binary Operator not defined: {parts[1]}")

    if parts[0] not in need:
        msg = f"Attribute not defined: {parts[0]}"
        log.warning_for_need(need, msg)
        return False

    return oper[parts[1]](need[parts[0]], parts[2])


def eval_need_condition(
    need: NeedItem, condition: str | dict[str, list[Any]], log: CheckLogger
) -> bool:
    """Evaluate a condition on a need:
    1. Check if the condition is only a simple check (e.g. "status == valid")
       If so call the check function.
    2. If the condition is a combination of multiple checks
       (e.g. "and: [check1, check2]")
       Recursively call the eval_need_function for each check and combine the
       results with the binary operation which was specified in the yaml file.
    """
    oper: dict[str, Any] = {
        "and": operator.and_,
        "or": operator.or_,
        "xor": operator.xor,
    }

    if not isinstance(condition, dict):
        if not isinstance(condition, str):
            raise ValueError(
                f"Invalid condition type: condition ({type(condition)}),"
                " expected str or dict."
            )
        return eval_need_check(need, condition, log)

    cond: str = list(condition.keys())[0]
    vals: list[Any] = list(condition.values())[0]

    if cond == "not":
        if not isinstance(vals, list) or len(vals) != 1:
            raise ValueError("Operator 'not' requires exactly one operand.")

        return not eval_need_condition(need, vals[0], log)

    if cond in oper:
        if not isinstance(vals, list) or len(vals) <= 1:
            raise ValueError(f"Operator '{cond}' requires at least two operands.")

        return reduce(
            lambda a, b: oper[cond](a, b),
            (eval_need_condition(need, val, log) for val in vals),
        )

    raise ValueError(f"Unsupported condition operator: {cond}")


def filter_needs_by_criteria(
    needs_types: list[NeedType],
    needs: list[NeedItem],
    needs_selection_criteria: dict[str, str],
    log: CheckLogger,
) -> list[NeedItem]:
    """
    Filter needs by include/exclude type patterns and an additional condition.

    The function:
    - accepts exactly one selector key: "include" or "exclude"
    - validates that "condition" exists
    - logs warnings for unknown need types in selector patterns
    - returns needs matching selector + condition
    """
    selected_needs: list[NeedItem] = []

    if "include" in needs_selection_criteria and "exclude" in needs_selection_criteria:
        raise ValueError(
            f"Invalid need selection: both include and exclude are set: {needs_selection_criteria}"
        )

    if "include" in needs_selection_criteria:
        need_pattern = "include"
        raw_patterns = needs_selection_criteria["include"]
    elif "exclude" in needs_selection_criteria:
        need_pattern = "exclude"
        raw_patterns = needs_selection_criteria["exclude"]
    else:
        raise ValueError(f"Invalid need selection: {needs_selection_criteria}")

    if "condition" not in needs_selection_criteria:
        raise ValueError(f"Invalid selection: {needs_selection_criteria}")

    condition = needs_selection_criteria["condition"]
    pattern = [pat.strip() for pat in raw_patterns.split(",") if pat.strip()]

    for pat in pattern:
        if not any(need_type["directive"] == pat for need_type in needs_types):
            log.warning(f"Unknown need type `{pat}` in graph check.", location="")

    for need in needs:
        sel = (
            need["type"] in pattern
            if need_pattern == "include"
            else need["type"] not in pattern
        )
        if sel and eval_need_condition(need, condition, log):
            selected_needs.append(need)

    return selected_needs


@graph_check
def check_metamodel_graph(
    app: Sphinx,
    all_needs: NeedsView,
    log: CheckLogger,
):
    graph_checks_global = app.config.graph_checks
    # Convert list to dictionary for easy lookup
    needs_dict_all = {need["id"]: need for need in all_needs.values()}
    needs_local = list(all_needs.filter_is_external(False).values())

    # Iterate over all graph checks
    for check_name, check_config in graph_checks_global.items():
        needs_selection_criteria: dict[str, str] = check_config.get("needs")
        check_to_perform: dict[str, str | dict[str, Any]] = check_config.get("check")
        explanation = check_config.get("explanation", "")
        assert explanation != "", (
            f"Explanation for graph check {check_name} is missing. "
            "Explanations are mandatory for graph checks."
        )
        # Get all needs matching the selection criteria
        try:
            selected_needs = filter_needs_by_criteria(
                app.config.needs_types, needs_local, needs_selection_criteria, log
            )
        except ValueError as e:
            # Turn a 3 page callstack into a readable error message for the user, since
            # this is a configuration error in the yaml file.
            logger.error(f"Error in graph check `{check_name}`: {e}")
            continue

        for need in selected_needs:
            for parent_relation in list(check_to_perform.keys()):
                if parent_relation not in need:
                    msg = (
                        f"Attribute not defined: `{parent_relation}` "
                        f"in need `{need['id']}`."
                    )
                    log.warning_for_need(need, msg)
                    continue

                parent_ids = cast(list[str] | Any, need[parent_relation])
                if not isinstance(parent_ids, list):
                    continue

                parent_ids_list = cast(list[str], parent_ids)
                for parent_id in parent_ids_list:
                    parent_need = needs_dict_all.get(parent_id)
                    if parent_need is None:
                        msg = f"Parent need `{parent_id}` not found in needs_dict."
                        log.warning_for_need(need, msg)
                        continue

                    if not eval_need_condition(
                        parent_need, check_to_perform[parent_relation], log
                    ):
                        msg = (
                            f"Parent need `{parent_id}` does not fulfill "
                            f"condition `{check_to_perform[parent_relation]}`."
                            f" Explanation: {explanation}"
                        )
                        log.warning_for_need(need, msg)


@graph_check
def check_valid_only_links_to_valid(
    app: Sphinx,
    all_needs: NeedsView,
    log: CheckLogger,
):
    # Pre-Gather all *valid* need id's (external, & local)
    valid_needs_id_all = set(
        x.id for x in all_needs.values() if x.get("status") == "valid"
    )
    # Pre-Gather all LOCAL *valid* id's to iterate over and check
    valid_needs_local = [
        x
        for x in all_needs.filter_is_external(False).values()
        if x.get("status") == "valid"
    ]

    for need in valid_needs_local:
        # Using set comprehension here to enable faster computation for comparisons
        all_linked_needs: set[str] = set(
            x.id
            for x in set(chain(*need._links.values()))  # type: ignore
        )
        invalid_needs = all_linked_needs.difference(valid_needs_id_all)
        if invalid_needs:
            msg = f"is valid but links to invalid need(s): {invalid_needs}"
            log.warning_for_need(need, msg, is_new_check=True)
