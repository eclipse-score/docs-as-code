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
       :config: reporting/module_verification_report.yaml   # optional

The config file has the shape::

    module_id: mod__baselibs
    # optional; derived from module_id if omitted
    component_prefix: comp__baselibs_
    # optional; standard workproducts checked per component
    workproducts:
      - key: requirements_inspect
        label: Requirements Inspection
        wp_id: wp__requirements_inspect
      - ...
    # optional; per-component overrides for irregular cases (documents
    # whose id does not contain the component slug, e.g.
    # ``comp__baselibs_nlohman_json`` -> ``doc__json_*``)
    overrides:
      comp__baselibs_some_component:
        workproducts:
          requirements_inspect: doc__some_component_req_inspection
          ...

Implementation is split across:

* :mod:`.scanner`     — filesystem scan for ``.. mod::`` / ``.. comp::``
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
from .scanner import scan_source_tree
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
    app.connect("env-before-read-docs", scan_source_tree)
    app.connect("env-before-read-docs", init_docnames)
    app.connect("env-purge-doc", purge_docname)
    app.connect("env-merge-info", merge_docnames)
    app.connect("doctree-resolved", annotate_testcase_results)
    return {
        "version": "0.7",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
