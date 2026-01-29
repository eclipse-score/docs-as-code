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
from typing import Any, cast
from unittest.mock import MagicMock

import pytest
from sphinx.util.logging import SphinxLoggerAdapter
from sphinx_needs.data import NeedsInfoType
from sphinx_needs.need_item import (
    NeedItem,
    NeedItemSourceUnknown,
    NeedsContent,
)

from src.extensions.score_metamodel import CheckLogger


def fake_check_logger():
    """Creates a CheckLogger with a mocked backend."""

    class FakeCheckLogger(CheckLogger):
        def __init__(self):
            self._mock_logger = MagicMock(spec=SphinxLoggerAdapter)
            self._mock_logger.warning = MagicMock()
            self._mock_logger.info = MagicMock()
            app_path = MagicMock()
            super().__init__(self._mock_logger, app_path)

        def assert_no_warnings(self):
            if self.warnings:
                warnings = "\n".join(
                    f"* {call}" for call in self._mock_logger.warning.call_args_list
                )
                pytest.fail(f"Expected no warnings, but got:\n{warnings}")

        def assert_no_infos(self):
            if self.infos:
                infos = "\n".join(
                    f"* {call}" for call in self._mock_logger.info.call_args_list
                )
                pytest.fail(f"Expected no infos, but got:\n{infos}")

        def assert_warning(self, expected_substring: str, expect_location: bool = True):
            """
            Assert that the logger warning was called exactly once with a message
            containing a specific substring.

            This also verifies that the defaults from need() are used correctly.
            So you must use need() to create the need object that is passed
            to the checks.
            """
            self._mock_logger.warning.assert_called_once()

            # Retrieve the call arguments
            args, kwargs = self._mock_logger.warning.call_args
            log_message = args[0]

            assert expected_substring in log_message, (
                "Expected substring "
                f"'{expected_substring}' "
                f"not found in log message: '{log_message}'"
            )

            # All our checks shall report themselves as score_metamodel checks
            assert kwargs["type"] == "score_metamodel"

            if expect_location:
                assert kwargs["location"] == "docname.rst:42"

        def assert_info(self, expected_substring: str, expect_location: bool = True):
            """
            Assert that the logger info was called exactly once with a message
            containing a specific substring.

            This also verifies that the defaults from need() are used correctly.
            So you must use need() to create the need object that is passed
            to the checks.
            """
            self._mock_logger.info.assert_called_once()

            # Retrieve the call arguments
            args, kwargs = self._mock_logger.info.call_args
            log_message = args[0]

            assert expected_substring in log_message, (
                "Expected substring "
                f"'{expected_substring}' "
                f"not found in log message: '{log_message}'"
            )

            # All our checks shall report themselves as score_metamodel checks
            assert kwargs["type"] == "score_metamodel"

            if expect_location:
                assert kwargs["location"] == "docname.rst:42"

    return FakeCheckLogger()


def need(**kwargs: Any) -> NeedItem:
    """Convenience function to create a NeedItem object with some defaults."""

    # Extract links (any list field that's not a core field)
    link_keys = {
        "links",
    }
    links = {k: kwargs.pop(k, []) for k in list(link_keys) if k in kwargs}

    # Set defaults for core fields
    kwargs.setdefault("id", "test_need")
    kwargs.setdefault("type", "requirement")
    kwargs.setdefault("title", "")
    kwargs.setdefault("status", None)
    kwargs.setdefault("tags", [])
    kwargs.setdefault("collapse", False)
    kwargs.setdefault("hide", False)
    kwargs.setdefault("layout", None)
    kwargs.setdefault("style", None)
    kwargs.setdefault("external_css", "")
    kwargs.setdefault("type_name", "")
    kwargs.setdefault("type_prefix", "")
    kwargs.setdefault("type_color", "")
    kwargs.setdefault("type_style", "")
    kwargs.setdefault("constraints", [])
    kwargs.setdefault("arch", {})
    kwargs.setdefault("sections", ())
    kwargs.setdefault("signature", None)
    kwargs.setdefault("has_dead_links", False)
    kwargs.setdefault("has_forbidden_dead_links", False)

    # Build core dict (only NeedsInfoType fields)
    core_keys = set(NeedsInfoType.__annotations__.keys())
    core = cast(NeedsInfoType, {k: kwargs[k] for k in core_keys})

    # Source/content keys to exclude from extras
    source_content_keys = {
        "docname",
        "lineno",
        "lineno_content",
        "external_url",
        "is_import",
        "is_external",
        "doctype",
        "content",
        "pre_content",
        "post_content",
    }

    # Extract extras (any remaining kwargs not in core or source/content)
    extras = {
        k: v
        for k, v in kwargs.items()
        if k not in core_keys and k not in source_content_keys
    }

    # Create source
    source = NeedItemSourceUnknown(
        docname=kwargs.get("docname", "docname"),
        lineno=kwargs.get("lineno", 42),
        lineno_content=kwargs.get("lineno_content"),
    )

    # Create content
    content = NeedsContent(
        doctype=kwargs.get("doctype", ".rst"),
        content=kwargs.get("content", ""),
        pre_content=kwargs.get("pre_content"),
        post_content=kwargs.get("post_content"),
    )

    return NeedItem(
        source=source,
        content=content,
        core=core,
        extras=extras,
        links=links,
    )
