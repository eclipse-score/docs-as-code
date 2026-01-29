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
import re
from typing import cast

from score_metamodel import (
    CheckLogger,
    ScoreNeedType,
    default_options,
    local_check,
)
from score_metamodel.metamodel_types import AllowedLinksType
from sphinx.application import Sphinx
from sphinx_needs.need_item import NeedItem


def get_need_type(needs_types: list[ScoreNeedType], directive: str) -> ScoreNeedType:
    for need_type in needs_types:
        assert isinstance(need_type, dict), need_type
        if need_type["directive"] == directive:
            return need_type
    raise ValueError(f"Need type {directive} not found in needs_types")


def _get_normalized(need: NeedItem, key: str, remove_prefix: bool = False) -> list[str]:
    """Normalize a raw value into a list of strings."""
    raw_value = need.get(key, None)
    if not raw_value:
        return []
    if isinstance(raw_value, str):
        if remove_prefix:
            return [_remove_namespace_prefix_(raw_value)]
        return [raw_value]
    if isinstance(raw_value, list):
        # Verify all elements are strings
        raw_list = cast(list[object], raw_value)
        for item in raw_list:
            if not isinstance(item, str):
                raise ValueError
        str_list = cast(list[str], raw_value)
        if remove_prefix:
            return [_remove_namespace_prefix_(v) for v in str_list]
        return str_list
    raise ValueError


def _validate_value_pattern(
    value: str,
    pattern: str,
    need: NeedItem,
    field: str,
):
    """Check if a value matches the given pattern and log the result.

    Returns true if the value matches the pattern, False otherwise.
    """
    try:
        return re.match(pattern, value) is not None
    except Exception as e:
        raise TypeError(
            f"Error in metamodel.yaml at {need['type']}->{field}: "
            f"pattern `{pattern}` is not a valid regex pattern."
        ) from e


def _remove_namespace_prefix_(word: str) -> str:
    # If the word starts with uppercase letters followed by an underscore, remove them.
    return re.sub(r"^[A-Z]+_", "", word)


def validate_options(
    log: CheckLogger,
    need_type: ScoreNeedType,
    need: NeedItem,
):
    """
    Validates that options in a need match their expected patterns.
    """

    def _validate(attributes_to_allowed_values: dict[str, str], mandatory: bool):
        for attribute, allowed_regex in attributes_to_allowed_values.items():
            values = _get_normalized(need, attribute)
            if mandatory and not values:
                log.warning_for_need(
                    need, f"is missing required attribute: `{attribute}`."
                )

            for value in values:
                if not _validate_value_pattern(value, allowed_regex, need, attribute):
                    log.warning_for_option(
                        need, attribute, f"does not follow pattern `{allowed_regex}`."
                    )

    _validate(need_type["mandatory_options"], True)
    _validate(need_type["optional_options"], False)


def validate_links(
    log: CheckLogger,
    need_type: ScoreNeedType,
    need: NeedItem,
):
    """
    Validates that links in a need match the expected types or regexes.
    """

    def _validate(
        attributes_to_allowed_values: AllowedLinksType,
        mandatory: bool,
        treat_as_info: bool = False,
    ):
        for attribute, allowed_values in attributes_to_allowed_values.items():
            values = _get_normalized(need, attribute, remove_prefix=True)
            if mandatory and not values:
                log.warning_for_need(need, f"is missing required link: `{attribute}`.")

            allowed_regex = "|".join(
                [
                    v if isinstance(v, str) else v["mandatory_options"]["id"]
                    for v in allowed_values
                ]
            )

            # regex based validation
            for value in values:
                if not _validate_value_pattern(value, allowed_regex, need, attribute):
                    log.warning_for_link(
                        need,
                        attribute,
                        value,
                        [
                            av
                            if isinstance(av, str)
                            else f"{av['title']} ({av['directive']})"
                            for av in allowed_values
                        ],
                        allowed_regex,
                        is_new_check=treat_as_info,
                    )

    _validate(need_type["mandatory_links"], True)
    _validate(need_type["optional_links"], False, treat_as_info=True)


# req-Id: tool_req__docs_req_attr_reqtype
# req-Id: tool_req__docs_common_attr_security
# req-Id: tool_req__docs_common_attr_safety
# req-Id: tool_req__docs_common_attr_status
# req-Id: tool_req__docs_req_attr_rationale
# req-Id: tool_req__docs_arch_attr_mandatory
@local_check
def check_options(
    app: Sphinx,
    need: NeedItem,
    log: CheckLogger,
):
    """
    Checks that required and optional options and links are present
    and follow their defined patterns.
    """
    need_type = get_need_type(app.config.needs_types, need["type"])

    validate_options(log, need_type, need)
    validate_links(log, need_type, need)


@local_check
def check_extra_options(
    app: Sphinx,
    need: NeedItem,
    log: CheckLogger,
):
    """
    This function checks if the user specified attributes in the need
    which are not defined for this element in the metamodel or by default
    system attributes.
    """

    production_needs_types = app.config.needs_types
    need_options = get_need_type(production_needs_types, need["type"])

    # set() creates a copy to avoid modifying the original
    allowed_options = set(default_options())

    for o in (
        "mandatory_options",
        "optional_options",
        "mandatory_links",
        "optional_links",
    ):
        allowed_options.update(need_options[o].keys())

    extra_options = [
        option
        for option in need
        if option not in allowed_options
        and need[option] not in [None, {}, "", []]
        and not option.endswith("_back")
    ]

    if extra_options:
        extra_options_str = ", ".join(f"`{option}`" for option in extra_options)
        msg = f"has these extra options: {extra_options_str}."
        log.warning_for_need(need, msg)


def parse_milestone(value: str) -> tuple[int, int, int]:
    """Parse a string like 'v0.5' or 'v1.0.0'. No suffixes."""
    match = re.match(r"v(\d+)(\.(\d+))?(\.(\d+))?$", value)
    if not match:
        raise ValueError(f"Invalid milestone format: {value}")
    major = int(match.group(1))
    minor = int(match.group(3) or 0)
    patch = int(match.group(5) or 0)
    return (major, minor, patch)


# req-Id: tool_req__docs_req_attr_validity_consistency
@local_check
def check_validity_consistency(
    app: Sphinx,
    need: NeedItem,
    log: CheckLogger,
):
    """
    Check if the attributes valid_from < valid_until.
    """
    if need["type"] not in ("stkh_req", "feat_req"):
        return

    valid_from = need.get("valid_from", None)
    valid_until = need.get("valid_until", None)

    if not valid_from or not valid_until:
        return

    valid_from_version = parse_milestone(valid_from)
    valid_until_version = parse_milestone(valid_until)
    if valid_from_version >= valid_until_version:
        msg = (
            "inconsistent validity: "
            f"valid_from ({valid_from}) >= valid_until ({valid_until})."
        )
        log.warning_for_need(need, msg)
