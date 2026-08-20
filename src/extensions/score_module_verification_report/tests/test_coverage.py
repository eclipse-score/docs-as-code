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
"""Unit tests for :mod:`score_module_verification_report.coverage`."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from src.extensions.score_module_verification_report.coverage import (
    COVERAGE_INTRO_MEASURED,
    COVERAGE_INTRO_SPEC_ONLY,
    COVERAGE_SUMMARY_REL_PATH,
    coverage_intro,
    load_coverage_summary,
)


def _env(srcdir: Path) -> SimpleNamespace:
    env = SimpleNamespace(srcdir=str(srcdir), _deps=[])
    env.note_dependency = env._deps.append  # type: ignore[attr-defined]
    return env


def _write_summary(srcdir: Path, payload: object) -> Path:
    path = srcdir / COVERAGE_SUMMARY_REL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# load_coverage_summary
# ---------------------------------------------------------------------------


def test_load_coverage_summary_reads_json_and_notes_dependency(tmp_path: Path) -> None:
    payload = {"comp_a": {"lines_pct": 87.5}}
    path = _write_summary(tmp_path, payload)
    env = _env(tmp_path)

    data = load_coverage_summary(env)

    assert data == payload
    assert env._deps == [str(path)]


def test_load_coverage_summary_missing_file_returns_empty(tmp_path: Path) -> None:
    env = _env(tmp_path)
    assert load_coverage_summary(env) == {}
    assert env._deps == []


def test_load_coverage_summary_invalid_json_returns_empty(tmp_path: Path) -> None:
    path = tmp_path / COVERAGE_SUMMARY_REL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not json", encoding="utf-8")
    env = _env(tmp_path)
    assert load_coverage_summary(env) == {}


def test_load_coverage_summary_null_content_returns_empty(tmp_path: Path) -> None:
    _write_summary(tmp_path, None)
    env = _env(tmp_path)
    assert load_coverage_summary(env) == {}


# ---------------------------------------------------------------------------
# coverage_intro
# ---------------------------------------------------------------------------


def test_coverage_intro_measured_when_pct_present() -> None:
    comp = {"slug": "kvs"}
    data = {"kvs": {"lines_pct": 90.0, "functions_pct": None, "branches_pct": None}}
    assert coverage_intro(comp, data).startswith(COVERAGE_INTRO_MEASURED[:32])


def test_coverage_intro_spec_only_when_slug_missing() -> None:
    assert coverage_intro({"slug": "kvs"}, {}).startswith(COVERAGE_INTRO_SPEC_ONLY[:32])


def test_coverage_intro_spec_only_when_all_metrics_none() -> None:
    data = {
        "kvs": {"lines_pct": None, "functions_pct": None, "branches_pct": None},
    }
    assert coverage_intro({"slug": "kvs"}, data).startswith(
        COVERAGE_INTRO_SPEC_ONLY[:32]
    )


def test_coverage_intro_terminates_with_blank_line() -> None:
    result = coverage_intro({"slug": "kvs"}, {})
    assert result.endswith("\n\n")
