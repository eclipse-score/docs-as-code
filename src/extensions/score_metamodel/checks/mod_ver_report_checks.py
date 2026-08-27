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

A ``mod_ver_report`` need declares the module it belongs to (``belongs_to``)
and the architecture needs it describes (``components`` and ``features``, both
mandatory links). Its body is rendered by the ``mod_ver_report`` content
template from those same fields.

Because all of that lives in the needs graph, the report can be validated
against the needs it claims to describe:

1. ``components`` and the module's ``includes`` must name the *same* set. The
   report and the module are two independent statements about which components
   make up the module — if they disagree, one of them is stale. Both
   directions are reported, and independently: a report that skips a component
   of its module is exactly as wrong as one that describes a component the
   module does not have.
2. Every feature a listed component ``belongs_to`` must itself be listed in
   ``features``. A report spanning several features is fine — what is not fine
   is a component whose feature the report never mentions, because the
   feature-level statistics then silently omit it.

Everything here reports through :class:`CheckLogger` rather than raising: a
malformed report must not abort the whole docs build, and the author needs to
see every problem in one run, not just the first.
"""

from __future__ import annotations

from score_metamodel import (
    CheckLogger,
    graph_check,
)
from sphinx.application import Sphinx
from sphinx_needs.data import NeedsView
from sphinx_needs.need_item import NeedItem


def _linked_ids(need: NeedItem, link: str) -> list[str]:
    """Return the ids linked via *link*, or an empty list.

    A declared but unset link yields ``[]``. The ``or []`` also covers a need
    type that does not declare *link* at all, where the lookup yields ``None``.
    """
    return need.get(link) or []


def _join(ids: list[str]) -> str:
    """Render a list of need ids for a warning message."""
    return ", ".join(f"`{i}`" for i in sorted(ids))


def _resolve(
    report: NeedItem,
    link: str,
    all_needs: NeedsView,
    log: CheckLogger,
) -> list[NeedItem]:
    """Resolve the ids linked via *link* to needs, warning about unknown ones."""
    resolved: list[NeedItem] = []
    for need_id in _linked_ids(report, link):
        target = all_needs.get(need_id)
        if target is None:
            log.warning_for_need(
                report, f"`{link}` references `{need_id}`, which is not a known need."
            )
            continue
        resolved.append(target)
    return resolved


def _check_component_parity(
    report: NeedItem, module: NeedItem, log: CheckLogger
) -> None:
    """The report's ``components`` and the module's ``includes`` must match."""
    module_components = set(_linked_ids(module, "includes"))
    report_components = set(_linked_ids(report, "components"))
    module_id = module["id"]

    # The two directions are independent problems, so they are reported
    # independently — a report that lists a stale component must still be told
    # about the component it is missing.
    missing_from_report = module_components - report_components
    if missing_from_report:
        log.warning_for_need(
            report,
            f"does not list {_join(list(missing_from_report))} under "
            f"`components`, but `{module_id}` `includes` "
            f"{'them' if len(missing_from_report) > 1 else 'it'}. The "
            "verification report must describe every component of the module.",
        )

    missing_from_module = report_components - module_components
    if missing_from_module:
        log.warning_for_need(
            report,
            f"lists {_join(list(missing_from_module))} under `components`, but "
            f"`{module_id}` does not `includes` "
            f"{'them' if len(missing_from_module) > 1 else 'it'}.",
        )


def _check_features_included(
    report: NeedItem,
    features: list[NeedItem],
    components: list[NeedItem],
    log: CheckLogger,
) -> None:
    """Every feature a listed component belongs to must be listed too.

    A component may belong to more than one feature, and a report may span
    more than one feature, so this compares the *full* set of features reached
    through the components against the set the report declares.
    """
    listed_feature_ids = {feature["id"] for feature in features}

    # feature id -> the listed components that belong to it. Keyed by feature
    # so the warning can name both the feature that is missing and the
    # components that pointed at it.
    unlisted: dict[str, list[str]] = {}
    for component in components:
        for feature_id in _linked_ids(component, "belongs_to"):
            if feature_id not in listed_feature_ids:
                unlisted.setdefault(feature_id, []).append(component["id"])

    for feature_id in sorted(unlisted):
        components_str = _join(unlisted[feature_id])
        log.warning_for_need(
            report,
            f"does not list `{feature_id}` under `features`, but "
            f"{components_str} "
            f"{'belong' if len(unlisted[feature_id]) > 1 else 'belongs'} to it.",
        )


@graph_check
def check_mod_ver_report_links(
    app: Sphinx,
    all_needs: NeedsView,
    log: CheckLogger,
) -> None:
    """Validate that every ``mod_ver_report`` agrees with the needs it describes."""
    reports = all_needs.filter_is_external(False).filter_types(["mod_ver_report"])

    for report in reports.values():
        components = _resolve(report, "components", all_needs, log)
        features = _resolve(report, "features", all_needs, log)
        modules = _resolve(report, "belongs_to", all_needs, log)

        _check_features_included(report, features, components, log)

        if not modules:
            # `belongs_to` is a mandatory link: the option checks report it
            # missing, and _resolve already warned about an unresolvable id.
            # Nothing left to compare the components against.
            continue
        if len(modules) > 1:
            log.warning_for_need(
                report,
                f"`belongs_to` names {len(modules)} modules "
                f"({_join([m['id'] for m in modules])}); a verification report "
                "describes exactly one module.",
            )
        _check_component_parity(report, modules[0], log)
