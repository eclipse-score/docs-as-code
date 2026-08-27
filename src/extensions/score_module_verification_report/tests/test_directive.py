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
"""Unit tests for the option parsing and id derivation in
:mod:`score_module_verification_report.directive`.

The directive needs a full Sphinx environment to instantiate, so the pure
helpers are tested in isolation.
"""

from __future__ import annotations

from src.extensions.score_module_verification_report.directive import (
    _MOD_VER_REPORT_LINKS,
    _MOD_VER_REPORT_OPTIONS,
    _mod_ver_report_id_and_title,
    _parse_ids,
)

# ---------------------------------------------------------------------------
# _parse_ids
# ---------------------------------------------------------------------------


def test_parse_single_id():
    assert _parse_ids("comp__mymod_json") == ["comp__mymod_json"]


def test_parse_multiple_ids_preserves_order():
    result = _parse_ids("comp__mymod_json, comp__mymod_bit_manipulation")
    assert result == ["comp__mymod_json", "comp__mymod_bit_manipulation"]


def test_parse_handles_multiline_values():
    """docutils folds a multi-line option value into one string."""
    assert _parse_ids("comp__m_json,\n   comp__m_result\n") == [
        "comp__m_json",
        "comp__m_result",
    ]


def test_parse_strips_version_qualifier():
    result = _parse_ids("comp__m_json[version==1], comp__m_result[version==2]")
    assert result == ["comp__m_json", "comp__m_result"]


def test_parse_skips_empty_entries():
    assert _parse_ids("comp__m_json,  ,  ") == ["comp__m_json"]
    assert _parse_ids("") == []
    assert _parse_ids("  ,  ") == []


def test_parse_is_type_agnostic():
    """The same parser serves :components: and :features:."""
    assert _parse_ids("feat__one, feat__two") == ["feat__one", "feat__two"]


# ---------------------------------------------------------------------------
# _mod_ver_report_id_and_title
# ---------------------------------------------------------------------------


def test_id_and_title_derived_from_module_slug():
    need_id, title = _mod_ver_report_id_and_title("baselibs")
    assert need_id == "mod_vrep__baselibs__report"
    assert title == "Baselibs Verification Report"


def test_id_keeps_exactly_two_separators_for_multiword_modules():
    """``mod_ver_report`` declares ``parts: 3`` — no more, no less."""
    need_id, title = _mod_ver_report_id_and_title("my_module")
    assert need_id.count("__") == 2
    assert need_id == "mod_vrep__my_module__report"
    assert title == "My Module Verification Report"


# ---------------------------------------------------------------------------
# Required options
# ---------------------------------------------------------------------------


def test_components_and_features_are_the_mandatory_links():
    """The directive must require exactly the need type's mandatory links."""
    assert _MOD_VER_REPORT_LINKS == ("components", "features")


def test_mandatory_options_match_the_need_type():
    assert _MOD_VER_REPORT_OPTIONS == (
        "safety",
        "security",
        "status",
        "verification-method",
    )
