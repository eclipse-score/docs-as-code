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
"""Sphinx extension providing the module verification report directive.

Usage in RST::

    .. module-verification-report::
       :id: mod_vrep__baselibs__report
       :module-id: mod__baselibs
       :features: feat__baselibs
       :components: comp__baselibs_json, comp__baselibs_containers
       :safety: ASIL_B
       :security: YES
       :status: valid
       :verification-method: test_and_inspection

The directive emits a single sphinx-needs ``mod_ver_report`` need. Its body —
feature summary and statistics, component overview, and one section per
component — comes from the ``mod_ver_report`` content template
(``src/needs_templates/mod_ver_report.need``), which Sphinx-Needs renders from
the need's own fields.

Consistency of the need with the rest of the graph — does the module
``includes`` exactly the components the report lists? does every listed
component ``belongs_to`` a listed feature? — is validated by
``score_metamodel``'s ``check_mod_ver_report_links`` graph check.
"""

from __future__ import annotations

from typing import Any

from .directive import ModuleVerificationReportDirective


def setup(app: Any) -> dict:
    app.add_directive("module-verification-report", ModuleVerificationReportDirective)
    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
