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

from typing import cast
from unittest.mock import Mock

import pytest
from attribute_plugin import add_test_properties  # type: ignore[import-untyped]
from score_metamodel import CheckLogger, ScoreNeedType
from score_metamodel.checks.check_options import (
    check_extra_options,
    check_options,
)
from score_metamodel.tests import fake_check_logger, need
from sphinx.application import Sphinx  # type: ignore[import-untyped]


class TestCheckOptions:
    NEED_TYPE_INFO: list[ScoreNeedType] = [
        {
            "title": "Test Type",
            "prefix": "TR",
            "tags": [],
            "parts": 1,
            "directive": "tool_req",
            "mandatory_options": {
                "id": "^tool_req__.*$",
                "some_required_option": "^some_value__.*$",
            },
            "optional_options": {},
            "mandatory_links": {},
            "optional_links": {},
        }
    ]
    NEED_TYPE_INFO_WITH_OPT_OPT: list[ScoreNeedType] = [
        {
            "title": "Test Type",
            "prefix": "TR",
            "tags": [],
            "parts": 1,
            "directive": "tool_req",
            "mandatory_options": {
                "id": "^tool_req__.*$",
                "some_required_option": "^some_value__.*$",
            },
            "optional_options": {
                "some_optional_option": "^some_value__.*$",
            },
            "mandatory_links": {},
            "optional_links": {},
        }
    ]

    @add_test_properties(
        partially_verifies=["tool_req__docs_metamodel"],
        test_type="requirements-based",
        derivation_technique="requirements-analysis",
    )
    def test_unknown_directive(self):
        """Given a need with an unknown type, should raise an error"""
        need_1 = need(
            target_id="tool_req__001",
            id="tool_req__001",
            type="unknown_type",
            some_required_option="some_value__001",
            docname=None,
            lineno=None,
        )

        logger = fake_check_logger()
        app = Mock(spec=Sphinx)
        app.config = Mock()
        app.config.needs_types = self.NEED_TYPE_INFO

        with pytest.raises(ValueError):
            check_options(app, need_1, cast(CheckLogger, logger))

    @add_test_properties(
        partially_verifies=["tool_req__docs_metamodel"],
        test_type="requirements-based",
        derivation_technique="requirements-analysis",
    )
    def test_unknown_option_present_in_neither_req_opt_neither_opt_opt(self):
        """
        Given a need with an option that is not listed
        in the required and optional options
        """
        need_1 = need(
            target_id="tool_req__001",
            id="tool_req__0011",
            type="tool_req",
            some_required_option="some_value__001",
            some_optional_option="some_value__001",
            other_option="some_other_value",
            docname=None,
            lineno=None,
        )

        logger = fake_check_logger()
        app = Mock(spec=Sphinx)
        app.config = Mock()
        app.config.needs_types = self.NEED_TYPE_INFO_WITH_OPT_OPT
        app.config.allowed_external_prefixes = []
        # Expect that the checks pass
        check_extra_options(app, need_1, cast(CheckLogger, logger))

        logger.assert_warning(
            "has these extra options: `other_option`.",
            expect_location=False,
        )

    @add_test_properties(
        partially_verifies=["tool_req__docs_metamodel"],
        test_type="requirements-based",
        derivation_technique="requirements-analysis",
    )
    def test_invalid_option_value_type_raises_value_error(self):
        """Given a need with an option of wrong type (list with non-str)"""
        need_1 = need(
            target_id="tool_req__002",
            id="tool_req__002",
            type="tool_req",
            some_required_option=123,
            docname=None,
            lineno=None,
        )

        logger = fake_check_logger()
        app = Mock(spec=Sphinx)
        app.config = Mock()
        app.config.needs_types = self.NEED_TYPE_INFO
        app.config.allowed_external_prefixes = []

        with pytest.raises(ValueError, match="Only Strings are allowed"):  # type: ignore[attr-defined]
            check_options(app, need_1, cast(CheckLogger, logger))
