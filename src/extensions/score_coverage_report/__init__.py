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
"""Feed per-component LCOV coverage into ``module_verification_report`` Needs.

This extension reads a single LCOV tracefile (produced by whatever coverage
tool the consuming repository already uses, e.g. ``bazel coverage``) and
exposes a ``component_coverage(component_id)`` helper to Sphinx-Needs
post-templates (see ``needs_render_context`` in the Sphinx-Needs docs). The
``module_verification_report`` post-template calls it to render the
per-component "Test Coverage" table that is otherwise a static placeholder.

Wiring, in order of precedence:

1. The ``SCORE_COVERAGE_LCOV`` environment variable (meant for a Bazel rule
   to inject a ``$(location ...)``-expanded path, mirroring how
   ``SCORE_SOURCELINKS`` is wired for ``score_source_code_linker``).
2. The ``score_coverage_lcov_path`` value in ``conf.py`` (a plain path,
   convenient for local/direct Sphinx builds).
3. Nothing at all: a tracefile under :data:`DEFAULT_COVERAGE_DIR` in the
   workspace, else :data:`DEFAULT_LCOV_PATH`, where ``bazel coverage
   --combined_report=lcov`` already leaves its output. A plain ``bazel
   coverage`` followed by a docs build therefore needs no configuration
   whatsoever.

The two defaults mirror how ``score_source_code_linker`` locates test results
(``tests-report``, else ``bazel-testlogs``): coverage, like test outcomes, only
exists once tests have *run*, so a docs build cannot declare it as a Bazel
input without pulling the whole test suite into its dependency graph. Both
defaults need ``BUILD_WORKSPACE_DIRECTORY``, i.e. ``bazel run``; under a
sandboxed ``bazel build`` neither resolves, and the tables fall back to a note
rather than failing the build.

A relative configured path is resolved against the Bazel workspace root when
one is known; it is used as-is otherwise. The file may be either a bare
tracefile or a coverage report archive (see :func:`_read_lcov`), so no manual
unpacking step is required.

Which files belong to which component is not configured here: every ``mod``
Need maps its included components to their implementation roots through the
optional ``source_roots`` option defined in the metamodel, one
``<comp-id>: <path>`` pair per line. Component boundaries are an architectural
decision that neither the directory layout nor the Bazel graph reproduces
reliably -- components nest, and several of them may share a single
documentation bundle -- so the architecture states them next to the
``includes`` list that already defines the module's scope. A component that no
module maps reports no coverage.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx_needs.data import SphinxNeedsData
from sphinx_needs.logging import get_logger

from src.extensions.score_coverage_report.lcov_parser import (
    ComponentCoverage,
    FileCoverage,
    assign_files_to_components,
    parse_lcov,
)
from src.helper_lib import Environment, find_ws_root

LOGGER = get_logger(__name__)

#: Optional ``mod`` option mapping each included component to its
#: implementation root, declared in ``score_metamodel``'s ``metamodel.yaml``.
#: The body holds one ``<comp-id>: <path>`` pair per line.
SOURCE_ROOTS_OPTION = "source_roots"

#: Workspace directory searched for a tracefile before falling back to
#: :data:`DEFAULT_LCOV_PATH`. This mirrors ``score_source_code_linker``'s
#: ``tests-report`` convention: a real directory inside the workspace survives
#: where the ``bazel-*`` convenience symlinks do not, so CI can drop a coverage
#: artifact here and have it picked up without further configuration.
DEFAULT_COVERAGE_DIR = "coverage-report"

#: Workspace-relative location where ``bazel coverage --combined_report=lcov``
#: writes the combined report. Used when neither the environment variable nor
#: ``conf.py`` names a file, so that the common case needs no configuration.
DEFAULT_LCOV_PATH = "bazel-out/_coverage/_coverage_report.dat"

#: Archive member holding the tracefile in a ``score_coverage`` report bundle.
ARCHIVE_LCOV_MEMBER = "lcov_report/lcov.dat"

#: Suffixes accepted when an archive does not use :data:`ARCHIVE_LCOV_MEMBER`.
_LCOV_SUFFIXES = (".dat", ".info", ".lcov")

# Process-local state, mirroring the pattern used by
# ``score_sphinx_needs_templates``'s ``_LinkedNeeds``: the render-context
# callable must stay a plain, pickleable top-level instance, so the data it
# reads is kept in module globals instead of instance state.
_build_environment: BuildEnvironment | None = None
_coverage_by_file: dict[str, FileCoverage] = {}
_coverage_by_component: dict[str, ComponentCoverage] | None = None


def _find_in_coverage_dir(ws_root: Path) -> Path | None:
    """Return the first tracefile inside :data:`DEFAULT_COVERAGE_DIR`, if any.

    Recursive, because a coverage artifact is usually an unpacked report tree
    rather than a single loose file. Sorting keeps the choice deterministic
    when several candidates exist.
    """
    coverage_dir = ws_root / DEFAULT_COVERAGE_DIR
    if not coverage_dir.is_dir():
        return None
    candidates = sorted(
        path
        for path in coverage_dir.rglob("*")
        if path.is_file() and path.suffix in _LCOV_SUFFIXES
    )
    return candidates[0] if candidates else None


def _resolve_lcov_path(app: Sphinx) -> Path:
    env = Environment()
    raw_path = env.get("SCORE_COVERAGE_LCOV", "") or (
        getattr(app.config, "score_coverage_lcov_path", "") or ""
    )
    ws_root = find_ws_root()
    if raw_path:
        lcov_path = Path(raw_path)
        if not lcov_path.is_absolute() and ws_root is not None:
            lcov_path = ws_root / lcov_path
        return lcov_path
    if ws_root is None:
        return Path(DEFAULT_LCOV_PATH)
    return _find_in_coverage_dir(ws_root) or ws_root / DEFAULT_LCOV_PATH


def _read_lcov(lcov_path: Path) -> str | None:
    """Return the tracefile text, unpacking a report archive when needed.

    ``bazel coverage --combined_report=lcov`` names its output ``.dat``, but a
    repository may plug in a report generator that writes an archive under that
    name instead -- ``score_coverage``'s reporter bundles the HTML, text and
    LCOV renderings into a ZIP. Sniff the content rather than the extension and
    accept both, so the docs build reads whatever ``bazel coverage`` produced.

    Members are read into memory only; nothing is written to disk, so a crafted
    archive cannot escape via ``..`` path entries.
    """
    if not zipfile.is_zipfile(lcov_path):
        return lcov_path.read_text(encoding="utf-8")
    with zipfile.ZipFile(lcov_path) as archive:
        names = archive.namelist()
        member = ARCHIVE_LCOV_MEMBER if ARCHIVE_LCOV_MEMBER in names else None
        if member is None:
            member = next(
                (name for name in sorted(names) if name.endswith(_LCOV_SUFFIXES)),
                None,
            )
        if member is None:
            LOGGER.warning(
                "score_coverage_report: no LCOV tracefile inside archive "
                f"{lcov_path}, skipping coverage tables",
                type="score_coverage_report",
            )
            return None
        return archive.read(member).decode("utf-8")


def _load_coverage(app: Sphinx) -> dict[str, FileCoverage]:
    lcov_path = _resolve_lcov_path(app)
    if not lcov_path.is_file():
        LOGGER.info(
            f"score_coverage_report: LCOV file not found, skipping: {lcov_path}",
            type="score_coverage_report",
        )
        return {}
    content = _read_lcov(lcov_path)
    if content is None:
        return {}
    return parse_lcov(content)


def _parse_source_roots(raw: str) -> dict[str, str]:
    """Parse a ``source_roots`` option body into ``{component_id: root}``.

    The body holds one ``<comp-id>: <path>`` pair per line. ``score_metamodel``
    validates that shape, but only as a warning, so malformed lines are skipped
    here rather than trusted.
    """
    roots: dict[str, str] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        component_id, separator, root = line.partition(":")
        if not separator:
            LOGGER.warning(
                f"score_coverage_report: ignoring malformed source_roots entry "
                f"(expected '<comp-id>: <path>'): {line!r}",
                type="score_coverage_report",
            )
            continue
        component_id, root = component_id.strip(), root.strip()
        if component_id and root:
            roots[component_id] = root
    return roots


def _component_source_roots(env: BuildEnvironment) -> dict[str, str]:
    """Collect the implementation roots declared by every ``mod`` Need."""
    needs = SphinxNeedsData(env).get_needs_mutable()
    roots: dict[str, str] = {}
    for need in needs.values():
        if need.get("type") != "mod":
            continue
        raw = str(need.get(SOURCE_ROOTS_OPTION) or "").strip()
        if not raw:
            continue
        for component_id, root in _parse_source_roots(raw).items():
            previous = roots.get(component_id)
            if previous is not None and previous != root:
                LOGGER.warning(
                    f"score_coverage_report: {component_id} is given conflicting "
                    f"source roots ({previous!r} and {root!r}); using {root!r}",
                    type="score_coverage_report",
                )
            roots[component_id] = root
    return roots


class _ComponentCoverage:
    """Render-context callable: ``component_coverage(component_id)``."""

    def __call__(self, component_id: str) -> ComponentCoverage | None:
        global _coverage_by_component
        if _build_environment is None or not _coverage_by_file:
            return None
        if _coverage_by_component is None:
            _coverage_by_component = assign_files_to_components(
                _coverage_by_file, _component_source_roots(_build_environment)
            )
        return _coverage_by_component.get(component_id)


_component_coverage_callable = _ComponentCoverage()


def _capture_coverage_config(app: Sphinx) -> None:
    """Load the LCOV tracefile and keep the build environment for lookups.

    Connected to ``builder-inited``, the first lifecycle event at which both
    ``app.config`` and ``app.env`` are available (mirrors
    ``score_sphinx_needs_templates._capture_template_environment``).
    """
    global _build_environment, _coverage_by_file
    _build_environment = app.env
    _coverage_by_file = _load_coverage(app)


def _invalidate_component_coverage(app: Sphinx, env: BuildEnvironment) -> None:
    """Drop the attribution cache before marked pages are rendered again.

    ``module_verification_report`` carries the ``render-after-needs-collection``
    marker, so it is rendered once while documents are read -- when a parallel
    worker need not see every ``mod`` Need yet -- and once more after the Need
    environments have been merged. Clearing the cache here makes the second pass
    attribute coverage using the complete set of Needs. The low priority number
    keeps this ahead of ``score_sphinx_needs_templates``, which re-reads the
    marked pages on the same event.
    """
    global _coverage_by_component
    _coverage_by_component = None


def setup(app: Sphinx) -> dict[str, object]:
    app.setup_extension("sphinx_needs")

    app.add_config_value(
        "score_coverage_lcov_path",
        default="",
        rebuild="env",
        types=str,
        description=(
            "Repo-relative (or absolute) path to an LCOV tracefile, or to an "
            "archive containing one, used to populate per-component "
            "test-coverage tables in module_verification_report. Overridden by "
            "the SCORE_COVERAGE_LCOV environment variable when set; defaults "
            f"to {DEFAULT_LCOV_PATH} when neither is given."
        ),
    )
    app.config.needs_render_context.setdefault(
        "component_coverage", _component_coverage_callable
    )
    app.connect("builder-inited", _capture_coverage_config)
    app.connect("env-updated", _invalidate_component_coverage, priority=100)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
