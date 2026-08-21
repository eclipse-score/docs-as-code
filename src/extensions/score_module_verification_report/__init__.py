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

* :mod:`.templates`   — RST templates + default workproduct lists + CSS
* :mod:`.rendering`   — template expansion / report body assembly
* :mod:`.directive`   — the ``ModuleVerificationReportDirective`` class
* :mod:`.testcase_annotations` — ``doctree-resolved`` badge decoration
  for ``testcase__…`` back-links on pages that render the directive
* :mod:`.consistency_checks` — ``build-finished`` validation that every
  component is properly linked in the needs graph
"""

from __future__ import annotations

from typing import Any

from .consistency_checks import (
    check_consistency,
    init_registry,
    merge_registry,
    purge_registry,
)
from .directive import ModuleVerificationReportDirective
from .testcase_annotations import (
    annotate_testcase_results,
    init_docnames,
    merge_docnames,
    purge_docname,
)


def setup(app: Any) -> dict:
    app.add_directive("module-verification-report", ModuleVerificationReportDirective)
    app.add_config_value(
        "mvr_coverage_lcov",
        "bazel-out/_coverage/_coverage_report.dat",
        "env",
    )
    app.connect("env-before-read-docs", init_docnames)
    app.connect("env-before-read-docs", init_registry)
    app.connect("env-purge-doc", purge_docname)
    app.connect("env-purge-doc", purge_registry)
    app.connect("env-merge-info", merge_docnames)
    app.connect("env-merge-info", merge_registry)
    app.connect("doctree-resolved", annotate_testcase_results)
    app.connect("build-finished", check_consistency)
    return {
        "version": "0.9",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
