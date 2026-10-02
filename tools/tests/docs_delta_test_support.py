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
"""Shared fixture helpers for documentation delta tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def need(docname: str, title: str, **extra: object) -> dict[str, object]:
    """Make a small representative Sphinx-Needs record for unit tests."""
    return {"id": title.lower(), "docname": docname, "title": title, **extra}


def write_needs(directory: Path, needs: dict[str, dict[str, object]]) -> None:
    """Write the versioned JSON envelope expected from Sphinx-Needs."""
    (directory / "needs.json").write_text(
        json.dumps({"versions": {"1": {"needs": needs}}}), encoding="utf-8"
    )


def git(directory: Path, *arguments: str) -> None:
    """Run a Git command against a temporary repository in an integration test."""
    subprocess.run(
        ["git", "-C", str(directory), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
