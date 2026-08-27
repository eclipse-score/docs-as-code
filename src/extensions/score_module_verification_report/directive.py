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

from .coverage import load_coverage
from .rendering import render_report
from .templates import DEFAULT_FEATURE_WORKPRODUCTS, DEFAULT_WORKPRODUCTS

# Strip an optional ``[version==N]`` qualifier from a component id.
_VERSION_QUALIFIER_RE = re.compile(r"\[version==\d+\]$")


def _parse_needs(ids_str: str, prefix: str) -> list[dict]:
    """Parse a comma-separated list of need ids into id/slug/title dicts.

    Each entry may carry an optional ``[version==N]`` qualifier which is
    stripped silently — the rendered report does not filter by version.

    The short slug is the need id with *prefix* removed (or the full id if the
    prefix is absent). The human-readable title is derived from the slug:
    underscores replaced with spaces, title-cased.

    Used for both ``:components:`` (with the ``comp__<module>_`` prefix) and
    ``:features:`` (with the generic ``feat__`` prefix).
    """
    result = []
    for raw in ids_str.split(","):
        need_id = _VERSION_QUALIFIER_RE.sub("", raw.strip())
        if not need_id:
            continue
        slug = (
            need_id[len(prefix) :] if prefix and need_id.startswith(prefix) else need_id
        )
        title = slug.replace("_", " ").title()
        result.append({"id": need_id, "slug": slug, "title": title})
    return result


def _parse_components(ids_str: str, component_prefix: str) -> list[dict]:
    """Parse the ``:components:`` option. See :func:`_parse_needs`."""
    return _parse_needs(ids_str, component_prefix)


def _parse_features(ids_str: str) -> list[dict]:
    """Parse the ``:features:`` option. See :func:`_parse_needs`."""
    return _parse_needs(ids_str, "feat__")


# Mandatory options every ``mod_ver_report`` need requires (see
# metamodel.yaml) that this directive cannot derive on its own.
_MOD_VER_REPORT_OPTIONS = ("safety", "security", "status", "verification-method")

# Mandatory *links* of the ``mod_ver_report`` need type. Both are populated
# from the directive option of the same name, so the option is required too —
# guessing a traceability link (e.g. deriving ``feat__<module>`` from
# ``:module-id:``) would silently produce a dangling link whenever the guess
# is wrong.
_MOD_VER_REPORT_LINKS = ("components", "features")


def _mod_ver_report_id_and_title(module_short: str) -> tuple[str, str]:
    """Derive the ``mod_vrep__...`` need id and its human-readable title
    from the module slug.

    The id follows the ``<Req Type>__<Abbreviations>__<Architectural
    Element>`` scheme mandated for 3-part need types (``mod_ver_report``
    declares ``parts: 3`` in metamodel.yaml), so exactly two ``__``
    separators are required: ``mod_vrep__<module_short>__report``.
    """
    title_case = module_short.replace("_", " ").title()
    return f"mod_vrep__{module_short}__report", f"{title_case} Verification Report"


class ModuleVerificationReportDirective(SphinxDirective):
    """Expand to the per-module verification report body.

    Minimal usage::

        .. module-verification-report::
           :module-id: mod__mymodule
           :components: comp__mymodule_a, comp__mymodule_b
           :features: feat__mymodule
           :safety: QM
           :security: YES
           :status: valid
           :verification-method: test_and_inspection

    ``component-prefix`` is optional and derived from ``module-id`` when
    omitted. Everything else is required, because it maps onto a mandatory
    option or link of the sphinx-needs ``mod_ver_report`` need type (see
    metamodel.yaml) — this directive emits one such need so the report is
    machine-readable, not just a rendered page.

    The ``:components:`` and ``:features:`` options are named after the need
    links they populate: each is a comma-separated id list that is passed
    straight through to the emitted need.
    """

    required_arguments = 0
    optional_arguments = 0
    option_spec = {
        "module-id": str,
        "features": str,
        "component-prefix": str,
        "components": str,
        "safety": str,
        "security": str,
        "status": str,
        "verification-method": str,
        "version": str,
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
        workproducts = DEFAULT_WORKPRODUCTS
        feature_workproducts = DEFAULT_FEATURE_WORKPRODUCTS

        components = _parse_components(
            self.options.get("components", ""), component_prefix
        )
        features = _parse_features(self.options.get("features", ""))

        # ``components`` and ``features`` are mandatory links of the
        # mod_ver_report need type, so an empty list cannot produce a valid
        # need — report it here, where the author can see which directive is
        # at fault, rather than as a metamodel warning about a generated need.
        parsed_links = {"components": components, "features": features}
        empty_links = [n for n in _MOD_VER_REPORT_LINKS if not parsed_links[n]]
        if empty_links:
            error = self.state_machine.reporter.error(
                "module-verification-report: no "
                f"{' or '.join(empty_links)} specified — add "
                + " and ".join(f"':{name}: <id>, ...'" for name in empty_links)
                + " to the directive",
                line=self.lineno,
            )
            return [error]

        missing = [opt for opt in _MOD_VER_REPORT_OPTIONS if not self.options.get(opt)]
        if missing:
            error = self.state_machine.reporter.error(
                "module-verification-report: missing mandatory option(s) "
                f"{', '.join(':' + m + ':' for m in missing)} required to "
                "generate the mod_ver_report need",
                line=self.lineno,
            )
            return [error]

        report_id, report_title = _mod_ver_report_id_and_title(module_short)
        mod_ver_report = {
            "module_id": module_id,
            "report_id": report_id,
            "title": report_title,
            "safety": self.options["safety"],
            "security": self.options["security"],
            "status": self.options["status"],
            "verification_method": self.options["verification-method"],
            "version": self.options.get("version", "1"),
            # The two mandatory links, passed straight through from the
            # options of the same name.
            "components": [c["id"] for c in components],
            "features": [f["id"] for f in features],
        }

        rst_text = render_report(
            components,
            features,
            workproducts,
            feature_workproducts,
            coverage_records=load_coverage(
                getattr(self.config, "mvr_coverage_lcov", "")
            ),
            mod_ver_report=mod_ver_report,
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

        return container.children
