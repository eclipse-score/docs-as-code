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
"""Tests for the metamodel lint: permissive mandatory regex detection."""

from attribute_plugin import add_test_properties  # type: ignore[import-untyped]
from score_metamodel import ScoreNeedType
from score_metamodel.yaml_parser import validate_mandatory_regexes


def _need_type(
    directive: str,
    mandatory_options: dict[str, str] | None = None,
) -> ScoreNeedType:
    """Build a minimal ScoreNeedType for testing."""
    return {
        "directive": directive,
        "title": directive,
        "prefix": f"{directive}__",
        "tags": [],
        "parts": 2,
        "mandatory_options": mandatory_options or {},
        "optional_options": {},
        "mandatory_links_str": {},
        "mandatory_links": {},
        "optional_links_str": {},
        "optional_links": {},
    }


@add_test_properties(
    partially_verifies=["tool_req__docs_saf_attrs_mandatory"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_no_issues_for_strict_regexes():
    """Regexes that reject the empty string are not flagged."""
    types = [
        _need_type("feat_saf_fmea", {"fault_id": "^.+$", "status": "^(valid)$"}),
        _need_type("comp_saf_fmea", {"fault_id": "^.+$", "status": "^(valid)$"}),
    ]
    assert validate_mandatory_regexes(types) == []


@add_test_properties(
    partially_verifies=["tool_req__docs_saf_attrs_mandatory"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_flags_wildcard_star():
    """^.*$ matches the empty string and must be flagged."""
    types = [
        _need_type("feat_saf_fmea", {"fault_id": "^.*$"}),
    ]
    issues = validate_mandatory_regexes(types)
    assert len(issues) == 1
    directive, option, pattern = issues[0]
    assert directive == "feat_saf_fmea"
    assert option == "fault_id"
    assert pattern == "^.*$"


@add_test_properties(
    partially_verifies=["tool_req__docs_saf_attrs_mandatory"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_flags_bare_wildcard():
    """A bare .* also matches the empty string."""
    types = [
        _need_type("comp_saf_fmea", {"fault_id": ".*"}),
    ]
    issues = validate_mandatory_regexes(types)
    assert len(issues) == 1
    assert issues[0][0] == "comp_saf_fmea"


@add_test_properties(
    partially_verifies=["tool_req__docs_saf_attrs_mandatory"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_flags_zero_or_more_quantifier():
    """^[0-9]*$ matches the empty string (zero digits)."""
    types = [
        _need_type("doc", {"version": "^[0-9]*$"}),
    ]
    issues = validate_mandatory_regexes(types)
    assert len(issues) == 1
    assert issues[0][1] == "version"


@add_test_properties(
    partially_verifies=["tool_req__docs_saf_attrs_mandatory"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_flags_empty_string_only_regex():
    """^$ matches only the empty string — still permissive for mandatory."""
    types = [
        _need_type("doc", {"name": "^$"}),
    ]
    issues = validate_mandatory_regexes(types)
    assert len(issues) == 1


@add_test_properties(
    partially_verifies=["tool_req__docs_saf_attrs_mandatory"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_flags_multiple_issues_in_one_type():
    """Multiple permissive mandatory options in one type are all flagged."""
    types = [
        _need_type(
            "review_header",
            {
                "reviewers": "^.*$",
                "approvers": "^.*$",
                "hash": "^.*$",
            },
        ),
    ]
    issues = validate_mandatory_regexes(types)
    assert len(issues) == 3
    flagged_options = {issue[1] for issue in issues}
    assert flagged_options == {"reviewers", "approvers", "hash"}


@add_test_properties(
    partially_verifies=["tool_req__docs_saf_attrs_mandatory"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_flags_across_multiple_types():
    """Issues from different types are all collected."""
    types = [
        _need_type("feat_saf_fmea", {"fault_id": "^.*$"}),
        _need_type("comp_saf_fmea", {"fault_id": "^.*$"}),
    ]
    issues = validate_mandatory_regexes(types)
    assert len(issues) == 2
    directives = {issue[0] for issue in issues}
    assert directives == {"feat_saf_fmea", "comp_saf_fmea"}


@add_test_properties(
    partially_verifies=["tool_req__docs_saf_attrs_mandatory"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_optional_options_not_checked():
    """Only mandatory options are checked, not optional ones."""
    types = [
        _need_type(
            "doc",
            mandatory_options={"status": "^(valid)$"},
        ),
    ]
    # This would be permissive if checked, but it's optional
    types[0]["optional_options"] = {"author": "^.*$"}
    assert validate_mandatory_regexes(types) == []


@add_test_properties(
    partially_verifies=["tool_req__docs_saf_attrs_mandatory"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_accepts_dict_input():
    """The function also accepts a dict of need types."""
    types = {
        "feat_saf_fmea": _need_type("feat_saf_fmea", {"fault_id": "^.*$"}),
    }
    issues = validate_mandatory_regexes(types)
    assert len(issues) == 1
    assert issues[0][0] == "feat_saf_fmea"
