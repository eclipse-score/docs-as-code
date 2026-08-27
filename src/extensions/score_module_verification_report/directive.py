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

from .rendering import render_mod_ver_report

# Strip an optional ``[version==N]`` qualifier from a need id.
_VERSION_QUALIFIER_RE = re.compile(r"\[version==\d+\]$")


def _parse_ids(ids_str: str) -> list[str]:
    """Parse a comma-separated option value into a list of need ids.

    Multi-line values are supported (docutils folds them into one string) and
    an optional ``[version==N]`` qualifier is stripped silently — the report
    does not filter by version.
    """
    ids = []
    for raw in ids_str.split(","):
        need_id = _VERSION_QUALIFIER_RE.sub("", raw.strip())
        if need_id:
            ids.append(need_id)
    return ids


# Mandatory options every ``mod_ver_report`` need requires (see
# metamodel.yaml) that this directive cannot derive on its own.
_MOD_VER_REPORT_OPTIONS = ("id", "safety", "security", "status", "verification-method")

# Mandatory *links* of the ``mod_ver_report`` need type. Both are populated
# from the directive option of the same name, so the option is required too —
# guessing a traceability link (e.g. deriving ``feat__<module>`` from
# ``:module-id:``) would silently produce a dangling link whenever the guess
# is wrong.
_MOD_VER_REPORT_LINKS = ("components", "features")


def _mod_ver_report_title(module_short: str) -> str:
    """Derive the report's human-readable title from the module slug.

    Only the display title is derived. The need's id comes from the
    directive's ``:id:`` option and is passed through untouched, so the
    author stays in control of it — ``mod_ver_report`` declares
    ``parts: 3`` in metamodel.yaml, and the metamodel's id checks report a
    value that does not follow that scheme.
    """
    return f"{module_short.replace('_', ' ').title()} Verification Report"


class ModuleVerificationReportDirective(SphinxDirective):
    """Emit the ``mod_ver_report`` need for one module.

    Usage::

        .. module-verification-report::
           :id: mod_vrep__mymodule__report
           :module-id: mod__mymodule
           :components: comp__mymodule_a, comp__mymodule_b
           :features: feat__mymodule
           :safety: QM
           :security: YES
           :status: valid
           :verification-method: test_and_inspection

    Every option is required: each maps onto a mandatory option or link of the
    sphinx-needs ``mod_ver_report`` need type (see metamodel.yaml). The
    directive is a shorthand — ``:id:`` becomes the need's id verbatim, the
    title is derived from ``:module-id:``, and the rest is passed straight
    through.

    The report *body* is not generated here. The emitted need selects the
    ``mod_ver_report`` content template
    (``src/needs_templates/mod_ver_report.need``), which Sphinx-Needs renders
    from the need's own fields.
    """

    required_arguments = 0
    optional_arguments = 0
    option_spec = {
        "id": str,
        "module-id": str,
        "components": str,
        "features": str,
        "safety": str,
        "security": str,
        "status": str,
        "verification-method": str,
        "version": str,
    }
    has_content = False

    def _error(self, message: str) -> list[nodes.Node]:
        return [
            self.state_machine.reporter.error(
                f"module-verification-report: {message}", line=self.lineno
            )
        ]

    def run(self) -> list[nodes.Node]:
        module_id = self.options.get("module-id", "")
        module_short = (
            module_id[len("mod__") :] if module_id.startswith("mod__") else module_id
        )

        parsed_links = {
            name: _parse_ids(self.options.get(name, ""))
            for name in _MOD_VER_REPORT_LINKS
        }

        # ``components`` and ``features`` are mandatory links of the
        # mod_ver_report need type, so an empty list cannot produce a valid
        # need — report it here, where the author can see which directive is
        # at fault, rather than as a metamodel warning about a generated need.
        empty_links = [n for n in _MOD_VER_REPORT_LINKS if not parsed_links[n]]
        if empty_links:
            return self._error(
                f"no {' or '.join(empty_links)} specified — add "
                + " and ".join(f"':{name}: <id>, ...'" for name in empty_links)
                + " to the directive"
            )

        missing = [opt for opt in _MOD_VER_REPORT_OPTIONS if not self.options.get(opt)]
        if missing:
            return self._error(
                "missing mandatory option(s) "
                f"{', '.join(':' + m + ':' for m in missing)} required to "
                "generate the mod_ver_report need"
            )

        report_id = self.options["id"]
        report_title = _mod_ver_report_title(module_short)
        rst_text = render_mod_ver_report(
            module_id=module_id,
            report_id=report_id,
            title=report_title,
            safety=self.options["safety"],
            security=self.options["security"],
            status=self.options["status"],
            verification_method=self.options["verification-method"],
            version=self.options.get("version", "1"),
            components=parsed_links["components"],
            features=parsed_links["features"],
        )

        view_list = ViewList()
        source = "<module-verification-report>"
        for lineno, line in enumerate(rst_text.splitlines()):
            view_list.append(line, source, lineno)

        container = nodes.container()
        container.document = self.state.document
        nested_parse_with_titles(self.state, view_list, container)  # type: ignore[arg-type]
        return container.children
