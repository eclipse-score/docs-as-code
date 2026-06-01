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

"""Tests for Sphinx-side metrics.json generation defaults."""

import json
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from sphinx.application import Sphinx

import src.extensions.score_metamodel.__init__ as metamodel_init


class _FakeNeedsData:
    def __init__(self, env: object):
        self._env = env

    def get_needs_view(self) -> dict[str, dict[str, object]]:
        return {
            "LOCAL_REQ": {
                "id": "LOCAL_REQ",
                "type": "tool_req",
                "implemented": "YES",
                "source_code_link": "",
                "testlink": "",
                "is_external": False,
            },
            "LOCAL_FEAT": {
                "id": "LOCAL_FEAT",
                "type": "feat_req",
                "implemented": "YES",
                "source_code_link": "",
                "testlink": "",
                "is_external": False,
            },
            "EXT_REQ": {
                "id": "EXT_REQ",
                "type": "tool_req",
                "implemented": "NO",
                "source_code_link": "src/ext.py:1",
                "testlink": "",
                "is_external": True,
            },
            "EXT_FEAT": {
                "id": "EXT_FEAT",
                "type": "feat_req",
                "implemented": "NO",
                "source_code_link": "src/ext_feat.py:1",
                "testlink": "",
                "is_external": True,
            },
            "EXT_GD": {
                "id": "EXT_GD",
                "type": "gd_req",
                "implemented": "NO",
                "source_code_link": "src/ext_gd.py:1",
                "testlink": "",
                "is_external": True,
            },
        }


class _FakeNonReqNeedsData:
    def __init__(self, env: object):
        self._env = env

    def get_needs_view(self) -> dict[str, dict[str, object]]:
        return {
            "LOCAL_COMP": {
                "id": "LOCAL_COMP",
                "type": "comp",
                "implemented": "YES",
                "source_code_link": "",
                "testlink": "",
                "is_external": False,
            },
            "LOCAL_DOC": {
                "id": "LOCAL_DOC",
                "type": "document",
                "implemented": "YES",
                "source_code_link": "",
                "testlink": "",
                "is_external": False,
            },
        }


def _app(
    tmp_path: Path,
    include_external: bool,
    requirement_types: str = "",
    needs_types: list[dict[str, object]] | None = None,
) -> SimpleNamespace:
    discovered_types = needs_types or [
        {"directive": "tool_req", "tags": ["requirement_excl_process"]},
        {"directive": "feat_req", "tags": ["requirement"]},
        {"directive": "workflow", "tags": []},
    ]
    return SimpleNamespace(
        env=object(),
        outdir=str(tmp_path),
        config=SimpleNamespace(
            score_metamodel_requirement_types=requirement_types,
            score_metamodel_include_external_needs=include_external,
            needs_types=discovered_types,
        ),
    )


def test_write_metrics_json_defaults_to_local_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(metamodel_init, "SphinxNeedsData", _FakeNeedsData)

    metamodel_init._write_metrics_json(
        cast(Sphinx, _app(tmp_path, include_external=False)),
        None,
    )

    payload = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    metrics = payload["metrics_by_type"]["tool_req"]

    assert payload["schema_version"] == "1"
    assert metrics["include_not_implemented"] is True
    assert metrics["include_external"] is False
    assert metrics["requirements"]["total"] == 1


def test_write_metrics_json_can_include_external(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(metamodel_init, "SphinxNeedsData", _FakeNeedsData)

    metamodel_init._write_metrics_json(
        cast(Sphinx, _app(tmp_path, include_external=True)),
        None,
    )

    payload = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    metrics = payload["metrics_by_type"]["tool_req"]

    assert metrics["include_external"] is True
    assert metrics["requirements"]["total"] == 2


def test_explicit_requirement_types_disable_autodiscovery(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(metamodel_init, "SphinxNeedsData", _FakeNeedsData)

    metamodel_init._write_metrics_json(
        cast(
            Sphinx,
            _app(
                tmp_path,
                include_external=False,
                requirement_types="tool_req",
            ),
        ),
        None,
    )

    payload = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    assert set(payload["metrics_by_type"].keys()) == {"tool_req"}


def test_write_metrics_json_autodiscovers_when_types_unset(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(metamodel_init, "SphinxNeedsData", _FakeNeedsData)

    metamodel_init._write_metrics_json(
        cast(
            Sphinx,
            _app(tmp_path, include_external=False, requirement_types=""),
        ),
        None,
    )

    payload = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1"
    assert set(payload["metrics_by_type"].keys()) == {"feat_req", "tool_req"}


def test_autodiscovery_excludes_tagged_types_not_present_in_needs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(metamodel_init, "SphinxNeedsData", _FakeNeedsData)

    metamodel_init._write_metrics_json(
        cast(
            Sphinx,
            _app(
                tmp_path,
                include_external=False,
                requirement_types="",
                needs_types=[
                    {"directive": "tool_req", "tags": ["requirement_excl_process"]},
                    {"directive": "feat_req", "tags": ["requirement"]},
                    {"directive": "aou_req", "tags": ["requirement"]},
                ],
            ),
        ),
        None,
    )

    payload = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    assert set(payload["metrics_by_type"].keys()) == {"feat_req", "tool_req"}


def test_write_metrics_json_empty_when_no_types_configured_or_discovered(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(metamodel_init, "SphinxNeedsData", _FakeNonReqNeedsData)

    metamodel_init._write_metrics_json(
        cast(
            Sphinx,
            _app(
                tmp_path,
                include_external=False,
                requirement_types="",
                needs_types=[{"directive": "workflow", "tags": []}],
            ),
        ),
        None,
    )

    payload = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1"
    assert payload["metrics_by_type"] == {}


def test_autodiscovery_without_tagged_requirement_types_is_empty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(metamodel_init, "SphinxNeedsData", _FakeNeedsData)

    metamodel_init._write_metrics_json(
        cast(
            Sphinx,
            _app(
                tmp_path,
                include_external=False,
                requirement_types="",
                needs_types=[{"directive": "workflow", "tags": []}],
            ),
        ),
        None,
    )

    payload = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    assert payload["metrics_by_type"] == {}


def test_autodiscovery_respects_include_external_scope(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(metamodel_init, "SphinxNeedsData", _FakeNeedsData)

    metamodel_init._write_metrics_json(
        cast(
            Sphinx,
            _app(
                tmp_path,
                include_external=True,
                requirement_types="",
                needs_types=[
                    {"directive": "tool_req", "tags": ["requirement_excl_process"]},
                    {"directive": "feat_req", "tags": ["requirement"]},
                    {"directive": "gd_req", "tags": ["requirement"]},
                ],
            ),
        ),
        None,
    )

    payload = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    assert set(payload["metrics_by_type"].keys()) == {"feat_req", "gd_req", "tool_req"}


@pytest.mark.parametrize(
    ("requirement_types", "include_external", "should_exist", "expected_totals"),
    [
        ("tool_req", False, True, {"tool_req": 1}),
        ("feat_req,tool_req", False, True, {"feat_req": 1, "tool_req": 1}),
        ("", False, True, {"feat_req": 1, "tool_req": 1}),
        ("   ", False, True, {"feat_req": 1, "tool_req": 1}),
        ("tool_req", True, True, {"tool_req": 2}),
    ],
)
def test_write_metrics_json_settings_matrix(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    requirement_types: str,
    include_external: bool,
    should_exist: bool,
    expected_totals: dict[str, int],
) -> None:
    monkeypatch.setattr(metamodel_init, "SphinxNeedsData", _FakeNeedsData)

    metamodel_init._write_metrics_json(
        cast(
            Sphinx,
            _app(
                tmp_path,
                include_external=include_external,
                requirement_types=requirement_types,
            ),
        ),
        None,
    )

    metrics_file = tmp_path / "metrics.json"
    assert metrics_file.exists() is should_exist
    if not should_exist:
        return

    payload = json.loads(metrics_file.read_text(encoding="utf-8"))
    by_type = payload["metrics_by_type"]
    assert set(by_type.keys()) == set(expected_totals.keys())

    for req_type, expected_total in expected_totals.items():
        assert by_type[req_type]["requirements"]["total"] == expected_total
