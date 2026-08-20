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
       :feature-id: feat__baselibs
       :components: comp__baselibs_json,
                    comp__baselibs_bit_manipulation,
                    comp__baselibs_containers

An optional ``:config:`` YAML file can supply non-default workproducts or
per-component doc-id overrides for the rare case where component documents
do not follow the standard naming convention.

Implementation is split across:

* :mod:`.coverage`    — ``coverage_summary.json`` loading
* :mod:`.templates`   — RST templates + default workproduct lists + CSS
* :mod:`.rendering`   — template expansion / report body assembly
* :mod:`.directive`   — the ``ModuleVerificationReportDirective`` class
* :mod:`.testcase_annotations` — ``doctree-resolved`` badge decoration
  for ``testcase__…`` back-links on pages that render the directive
"""
from __future__ import annotations

from typing import Any

from .directive import ModuleVerificationReportDirective
from .testcase_annotations import (
    annotate_testcase_results,
    init_docnames,
    merge_docnames,
    purge_docname,
)


def setup(app: Any) -> dict:
    app.add_directive(
        "module-verification-report", ModuleVerificationReportDirective
    )
    app.connect("env-before-read-docs", init_docnames)
    app.connect("env-purge-doc", purge_docname)
    app.connect("env-merge-info", merge_docnames)
    app.connect("doctree-resolved", annotate_testcase_results)
    return {
        "version": "0.8",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
