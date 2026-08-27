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
"""Unit tests for :mod:`score_module_verification_report.directive`.

The directive needs a full Sphinx environment to instantiate, so the pure
helpers and the emitted RST are tested in isolation.
"""

from __future__ import annotations

from src.extensions.score_module_verification_report.directive import (
    _REQUIRED_OPTIONS,
    MOD_VER_REPORT_TEMPLATE,
    NEEDS_TEMPLATE_NAME,
    _join_ids,
    _report_title,
)

# ---------------------------------------------------------------------------
# _join_ids
# ---------------------------------------------------------------------------


def test_join_single_id():
    assert _join_ids("comp__mymod_json") == "comp__mymod_json"


def test_join_normalises_spacing_and_order():
    assert (
        _join_ids("comp__mymod_json,comp__mymod_bits")
        == "comp__mymod_json, comp__mymod_bits"
    )


def test_join_folds_multiline_values_onto_one_line():
    """docutils folds a multi-line option value into one string with newlines.

    They must not survive into the emitted option or the RST breaks.
    """
    result = _join_ids("comp__m_json,\n   comp__m_result\n")
    assert result == "comp__m_json, comp__m_result"
    assert "\n" not in result


def test_join_preserves_version_qualifiers():
    """Sphinx-Needs parses ``id[version==N]`` itself; stripping loses it."""
    assert (
        _join_ids("comp__m_json[version==1], comp__m_result")
        == "comp__m_json[version==1], comp__m_result"
    )


def test_join_skips_empty_entries():
    assert _join_ids("comp__m_json,  ,  ") == "comp__m_json"
    assert _join_ids("") == ""
    assert _join_ids("  ,  ") == ""


def test_join_is_type_agnostic():
    """The same helper serves :components: and :features:."""
    assert _join_ids("feat__one, feat__two") == "feat__one, feat__two"


# ---------------------------------------------------------------------------
# _report_title
# ---------------------------------------------------------------------------


def test_title_derived_from_module_slug():
    assert _report_title("baselibs") == "Baselibs Verification Report"


def test_title_title_cases_multiword_modules():
    assert _report_title("my_module") == "My Module Verification Report"


def test_id_is_never_derived():
    """The need id comes from the author's :id:, never from the module slug."""
    import inspect

    from src.extensions.score_module_verification_report import directive

    source = inspect.getsource(directive.ModuleVerificationReportDirective.run)
    assert 'report_id=self.options["id"]' in source
    assert "mod_vrep__" not in source


# ---------------------------------------------------------------------------
# Required options
# ---------------------------------------------------------------------------


def test_required_options_cover_every_mandatory_field_and_link():
    """One list drives both the option spec and the missing-option error."""
    assert _REQUIRED_OPTIONS == (
        "id",
        "module-id",
        "components",
        "features",
        "safety",
        "security",
        "status",
        "verification-method",
    )


# ---------------------------------------------------------------------------
# Emitted RST
# ---------------------------------------------------------------------------


def _render(**overrides: str) -> str:
    fields = dict(
        title="Demo Verification Report",
        report_id="mod_vrep__demo__report",
        template_name=NEEDS_TEMPLATE_NAME,
        version="1",
        safety="QM",
        security="YES",
        status="valid",
        verification_method="test_and_inspection",
        module_id="mod__demo",
        components="comp__demo_a, comp__demo_b",
        features="feat__demo",
    )
    fields.update(overrides)
    return MOD_VER_REPORT_TEMPLATE.format(**fields)


def test_emitted_need_carries_every_field():
    out = _render()
    for expected in (
        ".. mod_ver_report:: Demo Verification Report",
        ":id: mod_vrep__demo__report",
        ":template: mod_ver_report",
        ":version: 1",
        ":safety: QM",
        ":security: YES",
        ":status: valid",
        ":verification_method: test_and_inspection",
        ":belongs_to: mod__demo",
        ":components: comp__demo_a, comp__demo_b",
        ":features: feat__demo",
    ):
        assert expected in out


def test_emitted_need_is_only_the_need():
    """The body comes from the content template, not from here."""
    out = _render()
    assert "needtable" not in out
    assert "needpie" not in out


def test_every_option_stays_inside_the_directive_block():
    body = [line for line in _render().splitlines() if line.strip()]
    assert body[0].startswith(".. mod_ver_report::")
    assert all(line.startswith("   :") for line in body[1:])
