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
"""Graph checks for ``mod_ver_report`` needs.

A ``mod_ver_report`` need is emitted by the
``.. module-verification-report::`` directive of
``score_module_verification_report``. It declares the module it belongs to
(``belongs_to``) and the artifacts the report covers (``covers``: the feature
and every component the report renders a section for).

Because all of that lives in the needs graph, the report can be validated
against the architecture needs it claims to describe:

1. ``covers`` and the module's ``includes`` must name the *same* components.
   The report and the module are two independent statements about which
   components make up the module — if they disagree, one of them is stale.
2. Every covered component must ``belongs_to`` every covered feature. A report
   that covers ``feat__x`` and ``comp__y`` asserts that ``comp__y`` is part of
   ``feat__x``; the component need has to agree.

Both directions of rule 1 are reported, but only the direction that was
already enforced before this check existed (component covered by the report,
missing from the module) is a hard warning. The opposite direction is reported
as a non-fatal "new check" so that existing modules with an incomplete report
do not break their build immediately.
"""

from __future__ import annotations

from typing import Any

from score_metamodel import (
    CheckLogger,
    graph_check,
)
from sphinx.application import Sphinx
from sphinx_needs.data import NeedsView
from sphinx_needs.need_item import NeedItem


def _resolve(
    report: NeedItem,
    link: str,
    all_needs: NeedsView,
    log: CheckLogger,
) -> list[NeedItem]:
    """Resolve the ids linked via *link* to needs, warning about unknown ones."""
    resolved: list[NeedItem] = []
    for need_id in report.get(link, []):
        target = all_needs.get(need_id)
        if target is None:
            log.warning_for_need(
                report, f"`{link}` references `{need_id}`, which is not a known need."
            )
            continue
        resolved.append(target)
    return resolved


def _check_component_parity(report: NeedItem, module: NeedItem, log: CheckLogger):
    module_components: set[str] = set(module.get("includes"))
    report_components: set[str] = set(report.get("components"))
    components_not_mention_in_report = module_components.difference(report_components)
    if components_not_mention_in_report:
        msg = f"Module includes components: {components_not_mention_in_report} that are not mentioned in the Module verification report: {report.id}"
        log.warning_for_need(report, msg)

        components_in_report_not_in_module = report_components.difference(
            module_components
        )
        if components_in_report_not_in_module:
            msg = f"Module verification Report: {report.id} mentiones components the linked Module:{report.belongs_to} does not mention. Components mentioned: {components_in_report_not_in_module}"
            log.warning_for_need(report, msg)


def _check_features_included(
    report: NeedItem, features: list[NeedItem], components: list[NeedItem], log
):
    comp_feat_dict = {c.id: c.get("belongs_to")[0] for c in components}
    features_in_components = set(comp_feat_dict.values())
    feats_missing_in_components = features_in_components.difference(set(features))
    if feats_missing_in_components:
        comp_feat_missing = [comp_feat_dict[feat] for feat in features_in_components]
        msg = f"Components: {comp_feat_missing} are mentioning Features: {features_in_components} that are not mentioned in the Module Verification Report: {report.id}"
        log.warning_for_need(report, msg)


@graph_check
def check_mod_ver_report_links(
    app: Sphinx,
    all_needs: NeedsView,
    log: CheckLogger,
) -> None:
    """Validate that every ``mod_ver_report`` agrees with the needs it covers."""
    reports = all_needs.filter_is_external(False).filter_types(["mod_ver_report"])

    for report in reports.values():
        # TODO: improve errors
        components = _resolve(report, "components", all_needs, log)
        features = _resolve(report, "features", all_needs, log)
        modules = _resolve(report, "belongs_to", all_needs, log)
        # There can only be one module linked to a mod_ver_report
        # Needed?
        assert modules
        if len(modules) != 1:
            msg = f"Only one module is allowed to be mentioned in Module Verification Report: {report.id}"
            log.warning_for_need(report, msg)
        module = modules[0]

        # Module should have all the same components as the mod_ver_report
        _check_component_parity(report, module, log)
        _check_features_included(report, features, components, log)
