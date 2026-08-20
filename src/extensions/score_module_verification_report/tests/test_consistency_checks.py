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
"""Unit tests for :mod:`score_module_verification_report.consistency_checks`."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.extensions.score_module_verification_report.consistency_checks import (
    check_consistency,
    init_registry,
    merge_registry,
    purge_registry,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_env(registry: dict | None = None) -> MagicMock:
    env = MagicMock()
    if registry is not None:
        env.module_verification_report_registry = registry
    else:
        del env.module_verification_report_registry
        # hasattr returns False for deleted attributes on MagicMock
        type(env).__contains__ = MagicMock(return_value=False)
    return env


def _make_app(registry: dict | None = None) -> MagicMock:
    app = MagicMock()
    app.env = MagicMock()
    if registry is not None:
        app.env.module_verification_report_registry = registry
    else:
        # Remove attribute so getattr returns default
        if hasattr(app.env, "module_verification_report_registry"):
            del app.env.module_verification_report_registry
    return app


def _registry_entry(
    module_id: str = "mod__m",
    feature_id: str = "feat__m",
    comp_ids: list[str] | None = None,
    docname: str = "reporting/index",
) -> dict:
    return {
        "docname": docname,
        "feature_id": feature_id,
        "comp_ids": comp_ids or ["comp__m_a"],
    }


# ---------------------------------------------------------------------------
# Lifecycle: init_registry
# ---------------------------------------------------------------------------


def test_init_registry_creates_dict_when_absent() -> None:
    env = MagicMock(spec=[])  # no attributes at all
    init_registry(None, env, [])
    assert env.module_verification_report_registry == {}


def test_init_registry_keeps_existing_dict() -> None:
    env = MagicMock(spec=["module_verification_report_registry"])
    env.module_verification_report_registry = {"mod__m": {"docname": "x"}}
    init_registry(None, env, [])
    assert "mod__m" in env.module_verification_report_registry


# ---------------------------------------------------------------------------
# Lifecycle: purge_registry
# ---------------------------------------------------------------------------


def test_purge_registry_removes_matching_docname() -> None:
    env = MagicMock()
    env.module_verification_report_registry = {
        "mod__m": _registry_entry(docname="docs/report"),
        "mod__other": _registry_entry(module_id="mod__other", docname="other/report"),
    }
    purge_registry(None, env, "docs/report")
    assert "mod__m" not in env.module_verification_report_registry
    assert "mod__other" in env.module_verification_report_registry


def test_purge_registry_noop_when_registry_missing() -> None:
    env = MagicMock(spec=[])
    purge_registry(None, env, "any/docname")  # must not raise


def test_purge_registry_noop_when_docname_unknown() -> None:
    env = MagicMock()
    env.module_verification_report_registry = {"mod__m": _registry_entry(docname="x")}
    purge_registry(None, env, "not_there")
    assert "mod__m" in env.module_verification_report_registry


# ---------------------------------------------------------------------------
# Lifecycle: merge_registry
# ---------------------------------------------------------------------------


def test_merge_registry_copies_other_entries() -> None:
    env = MagicMock(spec=["module_verification_report_registry"])
    env.module_verification_report_registry = {}
    other = MagicMock()
    other.module_verification_report_registry = {"mod__m": _registry_entry()}
    merge_registry(None, env, [], other)
    assert "mod__m" in env.module_verification_report_registry


def test_merge_registry_creates_dict_when_env_missing() -> None:
    env = MagicMock(spec=[])
    other = MagicMock(spec=[])  # other also has no registry
    merge_registry(None, env, [], other)
    assert env.module_verification_report_registry == {}


# ---------------------------------------------------------------------------
# check_consistency — early-exit paths
# ---------------------------------------------------------------------------


def test_noop_when_exception_set() -> None:
    app = MagicMock()
    with patch(
        "src.extensions.score_module_verification_report.consistency_checks.logger"
    ) as mock_logger:
        check_consistency(app, exception=RuntimeError("boom"))
    mock_logger.warning.assert_not_called()


def test_noop_when_registry_empty() -> None:
    app = MagicMock()
    app.env.module_verification_report_registry = {}
    with patch(
        "src.extensions.score_module_verification_report.consistency_checks.logger"
    ) as mock_logger:
        check_consistency(app, exception=None)
    mock_logger.warning.assert_not_called()


def test_noop_when_registry_missing() -> None:
    app = MagicMock()
    app.env = MagicMock(spec=[])  # no registry attribute
    with patch(
        "src.extensions.score_module_verification_report.consistency_checks.logger"
    ) as mock_logger:
        check_consistency(app, exception=None)
    mock_logger.warning.assert_not_called()


def test_noop_when_needs_unavailable() -> None:
    app = MagicMock()
    app.env.module_verification_report_registry = {"mod__m": _registry_entry()}
    with (
        patch(
            "src.extensions.score_module_verification_report.consistency_checks._needs_view",
            return_value=None,
        ),
        patch(
            "src.extensions.score_module_verification_report.consistency_checks.logger"
        ) as mock_logger,
    ):
        check_consistency(app, exception=None)
    mock_logger.warning.assert_not_called()


# ---------------------------------------------------------------------------
# check_consistency — warning cases
# ---------------------------------------------------------------------------


def _run_check(
    registry: dict,
    needs: dict,
) -> list[str]:
    """Run check_consistency and return list of warning messages."""
    app = MagicMock()
    app.env.module_verification_report_registry = registry
    warnings: list[str] = []

    def _capture(*args: object) -> None:
        # logger.warning(fmt, *args) — interpolate for easy assertion
        fmt = str(args[0]) if args else ""
        warnings.append(fmt % args[1:] if len(args) > 1 else fmt)

    with (
        patch(
            "src.extensions.score_module_verification_report.consistency_checks._needs_view",
            return_value=needs,
        ),
        patch(
            "src.extensions.score_module_verification_report.consistency_checks.logger"
        ) as mock_logger,
    ):
        mock_logger.warning.side_effect = _capture
        check_consistency(app, exception=None)
    return warnings


def test_warns_when_comp_missing_from_module_includes() -> None:
    registry = {"mod__m": _registry_entry(comp_ids=["comp__m_a"])}
    needs = {
        "mod__m": {"includes": []},  # comp__m_a NOT listed
        "comp__m_a": {"belongs_to": ["feat__m"]},
    }
    warnings = _run_check(registry, needs)
    assert any("comp__m_a" in w and "mod__m" in w and "includes" in w for w in warnings)


def test_warns_when_feature_missing_from_comp_belongs_to() -> None:
    registry = {"mod__m": _registry_entry(comp_ids=["comp__m_a"])}
    needs = {
        "mod__m": {"includes": ["comp__m_a"]},
        "comp__m_a": {"belongs_to": []},  # feat__m NOT listed
    }
    warnings = _run_check(registry, needs)
    assert any(
        "feat__m" in w and "comp__m_a" in w and "belongs_to" in w for w in warnings
    )


def test_no_warning_when_all_links_correct() -> None:
    registry = {"mod__m": _registry_entry(comp_ids=["comp__m_a", "comp__m_b"])}
    needs = {
        "mod__m": {"includes": ["comp__m_a", "comp__m_b"]},
        "comp__m_a": {"belongs_to": ["feat__m"]},
        "comp__m_b": {"belongs_to": ["feat__m"]},
    }
    warnings = _run_check(registry, needs)
    assert warnings == []


def test_skips_module_check_when_mod_need_not_found() -> None:
    registry = {
        "mod__missing": _registry_entry(
            module_id="mod__missing", comp_ids=["comp__m_a"]
        )
    }
    needs = {
        # mod__missing is absent
        "comp__m_a": {"belongs_to": ["feat__m"]},
    }
    warnings = _run_check(registry, needs)
    # warns that module id was not found
    assert any("mod__missing" in w and "not found" in w for w in warnings)
    # belongs_to is correct — no second warning
    assert not any("belongs_to" in w for w in warnings)


def test_warns_when_comp_need_not_found() -> None:
    registry = {"mod__m": _registry_entry(comp_ids=["comp__missing"])}
    needs = {
        "mod__m": {"includes": ["comp__missing"]},
        # comp__missing absent from needs
    }
    warnings = _run_check(registry, needs)
    assert any("comp__missing" in w and "not found" in w for w in warnings)


def test_warning_includes_docname() -> None:
    registry = {
        "mod__m": _registry_entry(comp_ids=["comp__m_a"], docname="docs/report")
    }
    needs = {
        "mod__m": {"includes": []},
        "comp__m_a": {"belongs_to": ["feat__m"]},
    }
    warnings = _run_check(registry, needs)
    assert any("docs/report" in w for w in warnings)

    registry = {"mod__m": _registry_entry(comp_ids=["comp__m_a", "comp__m_b"])}
    needs = {
        "mod__m": {"includes": []},  # neither comp listed
        "comp__m_a": {"belongs_to": []},  # feature missing
        "comp__m_b": {"belongs_to": []},  # feature missing
    }
    warnings = _run_check(registry, needs)
    assert len(warnings) == 4  # 2× includes + 2× belongs_to
