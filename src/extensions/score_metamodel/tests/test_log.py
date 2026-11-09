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
from pathlib import Path

import pytest

from src.extensions.score_metamodel import CheckLogger
from src.extensions.score_metamodel.__init__ import (
    _location_prefix,  # pyright: ignore[reportPrivateUsage]
)
from src.extensions.score_metamodel.tests import need


@pytest.mark.parametrize(
    ("prefix", "expected"),
    [
        ("docs", "docs/docname.rst:42"),
        ("", "docname.rst:42"),
    ],
)
def test_location_uses_given_prefix(prefix: str, expected: str):
    assert CheckLogger._location(need(), prefix) == expected  # pyright: ignore[reportPrivateUsage]


def test_location_without_source_info_is_none():
    assert CheckLogger._location(need(lineno=None), "docs") is None  # pyright: ignore[reportPrivateUsage]


@pytest.fixture
def no_bazel_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    for variable in (
        "RUNFILES_DIR",
        "RUNFILES_MANIFEST_FILE",
        "BUILD_WORKSPACE_DIRECTORY",
    ):
        monkeypatch.delenv(variable, raising=False)
    return monkeypatch


@pytest.mark.parametrize("variable", ["RUNFILES_DIR", "RUNFILES_MANIFEST_FILE"])
def test_location_prefix_is_empty_in_bazel_runfiles(
    no_bazel_env: pytest.MonkeyPatch, variable: str
):
    no_bazel_env.setenv(variable, "/some/runfiles")
    assert _location_prefix("/anywhere/docs") == ""


def test_location_prefix_is_relative_to_workspace(
    no_bazel_env: pytest.MonkeyPatch, tmp_path: Path
):
    no_bazel_env.setenv("BUILD_WORKSPACE_DIRECTORY", str(tmp_path))
    assert _location_prefix(tmp_path / "docs") == "docs"


def test_location_prefix_is_relative_to_cwd(
    no_bazel_env: pytest.MonkeyPatch, tmp_path: Path
):
    no_bazel_env.chdir(tmp_path)
    assert _location_prefix(tmp_path / "docs") == "docs"
