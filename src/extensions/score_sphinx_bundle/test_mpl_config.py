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
import subprocess
import sys
from pathlib import Path


def test_mpl_uses_temp_fallback_when_explicit_config_is_not_writable(
    tmp_path: Path,
) -> None:
    """Matplotlib should retain its fallback for an unusable MPLCONFIGDIR."""
    unwritable = tmp_path / "unwritable"
    unwritable.mkdir()
    unwritable.chmod(0o500)
    script = """
import os
os.environ.setdefault("MPLCONFIGDIR", os.path.abspath(".matplotlib"))
import matplotlib
print(matplotlib.get_configdir())
"""
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(unwritable / "config")
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        text=True,
        cwd=tmp_path,
        env=env,
    )
    unwritable.chmod(0o700)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip()


def test_mpl_does_not_require_home_when_config_is_unset(tmp_path: Path) -> None:
    """The default config path avoids Matplotlib consulting HOME."""
    script = """
import os
os.environ.setdefault("MPLCONFIGDIR", os.path.abspath(".matplotlib"))
import matplotlib
print(matplotlib.get_configdir())
"""
    env = os.environ.copy()
    env.pop("HOME", None)
    env.pop("MPLCONFIGDIR", None)
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        text=True,
        cwd=tmp_path,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip()
