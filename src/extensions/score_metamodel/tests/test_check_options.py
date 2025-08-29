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

from typing import TypedDict
from unittest.mock import Mock

import pytest
from attribute_plugin import add_test_properties
from score_metamodel.checks.check_options import (
    check_extra_options,
    check_options,
)
from score_metamodel.tests import fake_check_logger, need
from sphinx.application import Sphinx


class NeedTypeDict(TypedDict, total=False):
    directive: str
    mandatory_options: dict[str, str | int] | None
    opt_opt: dict[str, str] | None


class TestCheckOptions:
    NEED_TYPE_INFO: list[NeedTypeDict] = [
        {
            "directive": "tool_req",
            "mandatory_options": {
                "id": "^tool_req__.*$",
                "some_required_option": "^some_value__.*$",
            },
        }
    ]
    NEED_TYPE_INFO_WITH_OPT_OPT: list[NeedTypeDict] = [
        {
            "directive": "tool_req",
            "mandatory_options": {
                "id": "^tool_req__.*$",
                "some_required_option": "^some_value__.*$",
            },
            "opt_opt": {
                "some_optional_option": "^some_value__.*$",
            },
        }
    ]

    NEED_TYPE_INFO_WITHOUT_MANDATORY_OPTIONS: list[NeedTypeDict] = [
        {
            "directive": "workflow",
            "mandatory_options": None,
        },
    ]

    NEED_TYPE_INFO_WITH_INVALID_OPTION_TYPE: list[NeedTypeDict] = [
        {
            "directive": "workflow",
            "mandatory_options": {
                "id": "^wf_req__.*$",
                "some_invalid_option": 42,
            },
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
        # Expect that the checks pass
        check_options(app, need_1, logger)
        logger.assert_warning(
            "no type info defined for semantic check.",
            expect_location=False,
        )

    @add_test_properties(
        partially_verifies=["tool_req__docs_metamodel"],
        test_type="requirements-based",
        derivation_technique="requirements-analysis",
    )
    def test_unknown_directive_extra_option(self):
        """Given a need an unknown/undefined type, should raise an error"""
        need_1 = need(
            target_id="tool_req__001",
            type="unknown_type",
            id="tool_req__001",
            some_required_option="some_value__001",
            docname=None,
            lineno=None,
        )

        logger = fake_check_logger()
        app = Mock(spec=Sphinx)
        app.config = Mock()
        app.config.needs_types = self.NEED_TYPE_INFO
        # Expect that the checks pass
        check_extra_options(app, need_1, logger)
        logger.assert_warning(
            "no type info defined for semantic check.",
            expect_location=False,
        )

    @add_test_properties(
        partially_verifies=["tool_req__docs_metamodel"],
        test_type="requirements-based",
        derivation_technique="requirements-analysis",
    )
    def test_missing_mandatory_options_info(self):
        """
        Given any need of known type with missing mandatory options info
        it should raise an error
        """
        need_1 = need(
            target_id="wf_req__001",
            id="wf_req__001",
            type="workflow",
            some_required_option=None,
            docname=None,
            lineno=None,
        )

        logger = fake_check_logger()
        app = Mock(spec=Sphinx)
        app.config = Mock()
        app.config.needs_types = self.NEED_TYPE_INFO_WITHOUT_MANDATORY_OPTIONS
        app.config.allowed_external_prefixes = []
        # Expect that the checks pass
        check_options(app, need_1, logger)
        logger.assert_warning(
            "no type info defined for semantic check.",
            expect_location=False,
        )

    @add_test_properties(
        partially_verifies=["tool_req__docs_metamodel"],
        test_type="requirements-based",
        derivation_technique="requirements-analysis",
    )
    def test_invalid_option_type(self):
        """
        Given any need of known type with missing mandatory options info
        it should raise an error
        """
        need_1 = need(
            target_id="wf_req__001",
            id="wf_req__001",
            type="workflow",
            some_invalid_option="42",
            docname=None,
            lineno=None,
        )

        logger = fake_check_logger()
        app = Mock(spec=Sphinx)
        app.config = Mock()
        app.config.needs_types = self.NEED_TYPE_INFO_WITH_INVALID_OPTION_TYPE
        app.config.allowed_external_prefixes = []
        # Expect that the checks pass
        check_options(app, need_1, logger)
        logger.assert_warning(
            "pattern `42` is not a valid regex pattern.",
            expect_location=False,
        )

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
        check_extra_options(app, need_1, logger)

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

        with pytest.raises(ValueError, match="Only Strings are allowed"):
            check_options(app, need_1, logger)
