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
"""Module Verification Report.

One Need per module gives that module a report page whose sections behave like
ordinary RST: real anchors, real ToC entries, real ``:ref:`` targets, present in
every builder.

See ``directive.py`` for the design rules.  In short: the extension emits RST
and never reads the Need model; scope is a real link field validated by the
metamodel.

Lifecycle
---------
The extension deliberately has **no** build lifecycle hooks: no ``env-updated``
re-read, no ``build-finished`` consistency pass, no registry carried across
parallel workers, and no configuration of its own -- the template is the place
to change what a report says.  ``setup()`` points ``needs_template_folder`` at
the shipped templates and registers two directives.

The single ``config-inited`` handler exists only because directive registration
is last-one-wins and sphinx-needs registers ``mod_ver_report`` from its own
``config-inited`` handler (priority 500).  The handler below runs at priority
900 and does nothing but call ``add_directive`` twice.  It touches no
environment state and reads no needs.
"""

from __future__ import annotations

from score_module_verification_report import rendering
from score_module_verification_report.directive import (
    REPORT_NEED_DIRECTIVE,
    REPORT_TYPE,
    ModuleVerificationReportDirective,
)
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx_needs.directives.need import NeedDirective

from src.helper_lib import config_setdefault

__all__ = ["setup"]


class ReportNeedDirective(NeedDirective):
    """sphinx-needs' Need directive, reachable under an un-shadowed name.

    ``NeedDirective`` derives the need type from the directive name it was
    invoked as.  The public ``mod_ver_report`` name belongs to the report
    directive, so the generated RST calls this alias instead and it restores
    the intended type.
    """

    def run(self):  # type: ignore[no-untyped-def]
        self.name = REPORT_TYPE
        return super().run()


def _register_directives(app: Sphinx, config: Config) -> None:
    # Runs late on config-inited, after sphinx-needs registered a plain
    # NeedDirective under REPORT_TYPE. Registration only -- no model access.
    app.add_directive(REPORT_NEED_DIRECTIVE, ReportNeedDirective, override=True)
    app.add_directive(REPORT_TYPE, ModuleVerificationReportDirective, override=True)


def setup(app: Sphinx) -> dict[str, object]:
    app.setup_extension("sphinx_needs")
    # The default template uses grid/dropdown (sphinx_design) and needpie.
    app.setup_extension("sphinx_design")

    # The report body is a Sphinx-Needs template file: ``.need`` extension,
    # living in ``needs_template_folder`` next to every other need template.
    # Point that config at the folder shipped with docs-as-code unless the
    # project set it itself -- in which case the project's folder is searched
    # first and the shipped one is the fallback.
    config_setdefault(
        app.config, "needs_template_folder", str(rendering.shipped_template_folder())
    )

    app.connect("config-inited", _register_directives, priority=900)

    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
