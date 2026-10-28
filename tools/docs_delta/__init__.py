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
"""Compare documentation builds and format a Markdown delta."""

from .cli import main
from .comparison import (
    DocsDeltaError,
    NeedChange,
    NeedComparison,
    NeedMap,
    PageChange,
    PageComparison,
    compare_needs,
    load_needs,
)
from .rendered_html import compare_html, normalize_html
from .report import (
    MAX_RENDERED_VALUE_LENGTH,
    need_link,
    render_report,
    unavailable_report,
)

__all__ = [
    "DocsDeltaError",
    "MAX_RENDERED_VALUE_LENGTH",
    "NeedChange",
    "NeedComparison",
    "NeedMap",
    "PageChange",
    "PageComparison",
    "compare_html",
    "compare_needs",
    "load_needs",
    "main",
    "need_link",
    "normalize_html",
    "render_report",
    "unavailable_report",
]
