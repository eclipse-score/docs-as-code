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
"""Build-finished check: validate that each component listed in
``:components:`` is properly linked in the sphinx-needs graph.

Two rules are enforced for every ``.. module-verification-report::``
directive instance:

1. ``comp_id ∈ mod_need["includes"]``
   — the module need must explicitly include the component.
2. ``feature_id ∈ comp_need["belongs_to"]``
   — the component need must declare that it belongs to the feature.

Violations are reported as Sphinx warnings so they surface in CI logs
without stopping the build.

The registry (``env.module_verification_report_registry``) is populated by
:class:`~.directive.ModuleVerificationReportDirective` during the read phase
and is parallel-read safe via ``init_registry`` / ``purge_registry`` /
``merge_registry`` lifecycle hooks.
"""

from __future__ import annotations

from typing import Any

from sphinx.util import logging

logger = logging.getLogger(__name__)


def _needs_view(env: Any) -> Any | None:
    """Return sphinx-needs view or *None* when sphinx-needs is not loaded."""
    try:
        from sphinx_needs.data import SphinxNeedsData  # type: ignore[import-untyped]

        return SphinxNeedsData(env).get_needs_view()
    except Exception:  # pragma: no cover — only absent in test env
        return None


# ---------------------------------------------------------------------------
# Lifecycle hooks (parallel-read safe)
# ---------------------------------------------------------------------------


def init_registry(app: Any, env: Any, docnames: Any) -> None:
    """Create the registry dict on the env if it does not exist yet."""
    if not hasattr(env, "module_verification_report_registry"):
        env.module_verification_report_registry = {}  # type: ignore[attr-defined]


def purge_registry(app: Any, env: Any, docname: str) -> None:
    """Remove registry entries that were produced by *docname*."""
    registry: dict = getattr(env, "module_verification_report_registry", {})
    stale = [k for k, v in registry.items() if v.get("docname") == docname]
    for k in stale:
        del registry[k]


def merge_registry(app: Any, env: Any, docnames: Any, other: Any) -> None:
    """Merge the sub-build registry from *other* into *env*."""
    if not hasattr(env, "module_verification_report_registry"):
        env.module_verification_report_registry = {}  # type: ignore[attr-defined]
    other_registry: dict = getattr(other, "module_verification_report_registry", {})
    env_reg = env.module_verification_report_registry  # type: ignore[attr-defined]
    env_reg.update(other_registry)


# ---------------------------------------------------------------------------
# Build-finished consistency check
# ---------------------------------------------------------------------------


def _check_module(app: Any, needs: Any, module_id: str, info: dict) -> None:
    """Check one module's component links and emit warnings for violations."""
    feature_id: str | None = info["feature_id"]
    comp_ids: list[str] = info["comp_ids"]
    docname: str = info.get("docname", "?")
    mod_need = needs.get(module_id)

    if mod_need is None:
        logger.warning(
            "[module-verification-report] %s: "
            "%s (:module-id:) not found in sphinx-needs — "
            "check the id",
            docname,
            module_id,
        )

    for comp_id in comp_ids:
        comp_need = needs.get(comp_id)

        if comp_need is None:
            logger.warning(
                "[module-verification-report] %s: "
                "%s (listed in :components:) not found in "
                "sphinx-needs — check the id",
                docname,
                comp_id,
            )
            continue

        # Rule 1: component must be in the module's :includes:
        if mod_need is not None:  # noqa: SIM102
            if comp_id not in mod_need.get("includes", []):
                logger.warning(
                    "[module-verification-report] %s: "
                    "%s is listed in :components: but not in "
                    "%s :includes:",
                    docname,
                    comp_id,
                    module_id,
                )

        # Rule 2: feature must be in the component's :belongs_to:
        if feature_id is not None and feature_id not in comp_need.get("belongs_to", []):
            logger.warning(
                "[module-verification-report] %s: "
                "%s is not in %s :belongs_to: "
                "(component listed via :components: of %s)",
                docname,
                feature_id,
                comp_id,
                module_id,
            )


def check_consistency(app: Any, exception: Any) -> None:
    """Emit warnings for components that are missing required need links.

    Skipped entirely when the build already failed (*exception* is not None)
    or when sphinx-needs is unavailable (e.g. unit-test environment).
    """
    if exception:
        return
    registry: dict = getattr(app.env, "module_verification_report_registry", {})
    if not registry:
        return
    needs = _needs_view(app.env)
    if needs is None:
        return

    for module_id, info in registry.items():
        _check_module(app, needs, module_id, info)
