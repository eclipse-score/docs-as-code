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
import pytest
from attribute_plugin import add_test_properties  # type: ignore[import-untyped]
from sphinx.application import Sphinx
from sphinx_needs.data import NeedsView
from sphinx_needs.need_item import NeedItem

from src.extensions.score_metamodel import CheckLogger
from src.extensions.score_metamodel.__init__ import (
    graph_checks,
    local_checks,
    parse_checks_filter,
)
from src.extensions.score_metamodel.tests import need


def dummy_local_check(app: Sphinx, need: NeedItem, log: CheckLogger) -> None:
    pass


def dummy_graph_check(app: Sphinx, needs_view: NeedsView, log: CheckLogger) -> None:
    pass


@pytest.fixture(autouse=True)
def setup_checks():
    """Reset and set test-only local and graph checks before each test."""
    local_checks.clear()
    graph_checks.clear()
    local_checks.append(dummy_local_check)
    graph_checks.append(dummy_graph_check)


@add_test_properties(
    partially_verifies=["tool_req__docs_metamodel"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_returns_empty_list_when_filter_is_empty():
    """Return an empty list if no filter string is provided."""
    assert parse_checks_filter("") == []


@add_test_properties(
    partially_verifies=["tool_req__docs_metamodel"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_returns_valid_checks():
    """Return the provided valid check names."""
    result = parse_checks_filter("dummy_local_check,dummy_graph_check")
    assert result == ["dummy_local_check", "dummy_graph_check"]


@add_test_properties(
    partially_verifies=["tool_req__docs_metamodel"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_strips_whitespace():
    """Remove surrounding spaces from each check name."""
    result = parse_checks_filter(" dummy_local_check , dummy_graph_check ")
    assert result == ["dummy_local_check", "dummy_graph_check"]


@add_test_properties(
    partially_verifies=["tool_req__docs_metamodel"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_raises_assertion_for_invalid_check():
    """Raise AssertionError if a check name is unknown."""
    with pytest.raises(AssertionError) as exc_info:
        parse_checks_filter("non_existing_check")
    assert "non_existing_check" in str(exc_info.value)
    assert "not one of the defined local or graph checks" in str(exc_info.value)


# =============================================================================
# Tests for the need() helper function
# =============================================================================


class TestNeedHelper:
    """Tests for the need() convenience function that creates NeedItem objects."""

    def test_default_values(self):
        """Verify default values are set when no arguments provided."""
        n = need()
        assert n["id"] == "test_need"
        assert n["type"] == "requirement"
        assert n["title"] == ""
        assert n["status"] is None
        assert n["tags"] == []
        assert n["collapse"] is False
        assert n["hide"] is False

    def test_custom_values_override_defaults(self):
        """Verify custom values override the defaults."""
        n = need(
            id="custom_id",
            type="custom_type",
            title="Custom Title",
            status="valid",
            tags=["tag1", "tag2"],
        )
        assert n["id"] == "custom_id"
        assert n["type"] == "custom_type"
        assert n["title"] == "Custom Title"
        assert n["status"] == "valid"
        assert n["tags"] == ["tag1", "tag2"]

    def test_link_fields_extracted(self):
        """Verify link fields are extracted and accessible via .get()."""
        n = need(
            complies=["std_req_1", "std_req_2"],
            input=["wp_input_1"],
            output=["wp_output_1", "wp_output_2"],
            contains=["item_1"],
            satisfies=["req_1"],
        )
        # Links should be accessible via .get() on NeedItem
        assert n.get("complies", []) == ["std_req_1", "std_req_2"]
        assert n.get("input", []) == ["wp_input_1"]
        assert n.get("output", []) == ["wp_output_1", "wp_output_2"]
        assert n.get("contains", []) == ["item_1"]
        assert n.get("satisfies", []) == ["req_1"]

    def test_extra_fields_in_extras(self):
        """Verify extra fields (not core, not links) go into extras."""
        n = need(
            reqtype="Functional",
            security="YES",
            custom_field="custom_value",
        )
        # Extra fields should be accessible via .get()
        assert n.get("reqtype") == "Functional"
        assert n.get("security") == "YES"
        assert n.get("custom_field") == "custom_value"

    def test_empty_links_not_in_kwargs(self):
        """Verify that link keys not provided default to empty list."""
        n = need()
        # When link not provided, should return empty list
        assert n.get("complies", []) == []
        assert n.get("input", []) == []
        assert n.get("output", []) == []

    def test_combined_core_links_and_extras(self):
        """Verify a need with core, link, and extra fields works correctly."""
        n = need(
            id="combined_need",
            type="workflow",
            status="draft",
            input=["input_wp"],
            output=["output_wp"],
            custom_attr="custom_value",
        )
        # Core fields
        assert n["id"] == "combined_need"
        assert n["type"] == "workflow"
        assert n["status"] == "draft"
        # Link fields
        assert n.get("input", []) == ["input_wp"]
        assert n.get("output", []) == ["output_wp"]
        # Extra fields
        assert n.get("custom_attr") == "custom_value"
