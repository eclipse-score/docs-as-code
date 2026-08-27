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
"""Rendering of the ``mod_ver_report`` need declaration."""

from __future__ import annotations

from .templates import MOD_VER_REPORT_TEMPLATE, NEEDS_TEMPLATE_NAME


def render_mod_ver_report(
    module_id: str,
    report_id: str,
    title: str,
    safety: str,
    security: str,
    status: str,
    verification_method: str,
    components: list[str],
    features: list[str],
    version: str = "1",
) -> str:
    """Render the ``.. mod_ver_report::`` need declaration for *module_id*.

    ``components`` and ``features`` are mandatory links of the
    ``mod_ver_report`` need type (see metamodel.yaml). They record which
    architecture needs the report describes, which serves two purposes: the
    ``mod_ver_report`` content template renders the report body from them, and
    score_metamodel's ``check_mod_ver_report_links`` graph check compares them
    against the module's ``includes`` and the components' ``belongs_to``.
    """
    return MOD_VER_REPORT_TEMPLATE.format(
        title=title,
        report_id=report_id,
        template_name=NEEDS_TEMPLATE_NAME,
        version=version,
        safety=safety,
        security=security,
        status=status,
        verification_method=verification_method,
        module_id=module_id,
        components=", ".join(components),
        features=", ".join(features),
    )
