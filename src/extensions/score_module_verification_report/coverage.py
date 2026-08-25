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
"""LCOV parsing and per-component aggregation for the coverage dropdown.

The report renderer calls :func:`load_coverage` once per build; the result
is a list of :class:`FileCoverage` records that :func:`records_for_slug`
filters per component using the same normalised-slug substring match that
:func:`.rendering.workproduct_rows` uses for work-product zuordnung.

If the LCOV file cannot be found (no ``bazel coverage`` run yet), the
functions return empty lists so the coverage dropdown is silently
omitted rather than breaking the docs build.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


def _workspace_root() -> Path | None:
    """Return the workspace root or ``None`` if it cannot be determined.

    ``helper_lib.find_ws_root`` is only importable at Bazel run-time; in
    plain pytest runs it is absent, in which case we fall back to walking
    up from the current working directory looking for ``MODULE.bazel``
    or ``WORKSPACE``.
    """
    try:
        from helper_lib import find_ws_root  # type: ignore[import-not-found]

        root = find_ws_root()
        if root is not None:
            return root
    except ImportError:
        pass
    cwd = Path.cwd()
    for candidate in (cwd, *cwd.parents):
        if (candidate / "MODULE.bazel").exists() or (candidate / "WORKSPACE").exists():
            return candidate
    return None


@dataclass
class FileCoverage:
    """Aggregated coverage for a single source file (one ``SF:`` record)."""

    source: str
    lines_found: int = 0
    lines_hit: int = 0
    branches_found: int = 0
    branches_hit: int = 0

    @property
    def line_pct(self) -> float:
        return 100.0 * self.lines_hit / self.lines_found if self.lines_found else 0.0

    @property
    def branch_pct(self) -> float:
        return (
            100.0 * self.branches_hit / self.branches_found
            if self.branches_found
            else 0.0
        )


def parse_lcov(path: Path) -> list[FileCoverage]:
    """Parse an LCOV ``*.dat`` file into per-source coverage records."""
    records: list[FileCoverage] = []
    current: FileCoverage | None = None
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if line.startswith("SF:"):
            current = FileCoverage(source=line[3:])
            records.append(current)
        elif current is None:
            continue
        elif line.startswith("LF:"):
            current.lines_found = int(line[3:] or 0)
        elif line.startswith("LH:"):
            current.lines_hit = int(line[3:] or 0)
        elif line.startswith("BRF:"):
            current.branches_found = int(line[4:] or 0)
        elif line.startswith("BRH:"):
            current.branches_hit = int(line[4:] or 0)
        elif line == "end_of_record":
            current = None
    return records


def load_coverage(config_path: str) -> list[FileCoverage]:
    """Locate and parse the LCOV report.

    ``config_path`` may be absolute or relative. Relative paths are
    resolved against the workspace root (same discovery helper used by
    the source-code linker for ``bazel-testlogs``). If the file is
    missing, an empty list is returned and a single log line is
    emitted — the missing file must not break the docs build.
    """
    if not config_path:
        return []
    path = Path(config_path)
    if not path.is_absolute():
        ws_root = _workspace_root()
        if ws_root is None:
            logger.info("mvr coverage: workspace root not found; skipping LCOV load")
            return []
        path = ws_root / path
    if not path.is_file():
        logger.info(
            "mvr coverage: LCOV file not found at %s; skipping coverage dropdown",
            path,
        )
        return []
    logger.info("mvr coverage: parsing LCOV %s", path)
    return parse_lcov(path)


def records_for_slug(
    records: list[FileCoverage],
    slug_norm: str,
) -> list[FileCoverage]:
    """Filter *records* to those whose source path contains *slug_norm*.

    ``slug_norm`` must already be normalised (underscores stripped,
    lower-cased) — matching :func:`.rendering.normalize_slug`.
    """
    if not slug_norm:
        return []
    return [
        r
        for r in records
        if slug_norm in r.source.replace("_", "").replace("/", "").lower()
    ]


def _pct_str(hit: int, found: int) -> str:
    """Format a hit/found ratio as a percentage string.

    Returns an empty string when *found* is 0 — there is nothing to
    cover, so showing ``0.0`` would misleadingly read as "0% covered".
    """
    return f"{100.0 * hit / found:.1f}" if found else ""


def coverage_rows(records: list[FileCoverage]) -> str:
    """Render *records* as ``list-table`` rows (no header row).

    Files with neither line nor branch data (``lines_found == 0`` and
    ``branches_found == 0``, e.g. headers never instrumented by the
    coverage run) are skipped — a row of all zeroes carries no
    information and reads as "0% covered" even though nothing was
    measured at all.

    Returns an empty string when *records* is empty so callers can decide
    to omit the whole dropdown block.
    """
    if not records:
        return ""
    visible = [r for r in records if r.lines_found or r.branches_found]
    if not visible:
        return ""
    lines: list[str] = []
    total = FileCoverage(source="**Total**")
    for r in sorted(visible, key=lambda x: x.source):
        lines.append(f"      * - ``{r.source}``")
        lines.append(f"        - {r.lines_found}")
        lines.append(f"        - {r.lines_hit}")
        lines.append(f"        - {_pct_str(r.lines_hit, r.lines_found)}")
        lines.append(f"        - {r.branches_found}")
        lines.append(f"        - {r.branches_hit}")
        lines.append(f"        - {_pct_str(r.branches_hit, r.branches_found)}")
        total.lines_found += r.lines_found
        total.lines_hit += r.lines_hit
        total.branches_found += r.branches_found
        total.branches_hit += r.branches_hit
    lines.append(f"      * - {total.source}")
    lines.append(f"        - {total.lines_found}")
    lines.append(f"        - {total.lines_hit}")
    lines.append(f"        - {_pct_str(total.lines_hit, total.lines_found)}")
    lines.append(f"        - {total.branches_found}")
    lines.append(f"        - {total.branches_hit}")
    lines.append(f"        - {_pct_str(total.branches_hit, total.branches_found)}")
    return "\n".join(lines)
