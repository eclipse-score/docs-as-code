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
    parse_milestone,
    validate_links,
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
        partially_verifies=["tool_req__docs_common_attr_security"],
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
        partially_verifies=["tool_req__docs_common_attr_description"],
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
        # Expect that the checks pass
        check_extra_options(app, need_1, cast(CheckLogger, logger))

        logger.assert_warning(
            "has these extra options: `other_option`.",
            expect_location=False,
        )


def test_milestone_parsing():
    assert parse_milestone("v0.5") == (0, 5, 0)
    assert parse_milestone("v1.0") == (1, 0, 0)
    assert parse_milestone("v1.0.1") == (1, 0, 1)


class TestValidateLinks:
    """Tests for validate_links() — specifically the prefix-stripping bug (#588)."""

    NEED_TYPE_WITH_LINK_BY_NAME: ScoreNeedType = {
        "title": "Test Type",
        "prefix": "TT",
        "tags": [],
        "parts": 1,
        "directive": "test_type",
        "mandatory_options": {
            "id": "^test_type__.*$",
            "status": "^(draft|valid)$",
        },
        "optional_options": {},
        "mandatory_links": {},
        "optional_links": {
            "satisfies": ["product"],
        },
    }

    NEED_TYPE_WITH_LINK_BY_REGEX: ScoreNeedType = {
        "title": "Test Type",
        "prefix": "TT",
        "tags": [],
        "parts": 1,
        "directive": "test_type",
        "mandatory_options": {
            "id": "^test_type__.*$",
            "status": "^(draft|valid)$",
        },
        "optional_options": {},
        "mandatory_links": {},
        "optional_links": {
            "satisfies": ["^product__.*$"],
        },
    }

    def test_link_matches_by_type_name_no_prefix(self):
        """A link value that starts with the type name should pass validation."""
        need_1 = need(
            id="test_type__001",
            type="test_type",
            satisfies="product__foo",
        )
        logger = fake_check_logger()
        validate_links(
            cast(CheckLogger, logger),
            self.NEED_TYPE_WITH_LINK_BY_NAME,
            need_1,
        )
        logger.assert_no_warnings()

    def test_link_with_uppercase_prefix_no_longer_stripped(self):
        """
        After the fix for #588, uppercase prefixes are no longer stripped.
        P_FOO stays as P_FOO and correctly fails to match the 'product' type pattern.
        """
        need_1 = need(
            id="test_type__001",
            type="test_type",
            satisfies="P_FOO",
        )
        logger = fake_check_logger()
        validate_links(
            cast(CheckLogger, logger),
            self.NEED_TYPE_WITH_LINK_BY_NAME,
            need_1,
        )
        # P_FOO is preserved as-is (no stripping) and doesn't match ^product__
        logger.assert_warning("references 'P_FOO' as 'satisfies'")

    def test_link_with_uppercase_prefix_not_stripped_for_regex(self):
        """
        After the fix for #588, uppercase prefixes are no longer stripped.
        P_product__foo stays as P_product__foo and does NOT match ^product__.*$
        because the P_ prefix is preserved.
        """
        need_1 = need(
            id="test_type__001",
            type="test_type",
            satisfies="P_product__foo",
        )
        logger = fake_check_logger()
        validate_links(
            cast(CheckLogger, logger),
            self.NEED_TYPE_WITH_LINK_BY_REGEX,
            need_1,
        )
        # P_product__foo is preserved as-is and doesn't match ^product__.*$
        logger.assert_warning("references 'P_product__foo' as 'satisfies'")

    def test_link_without_prefix_matches_by_name(self):
        """A link value without any prefix that starts with the type name passes."""
        need_1 = need(
            id="test_type__001",
            type="test_type",
            satisfies="product__bar",
        )
        logger = fake_check_logger()
        validate_links(
            cast(CheckLogger, logger),
            self.NEED_TYPE_WITH_LINK_BY_NAME,
            need_1,
        )
        logger.assert_no_warnings()

    def test_link_not_matching_any_type_warns(self):
        """A link value that doesn't match any allowed type should warn."""
        need_1 = need(
            id="test_type__001",
            type="test_type",
            satisfies="unknown__thing",
        )
        logger = fake_check_logger()
        validate_links(
            cast(CheckLogger, logger),
            self.NEED_TYPE_WITH_LINK_BY_NAME,
            need_1,
        )
        logger.assert_warning("references 'unknown__thing' as 'satisfies'")
