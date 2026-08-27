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

from .coverage import FileCoverage, coverage_rows, records_for_slug
from .templates import (
    COMPONENT_COVERAGE_TEMPLATE,
    COMPONENT_TEMPLATE,
    COMPONENTS_HEADER,
    COVERAGE_EMPTY_BODY,
    COVERAGE_TABLE_HEADER,
    FEATURE_TEMPLATE,
    MOD_VER_REPORT_TEMPLATE,
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
    workproducts: list[dict],
) -> str:
    """Render the work-product rows for one component or the feature.

    Each row has four cells: the work-product ``:need:`` link, its
    label, the realising document, and its status. The "Realized by"
    and "Status" cells are both rendered as ``.. needtable::`` with the
    same filter (``type == "document"``, normalised-slug substring match
    on the doc id, ``realizes`` link containing ``wp['wp_id']``) but
    different ``:columns:``. If nothing matches, both cells are empty.
    """
    lines: list[str] = []
    for wp in workproducts:
        lines.append(f"      * - :need:`{wp['wp_id']}`")
        lines.append(f"        - {wp['label']}")
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
    workproducts: list[dict],
    coverage_records: list[FileCoverage] | None = None,
) -> str:
    title = comp["title"]
    slug = comp["slug"]
    ref = "comp-" + slugify(title)
    slug_norm = normalize_slug(slug)
    matched = records_for_slug(coverage_records or [], slug_norm)
    if matched:
        coverage_body = COVERAGE_TABLE_HEADER + coverage_rows(matched)
    else:
        coverage_body = COVERAGE_EMPTY_BODY
    coverage_block = COMPONENT_COVERAGE_TEMPLATE.format(coverage_body=coverage_body)
    return COMPONENT_TEMPLATE.format(
        ref=ref,
        title=title,
        title_underline="~" * len(title),
        comp_id=comp["id"],
        slug=slug,
        workproduct_rows=workproduct_rows(slug_norm, workproducts),
        coverage_block=coverage_block,
    )


def render_feature(
    feature_id: str,
    feature_slug: str,
    feature_workproducts: list[dict],
    heading: str = "Feature",
) -> str:
    """Render the ``Feature`` section (Requirements / Architecture /
    Inspection Statistics), delegating all attribute filtering to
    sphinx-needs.

    *heading* names the section. A report normally covers a single feature and
    keeps the plain ``Feature`` heading; when ``:features:`` lists more than
    one, :func:`render_report` passes a per-feature heading so the page does
    not repeat the same title.

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
        feature_heading=heading,
        feature_heading_underline="-" * len(heading),
        feature_id=feature_id,
        feature_slug=feature_slug,
        feature_workproduct_rows=workproduct_rows(
            normalize_slug(feature_slug),
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


def render_mod_ver_report(
    module_id: str,
    report_id: str,
    title: str,
    safety: str,
    security: str,
    status: str,
    verification_method: str,
    components: list[str],
    features: list[str],
    version: str = "1",
) -> str:
    """Render the ``.. mod_ver_report::`` need declaration for *module_id*.

    ``components`` and ``features`` are mandatory links of the
    ``mod_ver_report`` need type (see metamodel.yaml): they record which
    architecture needs this report describes. Emitting them puts the report
    into the needs graph, which is what lets score_metamodel's
    ``check_mod_ver_report_links`` graph check compare it against the module's
    ``includes`` and the components' ``belongs_to``.
    """
    return MOD_VER_REPORT_TEMPLATE.format(
        title=title,
        report_id=report_id,
        version=version,
        safety=safety,
        security=security,
        status=status,
        verification_method=verification_method,
        module_id=module_id,
        components=", ".join(components),
        features=", ".join(features),
    )


def render_report(
    components: list[dict],
    features: list[dict],
    workproducts: list[dict],
    feature_workproducts: list[dict],
    coverage_records: list[FileCoverage] | None = None,
    mod_ver_report: dict | None = None,
) -> str:
    """Assemble the full report body.

    *features* mirrors *components*: a list of ``{"id", "slug"}`` dicts, one
    per id in the directive's ``:features:`` option. One ``Feature`` section is
    rendered per entry; with more than one the heading is qualified with the
    feature slug so the page has no repeated titles.
    """
    parts = [WP_TABLE_CSS]
    if mod_ver_report is not None:
        parts.append(render_mod_ver_report(**mod_ver_report))
    for feature in features:
        heading = (
            "Feature"
            if len(features) == 1
            else f"Feature: {feature['slug'].replace('_', ' ').title()}"
        )
        parts.append(
            render_feature(
                feature["id"], feature["slug"], feature_workproducts, heading
            )
        )
    parts += [
        COMPONENTS_HEADER,
        render_overview(components),
    ]
    for comp in components:
        parts.append(render_component(comp, workproducts, coverage_records))
    return "\n".join(parts)
