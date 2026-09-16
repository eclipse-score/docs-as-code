# *******************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
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

from unittest.mock import Mock

import pytest

from score_pytest import main


def test_score_pytest_loads_conftest(fixture42):  # pyright: ignore[reportMissingParameterType]
    assert fixture42 == 42


def test_score_pytest_resolves_runfiles_arguments(monkeypatch: pytest.MonkeyPatch):
    """Resolve config and test-file addresses while leaving pytest options intact."""
    runfiles = Mock()
    runfiles.Rlocation.side_effect = lambda path: {
        "_main/pyproject.toml": "/runfiles/pyproject.toml",
        "_main/tests/test_example.py": "/runfiles/tests/test_example.py",
    }.get(path)
    monkeypatch.setattr(main.Runfiles, "Create", Mock(return_value=runfiles))
    pytest_main = Mock(return_value=0)
    monkeypatch.setattr(main.pytest, "main", pytest_main)

    result = main.main(
        [
            "-c",
            "_main/pyproject.toml",
            "-p",
            "no:cacheprovider",
            "--junitxml=/tmp/test.xml",
            "_main/tests/test_example.py",
        ]
    )

    assert result == 0
    pytest_main.assert_called_once_with(
        [
            "-c",
            "/runfiles/pyproject.toml",
            "-p",
            "no:cacheprovider",
            "--junitxml=/tmp/test.xml",
            "/runfiles/tests/test_example.py",
        ]
    )
