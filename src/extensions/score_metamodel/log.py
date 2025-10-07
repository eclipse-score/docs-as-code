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
from typing import Any

from docutils.nodes import Node
from sphinx_needs import logging
from sphinx_needs.data import NeedsInfoType
from sphinx_needs.logging import SphinxLoggerAdapter

Location = str | tuple[str | None, int | None] | Node | None
NewCheck = tuple[str, Location]
logger = logging.get_logger(__name__)


class CheckLogger:
    def __init__(self, log: SphinxLoggerAdapter, prefix: str):
        self._log = log
        self._info_count = 0
        self._warning_count = 0
        self._prefix = prefix
        self._new_checks: list[NewCheck] = []

    @staticmethod
    def _location(need: NeedsInfoType, prefix: str):
        def get(key: str) -> Any:
            return need.get(key, None)

        if get("docname") and get("doctype") and get("lineno"):
            # Note: passing the location as a string allows us to use
            # readable relative paths, passing as a tuple results
            # in absolute paths to ~/.cache/.../bazel-out/..
            if "RUNFILES_DIR" in os.environ or "RUNFILES_MANIFEST_FILE" in os.environ:
                matching_file = f"{need['docname']}{need['doctype']}"
            else:
                matching_file = f"{prefix}/{need['docname']}{need['doctype']}"

            return f"{matching_file}:{need['lineno']}"
        return None

    def warning_for_option(
        self, need: NeedsInfoType, option: str, msg: str, is_new_check: bool = False
    ):
        full_msg = f"{need['id']}.{option} ({need.get(option, None)}): {msg}"
        location = CheckLogger._location(need, self._prefix)
        self._log_message(full_msg, location, is_new_check)

    def warning_for_link(
        self,
        need: NeedsInfoType,
        option: str,
        problematic_value: str,
        allowed_values: list[str],
        allowed_regex: str,
        is_new_check: bool = False,
    ):
        msg = (
            f"references '{problematic_value}' as '{option}', "
            f"but it must reference {' or '.join(allowed_values)}."
        )
        # Sometimes printing this helps, but most often it just clutters the log.
        # Not sure yet.
        # if allowed_regex:
        #     msg += f" (allowed pattern: `{allowed_regex}`)"

        self.warning_for_need(need, msg, is_new_check=is_new_check)

    def warning_for_need(
        self, need: NeedsInfoType, msg: str, is_new_check: bool = False
    ):
        full_msg = f"{need['id']}: {msg}"
        location = CheckLogger._location(need, self._prefix)
        self._log_message(full_msg, location, is_new_check)

    def _log_message(
        self,
        msg: str,
        location: Location,
        is_new_check: bool = False,
    ):
        if is_new_check:
            self._new_checks.append((msg, location))
            self._info_count += 1
        else:
            self.warning(msg, location)
            self._warning_count += 1

    def info(
        self,
        msg: str,
        location: Location,
    ):
        self._log.info(msg, type="score_metamodel", location=location)

    def warning(
        self,
        msg: str,
        location: Location,
    ):
        self._log.warning(msg, type="score_metamodel", location=location)

    @property
    def warnings(self):
        return self._warning_count

    @property
    def infos(self):
        return self._info_count

    def flush_new_checks(self):
        """Log all new-check messages together at once."""

        def make_header_line(text: str, width: int = 80) -> str:
            """Center a header inside '=' padding so line length stays fixed."""
            text = f" {text} "
            return text.center(width, "=")

        if not self._new_checks:
            return

        warning_header = make_header_line(
            f"{len(self._new_checks)} non-fatal warnings "
            "(will become fatal in the future)"
        )

        logger.info(warning_header)

        for msg, location in self._new_checks:
            self.info(msg, location)
