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
"""Scope rule for module verification reports.

The report page rendered by ``score_module_verification_report`` needs its
component list authored on the Need, because sections must exist at read time.
That makes drift possible, so the rule below makes drift *detected*, never
silently corrected: the build fails and someone edits one line.

The rule is bidirectional and lives here -- in the metamodel -- rather than in
the rendering extension, so it applies to all reports regardless of how (or
whether) they are rendered.

The YAML ``graph_checks`` DSL compares an attribute of a linked need against a
constant; it cannot express set equality between two link fields, which is why
this one check is written in Python.
"""

from score_metamodel import CheckLogger, graph_check
from sphinx.application import Sphinx
from sphinx_needs.data import NeedsView
from sphinx_needs.need_item import NeedItem

REPORT_TYPE = "mod_ver_report"
MODULE_TYPE = "mod"
COMPONENT_TYPE = "comp"


def _link_ids(need: NeedItem, option: str) -> list[str]:
    value = need.get(option, None) or []
    if isinstance(value, str):
        return [value]
    return list(value)


@graph_check
def check_mod_ver_report_scope(app: Sphinx, needs: NeedsView, log: CheckLogger) -> None:
    """``mod_ver_report.covers`` must match ``mod.includes`` exactly.

    * a component included by the module but missing from ``:covers:`` has no
      section in the report -- the report silently under-reports its scope.
    * a component in ``:covers:`` that the module does not include claims
      verification of something outside the module.

    Only ``comp`` targets participate; ``:covers:`` may also point at
    requirements or other artifacts and those are left alone.
    """
    for need in needs.values():
        if need["type"] != REPORT_TYPE:
            continue

        covered_components = {
            need_id
            for need_id in _link_ids(need, "covers")
            if need_id in needs and needs[need_id]["type"] == COMPONENT_TYPE
        }

        for module_id in _link_ids(need, "belongs_to"):
            module = needs.get(module_id, None)
            if module is None or module["type"] != MODULE_TYPE:
                # Wrong or dangling belongs_to target is reported by the
                # regular link checks; nothing to add here.
                continue

            included = set(_link_ids(module, "includes"))

            for missing in sorted(included - covered_components):
                log.warning_for_option(
                    need,
                    "covers",
                    f"does not cover '{missing}', which is included by "
                    f"'{module_id}'. Add it to ':covers:' so the report gets a "
                    "section for it.",
                )

            for extra in sorted(covered_components - included):
                log.warning_for_option(
                    need,
                    "covers",
                    f"covers '{extra}', which is not included by '{module_id}'.",
                )
