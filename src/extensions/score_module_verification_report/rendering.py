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
"""Rendering functions that expand :mod:`.templates` for the report body."""

from __future__ import annotations

import re

from .templates import (
    COMPONENT_TEMPLATE,
    COMPONENTS_HEADER,
    FEATURE_TEMPLATE,
    OVERVIEW_TEMPLATE,
    WP_TABLE_CSS,
)


def normalize_slug(text: str) -> str:
    """Return *text* stripped of underscores and lower-cased.

    Component ids and document ids sometimes spell the same component
    with different underscoring (``bit_manipulation`` vs.
    ``bitmanipulation``). Comparing on the underscore-free form makes
    that difference invisible without introducing per-component config.
    """
    return text.replace("_", "").lower()


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def workproduct_rows(
    slug_norm: str,
    overrides: dict,
    workproducts: list[dict],
) -> str:
    """Render the work-product rows for one component or the feature.

    Each row has four cells: the work-product ``:need:`` link, its
    label, the realising document, and its status. The "Realized by"
    and "Status" cells are populated by sphinx-needs so their content
    stays in sync with the actual sphinx-needs data model:

    1. **Overrides** — when ``overrides['workproducts'][wp_key]`` names
       an explicit doc id, the row renders a direct ``:need:`` link
       and a ``:ndf:`copy('status', ...)``` call that pulls the doc's
       status field verbatim.
    2. **Filter** — otherwise, both cells render a ``.. needtable::``
       with the same filter (``type == "document"``, normalised-slug
       substring match on the doc id, ``realizes`` link containing
       ``wp['wp_id']``) but different ``:columns:``. If nothing matches,
       both cells are empty.
    """
    explicit = overrides.get("workproducts") or {}
    lines: list[str] = []
    for wp in workproducts:
        override_doc = explicit.get(wp["key"])
        lines.append(f"      * - :need:`{wp['wp_id']}`")
        lines.append(f"        - {wp['label']}")
        if override_doc:
            lines.append(f"        - :need:`{override_doc}`")
            lines.append(f"        - :ndf:`copy('status', need_id='{override_doc}')`")
        else:
            filter_expr = (
                f'type == "document" and '
                f'"{slug_norm}" in id.replace("_", "") and '
                f'"{wp["wp_id"]}" in realizes'
            )
            lines.append("        - .. needtable::")
            lines.append(f"             :filter: {filter_expr}")
            lines.append("             :columns: id")
            lines.append("             :style: table")
            lines.append("        - .. needtable::")
            lines.append(f"             :filter: {filter_expr}")
            lines.append("             :columns: status")
            lines.append("             :style: table")
    return "\n".join(lines)


def render_component(
    comp: dict,
    overrides: dict,
    workproducts: list[dict],
    coverage_data: dict,
) -> str:
    title = comp["title"]
    slug = comp["slug"]
    ref = "comp-" + slugify(title)
    return COMPONENT_TEMPLATE.format(
        ref=ref,
        title=title,
        title_underline="~" * len(title),
        comp_id=comp["id"],
        slug=slug,
        workproduct_rows=workproduct_rows(
            normalize_slug(slug), overrides, workproducts
        ),
        # Unit Test Coverage section disabled — see
        # ``templates.COMPONENT_COVERAGE_SECTION_DISABLED``. Restore by
        # passing ``coverage_intro=coverage_intro(comp, coverage_data)``.
    )


def render_feature(
    feature_id: str,
    feature_slug: str,
    feature_overrides: dict,
    feature_workproducts: list[dict],
) -> str:
    """Render the ``Feature`` section (Requirements / Architecture /
    Inspection Statistics), delegating all attribute filtering to
    sphinx-needs.

    Feature statistics filter ``feat_req`` / ``feat_arc_*`` by
    ``"{feature_id}" in belongs_to`` — the same link that the source
    RST declares — so the report tracks the sphinx-needs data model
    directly instead of guessing from id substrings. The Feature summary
    ``needtable`` pulls title / safety / security / status from the
    ``feat__*`` need itself. The Inspection Statistics work-product
    rows still substring-match the ``feature_slug`` against document
    ids because documents have no direct link back to the feature.
    """
    return FEATURE_TEMPLATE.format(
        feature_id=feature_id,
        feature_slug=feature_slug,
        feature_workproduct_rows=workproduct_rows(
            normalize_slug(feature_slug),
            feature_overrides,
            feature_workproducts,
        ),
    )


def render_overview(components: list[dict]) -> str:
    """Render the component overview as a ``.. needtable::``.

    Delegating to sphinx-needs means ``safety``/``security``/``status``
    come from its data model (validated, normalised, consistent with the
    rest of the site) rather than from raw strings scraped by our
    filesystem scan. Trade-off: the ``Component`` cell links to the
    need's detail page, not to the per-component section further down
    this page.
    """
    ids_literal = "[" + ", ".join(f'"{c["id"]}"' for c in components) + "]"
    return OVERVIEW_TEMPLATE.format(ids_literal=ids_literal)


def render_report(
    components: list[dict],
    feature_id: str | None,
    feature_slug: str | None,
    overrides_by_id: dict[str, dict],
    workproducts: list[dict],
    feature_workproducts: list[dict],
    coverage_data: dict,
) -> str:
    parts = [WP_TABLE_CSS]
    if feature_id is not None and feature_slug is not None:
        feature_overrides = overrides_by_id.get(feature_id, {})
        parts.append(
            render_feature(
                feature_id, feature_slug, feature_overrides, feature_workproducts
            )
        )
    parts += [
        COMPONENTS_HEADER,
        render_overview(components),
    ]
    for comp in components:
        overrides = overrides_by_id.get(comp["id"], {})
        parts.append(
            render_component(
                comp,
                overrides,
                workproducts,
                coverage_data,
            )
        )
    return "\n".join(parts)
