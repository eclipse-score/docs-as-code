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
"""The ``.. module-verification-report::`` Sphinx directive."""

from __future__ import annotations

import re

from docutils import nodes
from docutils.statemachine import ViewList
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import nested_parse_with_titles

from .rendering import render_report
from .templates import DEFAULT_FEATURE_WORKPRODUCTS, DEFAULT_WORKPRODUCTS

# Strip an optional ``[version==N]`` qualifier from a component id.
_VERSION_QUALIFIER_RE = re.compile(r"\[version==\d+\]$")


def _parse_components(ids_str: str, component_prefix: str) -> list[dict]:
    """Parse a comma-separated list of component ids into component dicts.

    Each entry may carry an optional ``[version==N]`` qualifier which is
    stripped silently — the rendered report does not filter by version.

    The short slug is the component id with ``component_prefix`` removed
    (or the full id if the prefix is absent). The human-readable title is
    derived from the slug: underscores replaced with spaces, title-cased.
    """
    result = []
    for raw in ids_str.split(","):
        comp_id = _VERSION_QUALIFIER_RE.sub("", raw.strip())
        if not comp_id:
            continue
        slug = (
            comp_id[len(component_prefix) :]
            if component_prefix and comp_id.startswith(component_prefix)
            else comp_id
        )
        title = slug.replace("_", " ").title()
        result.append({"id": comp_id, "slug": slug, "title": title})
    return result


class ModuleVerificationReportDirective(SphinxDirective):
    """Expand to the per-module verification report body.

    Minimal usage::

        .. module-verification-report::
           :module-id: mod__mymodule
           :components: comp__mymodule_a, comp__mymodule_b

    ``feature-id`` and ``component-prefix`` are optional and derived from
    ``module-id`` when omitted.
    """

    required_arguments = 0
    optional_arguments = 0
    option_spec = {
        "module-id": str,
        "feature-id": str,
        "component-prefix": str,
        "components": str,
    }
    has_content = False

    def run(self) -> list[nodes.Node]:
        module_id = self.options.get("module-id", "")
        module_short = (
            module_id[len("mod__") :] if module_id.startswith("mod__") else module_id
        )
        component_prefix = self.options.get("component-prefix") or (
            "comp__" + module_short + "_" if module_short else "comp__"
        )
        feature_id: str | None = self.options.get("feature-id") or None
        feature_slug = (
            (feature_id.split("__", 1)[1] if "__" in feature_id else feature_id)
            if feature_id is not None
            else None
        )
        workproducts = DEFAULT_WORKPRODUCTS
        feature_workproducts = DEFAULT_FEATURE_WORKPRODUCTS

        components_str = self.options.get("components", "")
        components = _parse_components(components_str, component_prefix)
        if not components:
            error = self.state_machine.reporter.error(
                "module-verification-report: no components specified — "
                "add ':components: comp__<id>, ...' to the directive",
                line=self.lineno,
            )
            return [error]

        rst_text = render_report(
            components,
            feature_id,
            feature_slug,  # type: ignore[arg-type]
            workproducts,
            feature_workproducts,
        )
        view_list = ViewList()
        source = "<module-verification-report>"
        for lineno, line in enumerate(rst_text.splitlines()):
            view_list.append(line, source, lineno)

        # Parse into a plain container (not a ``nodes.section``): a section
        # wrapper would push every heading we emit one level deeper than the
        # surrounding document sections, so ``Component Overview`` would
        # render as ``<h4>`` instead of ``<h3>`` alongside
        # ``Feature Requirements Statistics``.
        container = nodes.container()
        container.document = self.state.document
        nested_parse_with_titles(self.state, view_list, container)  # type: ignore[arg-type]

        # Register this docname so the ``doctree-resolved`` hook in
        # ``testcase_annotations`` knows to decorate testcase back-links
        # with a coloured ``(passed)`` / ``(failed)`` badge here.
        if not hasattr(self.env, "module_verification_report_docnames"):
            self.env.module_verification_report_docnames = set()  # type: ignore[attr-defined]
        self.env.module_verification_report_docnames.add(self.env.docname)  # type: ignore[attr-defined]

        # Register module/feature/component metadata so the build-finished
        # consistency check can validate need links without a pre-scan.
        if not hasattr(self.env, "module_verification_report_registry"):
            self.env.module_verification_report_registry = {}  # type: ignore[attr-defined]
        self.env.module_verification_report_registry[module_id] = {  # type: ignore[attr-defined]
            "docname": self.env.docname,
            "feature_id": feature_id,
            "comp_ids": [c["id"] for c in components],
        }

        return container.children
