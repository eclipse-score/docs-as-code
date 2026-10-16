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
"""Tests for Need inventory loading and comparison."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import docs_delta
from tools.tests.docs_delta_test_support import need


def test_compare_needs_categorizes_changes_and_ignores_volatile_fields() -> None:
    baseline = {
        "same": need(
            "same",
            "Same",
            id="same",
            lineno=10,
            source="old.rst",
            source_code_link="old-commit",
            testlink="old-result",
        ),
        "changed": need(
            "changed",
            "Old",
            id="changed",
            lineno=10,
            source="old.rst",
            source_code_link="old-commit",
            testlink="old-result",
        ),
        "removed": need("removed", "Removed", id="removed"),
    }
    current = {
        "same": need(
            "same",
            "Same",
            id="same",
            lineno=999,
            source="new.rst",
            source_code_link="new-commit",
            testlink="new-result",
        ),
        "changed": need(
            "changed",
            "New",
            id="changed",
            lineno=20,
            source="new.rst",
            source_code_link="new-commit",
            testlink="new-result",
        ),
        "added": need("added", "Added", id="added"),
    }

    result = docs_delta.compare_needs(baseline, current)

    assert [entry.need_id for entry in result.added] == ["added"]
    assert [entry.need_id for entry in result.removed] == ["removed"]
    assert [entry.need_id for entry in result.modified] == ["changed"]
    assert result.modified[0].changed_fields == ("title",)
    assert result.unchanged_count == 1


def test_need_comparison_distinguishes_missing_null_and_boolean_number() -> None:
    baseline: dict[str, dict[str, object]] = {
        "need": {"id": "need", "optional": None, "enabled": True}
    }
    current: dict[str, dict[str, object]] = {"need": {"id": "need", "enabled": 1}}

    result = docs_delta.compare_needs(baseline, current)

    assert result.modified[0].changed_fields == ("enabled", "optional")


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"versions": []},
        {"versions": {"1": {"needs": {"need": "not a record"}}}},
    ],
)
def test_load_needs_rejects_malformed_exports(tmp_path: Path, payload: object) -> None:
    (tmp_path / "needs.json").write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(docs_delta.DocsDeltaError, match="needs JSON|Need entry"):
        docs_delta.load_needs(tmp_path)


def test_load_needs_flattens_versions_and_uses_last_duplicate_id(
    tmp_path: Path,
) -> None:
    (tmp_path / "needs.json").write_text(
        json.dumps(
            {
                "versions": {
                    "1": {"needs": {"same": {"id": "same", "title": "Old"}}},
                    "ignored": "malformed version container",
                    "2": {
                        "needs": {"same": {"id": "same", "title": "New"}},
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    assert docs_delta.load_needs(tmp_path) == {"same": {"id": "same", "title": "New"}}
