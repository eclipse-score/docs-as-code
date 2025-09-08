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
from sphinx_needs.data import NeedsInfoType, NeedsView

from src.extensions.score_metamodel import CheckLogger
from src.extensions.score_metamodel.__init__ import (
    graph_checks,
    local_checks,
    parse_checks_filter,
)


def dummy_local_check(app: Sphinx, need: NeedsInfoType, log: CheckLogger) -> None:
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
