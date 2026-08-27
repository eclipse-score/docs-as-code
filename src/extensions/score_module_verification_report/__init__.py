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
"""Sphinx extension that generates the per-module verification report body.

Usage in RST::

    .. module-verification-report::
       :module-id: mod__baselibs
       :features: feat__baselibs
       :safety: ASIL_B
       :security: YES
       :status: valid
       :verification-method: test_and_inspection
       :components: comp__baselibs_json,
                    comp__baselibs_bit_manipulation,
                    comp__baselibs_containers

``safety``/``security``/``status``/``verification-method`` are the
mandatory options of the sphinx-needs ``mod_ver_report`` need type, and
``components``/``features`` are its mandatory links (see metamodel.yaml). The
directive emits one such need — ``belongs_to`` the module, ``components`` and
``features`` passed straight through from the options of the same name — so
the report is machine-readable and its links are validated by
score_metamodel's need-link and graph checks, not just rendered RST.

Implementation is split across:

* :mod:`.templates`   — RST templates + default workproduct lists + CSS
* :mod:`.rendering`   — template expansion / report body assembly
* :mod:`.directive`   — the ``ModuleVerificationReportDirective`` class

Consistency of the emitted need with the rest of the needs graph (does the
module ``includes`` exactly the components the report lists? does every listed
component ``belongs_to`` a listed feature?) is validated by ``score_metamodel``
's ``check_mod_ver_report_links`` graph check, not by this extension.

Testcase back-links rendered by this directive are annotated with a
``(passed)`` / ``(failed)`` result badge by
``score_source_code_linker``'s ``doctree-resolved`` hook, not by this
extension.
"""

from __future__ import annotations

from typing import Any

from .directive import ModuleVerificationReportDirective
from .render_context import register_render_context


def setup(app: Any) -> dict:
    app.add_directive("module-verification-report", ModuleVerificationReportDirective)
    app.add_config_value(
        "mvr_coverage_lcov",
        "bazel-out/_coverage/_coverage_report.dat",
        "env",
    )
    # The ``mod_ver_report`` need template renders coverage tables, but LCOV
    # data lives on disk rather than in the needs graph — expose it as a
    # render-context helper the template can call.
    app.connect("config-inited", register_render_context)
    return {
        "version": "0.9",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
