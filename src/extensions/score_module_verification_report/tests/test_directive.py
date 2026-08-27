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
"""Unit tests for the component-parsing and option-derivation logic
in :mod:`score_module_verification_report.directive`.

The directive requires a full Sphinx environment to instantiate, so we test
the pure derivation rules and the id-parsing helpers in isolation.
"""

from __future__ import annotations

from src.extensions.score_module_verification_report.directive import (
    _MOD_VER_REPORT_LINKS,
    _mod_ver_report_id_and_title,
    _parse_components,
    _parse_features,
)

# ---------------------------------------------------------------------------
# Helpers that mirror the derivation logic in directive.py so we can test
# it without a Sphinx environment.
# ---------------------------------------------------------------------------


def _resolve(
    *,
    option_module_id: str = "",
    option_component_prefix: str = "",
) -> dict:
    """Mirror the derivation logic from ``run()`` and return resolved fields.

    Only ``component_prefix`` is still derived — ``:features:`` is an explicit
    option now, parsed by :func:`_parse_features` like any other id list.
    """
    module_id = option_module_id
    module_short = (
        module_id[len("mod__") :] if module_id.startswith("mod__") else module_id
    )
    component_prefix = option_component_prefix or (
        "comp__" + module_short + "_" if module_short else "comp__"
    )
    return {
        "module_id": module_id,
        "module_short": module_short,
        "component_prefix": component_prefix,
    }


# ---------------------------------------------------------------------------
# _parse_components
# ---------------------------------------------------------------------------


def test_parse_single_id():
    result = _parse_components("comp__mymod_json", "comp__mymod_")
    assert len(result) == 1
    assert result[0]["id"] == "comp__mymod_json"
    assert result[0]["slug"] == "json"
    assert result[0]["title"] == "Json"


def test_parse_multiple_ids():
    result = _parse_components(
        "comp__mymod_json, comp__mymod_bit_manipulation", "comp__mymod_"
    )
    assert len(result) == 2
    assert result[0]["slug"] == "json"
    assert result[1]["slug"] == "bit_manipulation"
    assert result[1]["title"] == "Bit Manipulation"


def test_parse_strips_version_qualifier():
    result = _parse_components(
        "comp__mymod_json[version==1], comp__mymod_result[version==2]",
        "comp__mymod_",
    )
    assert result[0]["id"] == "comp__mymod_json"
    assert result[1]["id"] == "comp__mymod_result"


def test_parse_empty_string_returns_empty():
    assert _parse_components("", "comp__mymod_") == []


def test_parse_whitespace_only_entries_skipped():
    result = _parse_components("comp__mymod_json,  ,  ", "comp__mymod_")
    assert len(result) == 1


def test_parse_without_matching_prefix_uses_full_id_as_slug():
    result = _parse_components("comp__other_json", "comp__mymod_")
    assert result[0]["slug"] == "comp__other_json"
    assert result[0]["title"] == "Comp  Other Json"


def test_parse_no_prefix_uses_full_id():
    result = _parse_components("comp__mymod_json", "")
    assert result[0]["slug"] == "comp__mymod_json"


def test_parse_title_uses_titlecase():
    result = _parse_components("comp__m_memory_shared", "comp__m_")
    assert result[0]["title"] == "Memory Shared"


def test_parse_multiline_string():
    """Continuation lines (as docutils joins them with whitespace) work."""
    result = _parse_components("comp__m_json,\n   comp__m_result\n", "comp__m_")
    assert len(result) == 2


# ---------------------------------------------------------------------------
# Tests — option-only (no config file)
# ---------------------------------------------------------------------------


def test_module_id_option_derives_prefix_only_not_feature():
    """:module-id: drives the component prefix — never the feature."""
    r = _resolve(option_module_id="mod__baselibs")
    assert r["module_id"] == "mod__baselibs"
    assert r["module_short"] == "baselibs"
    assert r["component_prefix"] == "comp__baselibs_"


def test_explicit_component_prefix_option_overrides_derived():
    r = _resolve(option_module_id="mod__baselibs", option_component_prefix="comp__bl_")
    assert r["component_prefix"] == "comp__bl_"


def test_module_id_without_mod_prefix():
    r = _resolve(option_module_id="mymodule")
    assert r["module_short"] == "mymodule"
    assert r["component_prefix"] == "comp__mymodule_"


def test_empty_module_id_gives_generic_prefix():
    r = _resolve()
    assert r["module_id"] == ""
    assert r["component_prefix"] == "comp__"


# ---------------------------------------------------------------------------
# _parse_features
# ---------------------------------------------------------------------------


def test_parse_single_feature():
    result = _parse_features("feat__my_module")
    assert result == [
        {"id": "feat__my_module", "slug": "my_module", "title": "My Module"}
    ]


def test_parse_multiple_features():
    """:features: is a list link, so the option accepts a list."""
    result = _parse_features("feat__one,\n   feat__two\n")
    assert [f["id"] for f in result] == ["feat__one", "feat__two"]
    assert [f["slug"] for f in result] == ["one", "two"]


def test_parse_features_strips_version_qualifier():
    result = _parse_features("feat__demo[version==2]")
    assert result[0]["id"] == "feat__demo"


def test_parse_features_keeps_full_id_without_feat_prefix():
    result = _parse_features("noprefix")
    assert result[0]["id"] == "noprefix"
    assert result[0]["slug"] == "noprefix"


def test_parse_features_empty():
    assert _parse_features("") == []
    assert _parse_features("  ,  ") == []


def test_components_and_features_are_the_mandatory_links():
    """The directive must require exactly the need type's mandatory links."""
    assert _MOD_VER_REPORT_LINKS == ("components", "features")


# ---------------------------------------------------------------------------
# Tests — _mod_ver_report_id_and_title
# ---------------------------------------------------------------------------


def test_mod_ver_report_id_and_title_basic():
    report_id, title = _mod_ver_report_id_and_title("baselibs")
    assert report_id == "mod_vrep__baselibs__report"
    assert title == "Baselibs Verification Report"


def test_mod_ver_report_id_and_title_underscored_slug():
    report_id, title = _mod_ver_report_id_and_title("bit_manipulation")
    assert report_id == "mod_vrep__bit_manipulation__report"
    assert title == "Bit Manipulation Verification Report"
