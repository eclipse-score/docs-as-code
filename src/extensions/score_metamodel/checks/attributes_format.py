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

from score_metamodel import CheckLogger, local_check
from sphinx.application import Sphinx
from sphinx_needs.data import NeedsInfoType


# req-#id: gd_req__req__attr_uid
@local_check
def check_id_format(app: Sphinx, need: NeedsInfoType, log: CheckLogger):
    """
    Checking if the title, directory and feature are included in
    the requirement id or not.
    ---
    """
    # These folders are taken from 'https://github.com/eclipse-score/process_description/tree/main/process'
    # This means, any needs within any of these folders (no matter where they are) will not be required to have 3 parts
    process_folder_names = [
        "general_concepts",
        "introduction",
        "process_areas",
        "roles",
        "standards",
        "workflows",
        "workproducts",
        "process",
    ]
    # Split the string by underscores
    parts = need["id"].split("__")
    if need["type"] in [
        "std_wp",
        "document",  # This is used in 'platform_managment' in score.
        "doc_tool",
        "gd_guidl",
        "workflow",
        "gd_chklst",
        "std_req",
        "tool_req",
        "role",
        "doc_concept",
        "gd_temp",
        "gd_method",
        "gd_req",
        "workproduct",
        "doc_getstrt",
    ] or any(prefix in str(need.get("docname", "")) for prefix in process_folder_names):
        if len(parts) != 2 and len(parts) != 3:
            msg = (
                "expected to consisting of one of these 2 formats:"
                "`<Req Type>__<Abbreviations>` or "
                "`<Req Type>__<Abbreviations>__<Architectural Element>`."
            )
            log.warning_for_option(need, "id", msg)
    else:
        if len(parts) != 3:
            msg = (
                "expected to consisting of this format: "
                "`<Req Type>__<Abbreviations>__<Architectural Element>`."
            )
            log.warning_for_option(need, "id", msg)


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


# req-#id: gd_req__requirements_attr_title
@local_check
def check_title(app: Sphinx, need: NeedsInfoType, log: CheckLogger):
    """
    Ensures that the requirement Title does not contain stop words.
    This helps enforce clear and concise naming conventions.
    """
    stop_words = app.config.stop_words
    if need["type"] in ["stkh_req", "feat_req", "comp_req"]:
        for word in stop_words:
            if word in need["title"]:
                msg = (
                    f"contains a stop word: `{word}`. "
                    "The title is meant to provide a short summary, "
                    "not to repeat the requirement statement. "
                    "Please revise the title for clarity and brevity."
                )
                log.warning_for_option(need, "title", msg)
                break


# req-#id: gd_req__req__attr_desc_weak
@local_check
def check_description(app: Sphinx, need: NeedsInfoType, log: CheckLogger):
    """
    Ensures that the requirement Description does not contain weak words.
    This helps enforce strong, clear, and unambiguous requirement phrasing
    ---
    """
    weak_words = app.config.weak_words
    if need["type"] in [
        "stkh_req",
        "feat_req",
        "comp_req",
    ] and need.get("content", None):
        for word in weak_words:
            if word in need["content"]:
                msg = f"contains a weak word: `{word}`. Please revise the description."
                log.warning_for_option(need, "content", msg)
                break
