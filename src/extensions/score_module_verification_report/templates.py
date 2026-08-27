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
"""The RST emitted by the ``.. module-verification-report::`` directive.

Only the ``mod_ver_report`` need declaration lives here. The report *body* —
feature statistics, component overview, per-component sections, work-product
and coverage tables — is a Sphinx-Needs content template,
``src/needs_templates/mod_ver_report.need``, selected via the ``:template:``
option below. Sphinx-Needs renders it from the need's own fields, so the body
follows the needs model instead of a second, parallel description of it.
"""

from __future__ import annotations

# ``:template:`` is a Sphinx-Needs core option, so score_metamodel's
# option check accepts it on a metamodel-defined need type.
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
