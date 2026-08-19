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
"""Coverage summary loading and intro-paragraph selection.

The JSON is produced by ``tools/extract_coverage.py`` from an LCOV
report. Its top-level keys are component slugs (matching
``comp__<module>_<slug>`` in the sphinx-needs data). Presence of a slug
with real metric values marks that component as *measured*; absence
marks it as *specification-only*.
"""
from __future__ import annotations

import json
import os


COVERAGE_INTRO_MEASURED = (
    "Aggregated from ``bazel coverage``. Regenerate via\n"
    "``python3 tools/extract_coverage.py \"$(bazel info output_path)"
    "/_coverage/_coverage_report.dat\" docs/reporting/coverage_summary.json``.\n"
)
COVERAGE_INTRO_SPEC_ONLY = (
    "This component is specification-only and has no dedicated unit\n"
    "test binary in ``//score/\u2026``.\n"
)

COVERAGE_SUMMARY_REL_PATH = os.path.join("reporting", "coverage_summary.json")


def load_coverage_summary(env) -> dict:
    """Return the parsed ``coverage_summary.json`` (empty dict on failure)."""
    path = os.path.join(env.srcdir, COVERAGE_SUMMARY_REL_PATH)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    if os.path.isfile(path):
        env.note_dependency(path)
    return data or {}


def coverage_intro(comp: dict, coverage_data: dict) -> str:
    """Choose the intro paragraph based on ``coverage_summary.json``.

    A component counts as *measured* iff its slug appears in the JSON
    with at least one non-null metric percentage. Otherwise it is
    treated as specification-only. This mirrors how the
    ``|coverage_<slug>_*|`` substitutions in ``conf.py`` decide between
    numeric output and ``"not measured"``.
    """
    entry = coverage_data.get(comp["slug"]) or {}
    measured = any(
        entry.get(f"{m}_pct") is not None
        for m in ("lines", "functions", "branches")
    )
    return (COVERAGE_INTRO_MEASURED if measured else COVERAGE_INTRO_SPEC_ONLY) + "\n"
