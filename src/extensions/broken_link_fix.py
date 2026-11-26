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
from collections.abc import Callable
from enum import StrEnum
from typing import Any, cast

from sphinx._cli.util.colour import darkgray
from sphinx.application import Sphinx
from sphinx.builders import linkcheck
from sphinx.builders.linkcheck import CheckExternalLinksBuilder, CheckResult
from sphinx.util import logging

logger = logging.getLogger(__name__)

linkcheckbase = cast(
    Callable[[CheckExternalLinksBuilder, CheckResult], None],
    linkcheck.CheckExternalLinksBuilder.process_result,
)


class _Status(StrEnum):
    BROKEN = "broken"


IGNORED_HTTP_CODES: frozenset[int] = frozenset({401, 402, 403, 407, 418, 429, 451, 511})

# When requests.raise_for_status()/HTTPError reports a failure, Sphinx sets
# CheckResult.code to 0 and the HTTP status only appears in the message
# (e.g. "403 Client Error: Forbidden for url: ..."). requests phrases 4xx
# as "Client Error" and 5xx as "Server Error".
_HTTP_ERROR_RE = re.compile(r"\b(4\d\d|5\d\d) (?:Client|Server) Error\b")


def _ignored_http_error(result: CheckResult) -> bool:
    """Return whether result reports an HTTP error that should be ignored."""
    # For status="broken", Sphinx always reports CheckResult.code = 0.
    # The HTTP status only appears in the message, so parse it from there
    # and apply the curated ignore list.
    match = _HTTP_ERROR_RE.search(str(result.message))
    if match is None:
        return False
    return int(match.group(1)) in IGNORED_HTTP_CODES


def process_result(self: CheckExternalLinksBuilder, result: CheckResult) -> None:
    """hook a custom process_result function.

    Args:
        self: The CheckExternalLinksBuilder instance.
        result: The CheckResult instance.

    Returns:
        None
    """
    match result.status:
        case _Status.BROKEN:
            # Ignore selected HTTP errors that can be caused by access restrictions or rate limits.
            if _ignored_http_error(result):
                logger.info(darkgray("-ignored- ") + result.uri)
                self.write_entry(
                    "ignored",
                    result.docname,
                    self.env.doc2path(result.docname, False),
                    result.lineno,
                    f"{result.uri} to {result.message}",
                )
                return

            """ Ignore Anchor errors from .md files """
            if re.match(
                r"https?://.*?\.md#[A-Za-z0-9_.-]+$", result.uri
            ) and "Anchor" in str(result.message):
                logger.info(darkgray("-ignored- ") + result.uri)
                self.write_entry(
                    "ignored",
                    result.docname,
                    self.env.doc2path(result.docname, False),
                    result.lineno,
                    f"{result.uri} to {result.message}",
                )
                return

    linkcheckbase(self, result)


def setup(app: Sphinx) -> dict[str, object]:
    """Register the custom linkcheck extension.

    The extension patches the default Sphinx linkcheck builder to ignore
    known false-positive anchor errors reported for selected GitHub
    Markdown URLs.

    Args:
        app: The Sphinx application instance.

    Returns:
        Extension metadata required by Sphinx.
    """

    # hook a custom process_result function
    cast(Any, linkcheck.CheckExternalLinksBuilder).process_result = process_result

    return {
        "version": "0.0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
