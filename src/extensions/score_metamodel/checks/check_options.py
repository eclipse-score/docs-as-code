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

from score_metamodel import (
    CheckLogger,
    ScoreNeedType,
    default_options,
    local_check,
)
from sphinx.application import Sphinx
from sphinx_needs.data import NeedsInfoType


def get_need_type(needs_types: list[ScoreNeedType], directive: str) -> ScoreNeedType:
    for need_type in needs_types:
        assert isinstance(need_type, dict), need_type
        if need_type["directive"] == directive:
            return need_type
    raise ValueError(f"Need type {directive} not found in needs_types")


def _normalize_values(raw_value: str | list[str] | None) -> list[str]:
    """Normalize a raw value into a list of strings."""
    if raw_value is None:
        return []
    if isinstance(raw_value, str):
        return [raw_value]
    if isinstance(raw_value, list) and all(isinstance(v, str) for v in raw_value):
        return raw_value
    raise ValueError


def _validate_value_pattern(
    value: str,
    pattern: str,
    need: NeedsInfoType,
    field: str,
):
    """Check if a value matches the given pattern and log the result.

    Returns true if the value matches the pattern, False otherwise.
    """
    try:
        return re.match(pattern, value) is not None
    except TypeError as e:
        raise TypeError(
            f"Error in metamodel.yaml at {need['type']}->{field}: "
            f"pattern `{pattern}` is not a valid regex pattern."
        ) from e


def validate_fields(
    need: NeedsInfoType,
    log: CheckLogger,
    fields: dict[str, str],
    required: bool,
    field_type: str,
    allowed_prefixes: list[str],
):
    """
    Validates that fields (options or links) in a need match their expected patterns.

    :param need: The need object containing the data.
    :param log: Logger for warnings.
    :param fields: A dictionary of field names and their regex patterns.
    :param required: Whether the fields are required (True) or optional (False).
    :param field_type: A string indicating the field type ('option' or 'link').
    """

    def remove_prefix(word: str, prefixes: list[str]) -> str:
        # Memory and allocation wise better to use a generator here.
        # Removes any prefix allowed by configuration, if prefix is there.
        return [word.removeprefix(prefix) for prefix in prefixes][0]

    optional_link_as_info = (not required) and (field_type == "link")

    for field, allowed_value in fields.items():
        raw_value: str | list[str] | None = need.get(field, None)
        if raw_value in [None, [], ""]:
            if required:
                log.warning_for_need(
                    need, f"is missing required {field_type}: `{field}`."
                )
            continue  # Nothing to validate if not present

        values = _normalize_values(raw_value)

        # regex based validation
        for value in values:
            if allowed_prefixes:
                value = remove_prefix(value, allowed_prefixes)
            if not _validate_value_pattern(value, allowed_value, need, field):
                msg = f"does not follow pattern `{allowed_value}`."
                log.warning_for_option(
                    need,
                    field,
                    msg,
                    is_new_check=optional_link_as_info,
                )


# req-Id: tool_req__docs_req_attr_reqtype
# req-Id: tool_req__docs_common_attr_security
# req-Id: tool_req__docs_common_attr_safety
# req-Id: tool_req__docs_common_attr_status
# req-Id: tool_req__docs_req_attr_rationale
# req-Id: tool_req__docs_arch_attr_mandatory
@local_check
def check_options(
    app: Sphinx,
    need: NeedsInfoType,
    log: CheckLogger,
):
    """
    Checks that required and optional options and links are present
    and follow their defined patterns.
    """
    need_type = get_need_type(app.config.needs_types, need["type"])

    # If undefined this is an empty list
    allowed_prefixes = app.config.allowed_external_prefixes

    # Validate Options and Links
    field_validations = [
        ("option", need_type["mandatory_options"], True),
        ("option", need_type["optional_options"], False),
        ("link", need_type["mandatory_links"], True),
        ("link", need_type["optional_links"], False),
    ]

    for field_type, field_values, is_required in field_validations:
        validate_fields(
            need,
            log,
            field_values,
            required=is_required,
            field_type=field_type,
            allowed_prefixes=allowed_prefixes,
        )


@local_check
def check_extra_options(
    app: Sphinx,
    need: NeedsInfoType,
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
