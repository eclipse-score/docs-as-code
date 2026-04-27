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
            "EXT_REQ": {
                "id": "EXT_REQ",
                "type": "tool_req",
                "implemented": "NO",
                "source_code_link": "src/ext.py:1",
                "testlink": "",
                "is_external": True,
            },
        }


def _app(tmp_path: Path, include_external: bool) -> SimpleNamespace:
    return SimpleNamespace(
        env=object(),
        outdir=str(tmp_path),
        config=SimpleNamespace(
            score_metamodel_requirement_types="tool_req",
            score_metamodel_include_external_needs=include_external,
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
