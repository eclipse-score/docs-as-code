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

"""Tests for verification_schema_sync_check.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_MY_PATH = Path(__file__).parent
_CHECK_SCRIPT = _MY_PATH.parent / "verification_schema_sync_check.py"


def _write_template(tmp_path: Path, description: str) -> Path:
    path = tmp_path / "module_verification_report.rst"
    path.write_text(
        """
Verification Report contains:

.. list-table:: Verification report section contract fields
   :header-rows: 1
   :widths: 1 2 5

   * - section_index
     - section_key
     - section_description
   * - 1
     - verification_coverage
     - DESCRIPTION_PLACEHOLDER
""".replace("DESCRIPTION_PLACEHOLDER", description),
        encoding="utf-8",
    )
    return path


def _write_schema(tmp_path: Path, description: str | None) -> Path:
    schema = {
        "properties": {
            "verification_coverage": {
                "$ref": "./verification_coverage_schema.json",
            }
        }
    }
    if description is not None:
        schema["properties"]["verification_coverage"]["description"] = description

    path = tmp_path / "verification_report_schema.json"
    path.write_text(json.dumps(schema), encoding="utf-8")
    return path


def _run_check(template_path: Path, schema_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            _CHECK_SCRIPT,
            "--process-template",
            str(template_path),
            "--report-schema",
            str(schema_path),
            "--section-key",
            "verification_coverage",
        ],
        capture_output=True,
        text=True,
    )


def test_sync_check_passes_on_matching_description(tmp_path: Path) -> None:
    description = (
        "Coverage on requirements, architecture, and detailed design including "
        "test and inspection results."
    )
    template_path = _write_template(tmp_path, description)
    schema_path = _write_schema(tmp_path, description)

    result = _run_check(template_path, schema_path)

    assert result.returncode == 0
    assert "Schema sync check passed." in result.stdout


def test_sync_check_fails_on_description_drift(tmp_path: Path) -> None:
    template_path = _write_template(
        tmp_path,
        "Coverage on requirements, architecture, and detailed design including test and inspection results.",
    )
    schema_path = _write_schema(
        tmp_path,
        "Coverage-focused sections of the S-CORE process verification report.",
    )

    result = _run_check(template_path, schema_path)

    assert result.returncode == 2
    assert "Schema sync check failed:" in result.stdout


def test_sync_check_fails_on_missing_description(tmp_path: Path) -> None:
    template_path = _write_template(
        tmp_path,
        "Coverage on requirements, architecture, and detailed design including test and inspection results.",
    )
    schema_path = _write_schema(tmp_path, None)

    result = _run_check(template_path, schema_path)

    assert result.returncode == 2
    assert "schema description missing" in result.stderr
