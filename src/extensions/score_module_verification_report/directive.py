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

from docutils import nodes
from docutils.statemachine import ViewList
from sphinx.util.docutils import SphinxDirective

# ``:template:`` is a Sphinx-Needs core option, so score_metamodel's option
# check accepts it on a metamodel-defined need type. It selects
# ``src/needs_templates/mod_ver_report.need``, which renders the whole report
# body from the need's own fields — this directive emits the need, nothing more.
NEEDS_TEMPLATE_NAME = "mod_ver_report"

MOD_VER_REPORT_TEMPLATE = """\
.. mod_ver_report:: {title}
   :id: {report_id}
   :template: {template_name}
   :version: {version}
   :safety: {safety}
   :security: {security}
   :status: {status}
   :verification_method: {verification_method}
   :belongs_to: {module_id}
   :components: {components}
   :features: {features}

"""

# Every option the directive requires. Each maps onto a mandatory option or
# link of the ``mod_ver_report`` need type (see metamodel.yaml), so none of
# them can be defaulted: guessing a traceability link would silently produce a
# dangling one whenever the guess is wrong.
_REQUIRED_OPTIONS = (
    "id",
    "module-id",
    "components",
    "features",
    "safety",
    "security",
    "status",
    "verification-method",
)


def _join_ids(ids_str: str) -> str:
    """Normalise a comma-separated option value onto a single line.

    Multi-line values are supported — docutils folds them into one string with
    newlines, which would break the emitted option. Version qualifiers such as
    ``[version==1]`` are passed through: Sphinx-Needs parses them itself, and
    stripping them here would silently drop the constraint.
    """
    return ", ".join(part.strip() for part in ids_str.split(",") if part.strip())


def _report_title(module_short: str) -> str:
    """Derive the report's human-readable title from the module slug.

    Only the display title is derived. The need's id comes from ``:id:`` and is
    passed through untouched, so the author stays in control of it.
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

    Every option is required. The directive is a shorthand: ``:id:`` becomes
    the need's id verbatim, the title is derived from ``:module-id:``, and the
    rest is passed straight through.

    The report *body* is not generated here — the emitted need selects the
    ``mod_ver_report`` content template, which Sphinx-Needs renders from the
    need's own fields.
    """

    required_arguments = 0
    optional_arguments = 0
    option_spec = {opt: str for opt in _REQUIRED_OPTIONS} | {"version": str}
    has_content = False

    def run(self) -> list[nodes.Node]:
        missing = [opt for opt in _REQUIRED_OPTIONS if not self.options.get(opt)]
        if missing:
            # Report here, where the author can see which directive is at
            # fault, rather than as a metamodel warning about a generated need.
            return [
                self.state_machine.reporter.error(
                    "module-verification-report: missing mandatory option(s) "
                    f"{', '.join(':' + m + ':' for m in missing)} required to "
                    "generate the mod_ver_report need",
                    line=self.lineno,
                )
            ]

        module_id = self.options["module-id"]
        module_short = (
            module_id[len("mod__") :] if module_id.startswith("mod__") else module_id
        )
        rst_text = MOD_VER_REPORT_TEMPLATE.format(
            title=_report_title(module_short),
            report_id=self.options["id"],
            template_name=NEEDS_TEMPLATE_NAME,
            version=self.options.get("version", "1"),
            safety=self.options["safety"],
            security=self.options["security"],
            status=self.options["status"],
            verification_method=self.options["verification-method"],
            module_id=module_id,
            components=_join_ids(self.options["components"]),
            features=_join_ids(self.options["features"]),
        )

        view_list = ViewList()
        for lineno, line in enumerate(rst_text.splitlines()):
            view_list.append(line, "<module-verification-report>", lineno)

        # A plain nested_parse is enough: the emitted block is a single
        # directive with no section titles.
        container = nodes.container()
        container.document = self.state.document
        self.state.nested_parse(view_list, self.content_offset, container)
        return container.children
