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

from __future__ import annotations

from dataclasses import dataclass, field

from sphinx_needs.config import NeedType


@dataclass
class ProhibitedWordCheck:
    name: str
    option_check: dict[str, list[str]] = field(
        default_factory=dict
    )  # { Option: [Forbidden words]}
    types: list[str] = field(default_factory=list)


class ScoreNeedType(NeedType):
    tags: list[str]
    parts: int

    mandatory_options: dict[str, str]
    optional_options: dict[str, str]

    # Holds either regexes (str) or a list of other need types (list of ScoreNeedType).
    # One or the other for simplicity, no mixing.
    mandatory_links: dict[str, str] | dict[str, list[ScoreNeedType]]
    optional_links: dict[str, str] | dict[str, list[ScoreNeedType]]
