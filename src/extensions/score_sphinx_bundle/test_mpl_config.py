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
"""Regression tests for Matplotlib initialization in restricted environments."""

import os
from importlib import import_module
from pathlib import Path
from typing import Any

import matplotlib
from _pytest.monkeypatch import MonkeyPatch


def test_mpl_config_default_does_not_overwrite_explicit_value(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    """The extension preserves a caller-provided Matplotlib config path."""
    setup = import_module("src.extensions.score_sphinx_bundle").setup

    configured = tmp_path / "chosen-config"
    monkeypatch.setenv("MPLCONFIGDIR", str(configured))
    monkeypatch.chdir(tmp_path)
    app = _FakeSphinxApp()

    setup(app)  # type: ignore[arg-type] -- lightweight Sphinx test double.

    assert Path(os.environ["MPLCONFIGDIR"]) == configured
    assert not configured.exists()


def test_mpl_config_default_avoids_home_lookup(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    """The extension sets a default before importing Matplotlib."""
    setup = import_module("src.extensions.score_sphinx_bundle").setup

    monkeypatch.delenv("HOME", raising=False)
    monkeypatch.delenv("MPLCONFIGDIR", raising=False)
    monkeypatch.chdir(tmp_path)
    app = _FakeSphinxApp()

    setup(app)  # type: ignore[arg-type] -- lightweight Sphinx test double.

    assert os.environ["MPLCONFIGDIR"] == str(tmp_path / ".matplotlib")
    monkeypatch.setattr(matplotlib, "get_configdir", lambda: os.environ["MPLCONFIGDIR"])
    assert matplotlib.get_configdir() == str(tmp_path / ".matplotlib")


class _FakeConfig:
    def __init__(self) -> None:
        self._raw_config: dict[str, Any] = {}
        self.templates_path: list[str] = []
        self.exclude_patterns: list[str] = []
        self.source_suffix: dict[str, str] = {}
        self.myst_enable_extensions: list[str] = []


class _FakeBuilder:
    name = "html"


class _FakeSphinxApp:
    def __init__(self) -> None:
        self.config = _FakeConfig()
        self.builder = _FakeBuilder()

    def add_config_value(self, name: str, default: object, rebuild: str) -> None:
        setattr(self.config, name, default)

    def setup_extension(self, extension: str) -> None:
        pass

    def connect(
        self, event: str, callback: object, priority: int | None = None
    ) -> None:
        pass
