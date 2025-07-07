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
import os
import re

from sphinx.application import Sphinx
from sphinx_needs.data import NeedsInfoType

from score_metamodel import (
    CheckLogger,
    local_check,
)


@local_check
def id_contains_feature(app: Sphinx, need: NeedsInfoType, log: CheckLogger):
    """
    The ID is expected to be in the format '<Req Type>__<feature>__<Title>'.
    Most of this is ensured via regex in the metamodel.
    However the feature part is checked here.
    """

    parts = need["id"].split("__")

    if len(parts) != 3 or need["id"].startswith("stkh_req__"):
        # No warning needed here, as this is already checked in the metamodel.
        return

    # Get the part of the string after the first two underscores: the path
    feature = parts[1]
    featureparts = re.split(r"[_-]", feature)

    dir_docname = os.path.dirname(str(need.get("docname", "")))

    # If the 'rst' file is not in a directory, the above expression will be "".
    # Even if the need itself has a docname. That's why we have this logic here.
    # NOTE: This does not match the process requirements
    docname = dir_docname if dir_docname else need.get("docname", "")

    # allow if any feature part is contained in UID
    foundfeatpart = any(
        featurepart.lower() in docname.lower()
        for featurepart in featureparts
        if featureparts
    )

    # allow abbreviation of the feature
    initials = "".join(
        featurepart[0].lower() for featurepart in featureparts if len(featureparts) > 1
    )
    foundinitials = initials in docname.lower()

    if not (foundfeatpart or foundinitials):
        log.warning_for_option(
            need,
            "id",
            f"Featurepart '{featureparts}' not in path '{docname}' or abbreviation not ok, expected: '{initials}'.",
        )
