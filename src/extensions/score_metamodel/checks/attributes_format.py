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

import string
from typing import cast

from score_metamodel import CheckLogger, ProhibitedWordCheck, ScoreNeedType, local_check
from sphinx.application import Sphinx
from sphinx_needs.need_item import NeedItem


def get_need_type(needs_types: list[ScoreNeedType], directive: str) -> ScoreNeedType:
    for need_type in needs_types:
        assert isinstance(need_type, dict), need_type
        if need_type["directive"] == directive:
            return need_type
    raise ValueError(f"Need type {directive} not found in needs_types")


# req-Id: tool_req__docs_common_attr_id_scheme
@local_check
def check_id_format(app: Sphinx, need: NeedItem, log: CheckLogger):
    """
    Checking if the title, directory and feature are included in
    the requirement id or not.
    ---
    """
    need_options = get_need_type(app.config.needs_types, need["type"])
    expected_parts = need_options.get("parts", 3)
    id_parts = need["id"].split("__")
    id_parts_len = len(id_parts)

    if id_parts_len != expected_parts:
        msg = ""
        if expected_parts == 2:
            msg = (
                "expected to consist of this format: `<Req Type>__<Abbreviations>`. "
                "Only one '__' is allowed in this need's id."
            )
        elif expected_parts == 3:
            msg = (
                "expected to consist of this format: "
                "`<Req Type>__<Abbreviations>__<Architectural Element>`. "
                "Only two '__' are allowed in this need's id."
            )
        log.warning_for_option(need, "id", msg)


@local_check
def check_id_length(app: Sphinx, need: NeedItem, log: CheckLogger):
    """
    Validates that the requirement ID does not exceed the hard limit of 45 characters.
    While the recommended limit is 30 characters, this check enforces a strict maximum
    of 45 characters.
    If the ID exceeds 45 characters, a warning is logged specifying the actual length.
    Any examples that are required to have 3 parts (2x'__') have an exception,
    and get 17 extra characters to compensate for the lenght of `_example_feature_`
    that would be replaced by actually feature names.
    ---
    """
    max_length = 45
    parts = need["id"].split("__")
    if parts[1] == "example_feature":
        max_length += 17  # _example_feature_
    if len(need["id"]) > max_length:
        length = len(need["id"])
        if "example_feature" in need["id"]:
            length -= 17
        msg = (
            f"exceeds the maximum allowed length of 45 characters "
            "(current length: "
            f"{length})."
        )
        log.warning_for_option(need, "id", msg)


def _check_options_for_prohibited_words(
    prohibited_word_checks: ProhibitedWordCheck, need: NeedItem, log: CheckLogger
):
    options: list[str] = [
        x for x in prohibited_word_checks.option_check if x != "types"
    ]
    for option in options:
        forbidden_words = prohibited_word_checks.option_check[option]
        option_value = need.get(option)
        if not isinstance(option_value, str):
            continue
        option_text = cast(str, option_value)
        for word in option_text.split():
            normalized = word.strip(string.punctuation).lower()
            if normalized in forbidden_words:
                msg = (
                    f"contains a weak word: `{normalized}` in option: `{option}`. "
                    "Please revise the wording."
                )
                log.warning_for_need(need, msg)


# req-Id: tool_req__docs_common_attr_desc_wording
# req-Id: tool_req__docs_common_attr_title
@local_check
def check_for_prohibited_words(app: Sphinx, need: NeedItem, log: CheckLogger):
    need_options = get_need_type(app.config.needs_types, need["type"])
    prohibited_word_checks: list[ProhibitedWordCheck] = (
        app.config.prohibited_words_checks
    )
    for check in prohibited_word_checks:
        # Check if there are any type restrictions for this check
        types_to_check = check.types
        if types_to_check:
            if any(tag in need_options.get("tags", []) for tag in types_to_check):
                _check_options_for_prohibited_words(check, need, log)
        else:
            _check_options_for_prohibited_words(check, need, log)
