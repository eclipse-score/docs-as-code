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

from score_metamodel import CheckLogger, local_check, ScoreNeedType, ProhibitedWordCheck
from sphinx.application import Sphinx
from sphinx_needs.data import NeedsInfoType


def get_need_type(needs_types: list[ScoreNeedType], directive: str) -> ScoreNeedType:
    for need_type in needs_types:
        assert isinstance(need_type, dict), need_type
        if need_type["directive"] == directive:
            return need_type
    raise ValueError(f"Need type {directive} not found in needs_types")


@local_check
def check_id_length(app: Sphinx, need: NeedsInfoType, log: CheckLogger):
    """
    Validates that the requirement ID does not exceed the hard limit of 45 characters.
    While the recommended limit is 30 characters, this check enforces a strict maximum
    of 45 characters.
    If the ID exceeds 45 characters, a warning is logged specifying the actual length.
    ---
    """
    if len(need["id"]) > 45:
        msg = (
            f"exceeds the maximum allowed length of 45 characters "
            f"(current length: {len(need['id'])})."
        )
        log.warning_for_option(need, "id", msg)


def _check_options_for_prohibited_words(
    prohibited_word_checks: ProhibitedWordCheck, need: NeedsInfoType, log: CheckLogger
):
    options: list[str] = [
        x for x in prohibited_word_checks.option_check.keys() if x != "types"
    ]
    for option in options:
        forbidden_words = prohibited_word_checks.option_check[option]
        for word in need[option].split():
            if word in forbidden_words:
                msg = f"contains a weak word: `{word}` in option: `{option}`. Please revise the wording."
                log.warning_for_need(need, msg)


# req-#id: gd_req__req__attr_desc_weak
# # req-#id: gd_req__requirements_attr_title
@local_check
def check_for_prohibited_words(app: Sphinx, need: NeedsInfoType, log: CheckLogger):
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
