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
"""Unit tests for :mod:`score_module_verification_report.rendering`."""

from __future__ import annotations

from src.extensions.score_module_verification_report.rendering import (
    render_mod_ver_report,
)

_ARGS = dict(
    module_id="mod__demo",
    report_id="mod_vrep__demo__report",  # supplied by the directive's :id:
    title="Demo Verification Report",
    safety="QM",
    security="YES",
    status="valid",
    verification_method="test_and_inspection",
)


def test_render_mod_ver_report_emits_all_mandatory_fields() -> None:
    out = render_mod_ver_report(
        components=["comp__demo_a", "comp__demo_b"],
        features=["feat__demo"],
        **_ARGS,
    )
    assert ".. mod_ver_report:: Demo Verification Report" in out
    assert ":id: mod_vrep__demo__report" in out
    assert ":version: 1" in out
    assert ":safety: QM" in out
    assert ":security: YES" in out
    assert ":status: valid" in out
    assert ":verification_method: test_and_inspection" in out
    assert ":belongs_to: mod__demo" in out
    assert ":components: comp__demo_a, comp__demo_b" in out
    assert ":features: feat__demo" in out


def test_render_mod_ver_report_selects_the_needs_template() -> None:
    """The body comes from the ``mod_ver_report`` content template."""
    out = render_mod_ver_report(
        components=["comp__demo_a"], features=["feat__demo"], **_ARGS
    )
    assert ":template: mod_ver_report" in out
    # The directive emits the need only — no rendered body.
    assert "needtable" not in out
    assert "needpie" not in out


def test_render_mod_ver_report_block_is_self_contained() -> None:
    """Every option must sit inside the directive block."""
    out = render_mod_ver_report(
        components=["comp__demo_a"], features=["feat__demo"], **_ARGS
    )
    assert out.endswith(
        ":belongs_to: mod__demo\n"
        "   :components: comp__demo_a\n"
        "   :features: feat__demo\n\n"
    )
    body = [ln for ln in out.splitlines() if ln.strip()]
    assert body[0].startswith(".. mod_ver_report::")
    assert all(ln.startswith("   :") for ln in body[1:])
