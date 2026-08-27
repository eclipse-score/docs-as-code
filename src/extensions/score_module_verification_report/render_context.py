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
"""Render-context helpers for the ``mod_ver_report`` need template.

Sphinx-Needs renders a need's ``:template:`` from the need's own fields plus
whatever sits in ``needs_render_context``. Everything the module verification
report shows is either a field of the need or a ``needtable`` / ``needpie``
filter — with one exception: test coverage, which comes from an LCOV file on
disk. A Jinja template cannot read files, so the coverage lookup is registered
here as a callable the template invokes by component slug.
"""

from __future__ import annotations

from typing import Any

from .coverage import FileCoverage, coverage_rows, load_coverage, records_for_slug


class CoverageLookup:
    """``mvr_coverage(slug_norm)`` — coverage table rows for one component.

    Deliberately a class rather than a closure: Sphinx checks every config
    value with ``is_serializable``, which rejects ``types.FunctionType``
    outright. A plain function (or lambda) in ``needs_render_context`` makes
    Sphinx log ``cannot cache unpickleable configuration value``, which is
    fatal in a ``-W`` build. An instance of a module-level class is not a
    function type, and its state (a path plus plain dataclasses) pickles
    cleanly, so the config cache keeps working.

    The LCOV file is parsed on first use and cached for the rest of the build:
    a report with N components would otherwise re-read it N times, and a
    project without a report must not pay for parsing it at all.
    """

    def __init__(self, lcov_path: str) -> None:
        self.lcov_path = lcov_path
        self.records: list[FileCoverage] | None = None

    def __call__(self, slug_norm: str) -> str:
        """Return ``list-table`` rows for *slug_norm*, or ``""`` if no match.

        The rows come from :func:`.coverage.coverage_rows` (including the
        ``**Total**`` row). The template branches on the empty string to show
        either the table or the "no coverage data" note.
        """
        if self.records is None:
            self.records = load_coverage(self.lcov_path)
        return coverage_rows(records_for_slug(self.records, slug_norm))


def register_render_context(app: Any, config: Any) -> None:
    """Add the report's helpers to ``needs_render_context``.

    Runs on ``config-inited`` so the helpers are in place before sphinx-needs
    starts creating needs — templates render during the read phase.
    """
    context = getattr(config, "needs_render_context", None)
    if context is None:
        context = {}
        config.needs_render_context = context
    context.setdefault(
        "mvr_coverage", CoverageLookup(getattr(config, "mvr_coverage_lcov", ""))
    )
