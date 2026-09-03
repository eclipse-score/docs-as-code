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
"""
Renders a pre-built Lobster traceability report (JSON, as produced by the
rules_score ``component()``/``dependable_element()`` Bazel macros) as a table
directly inside a Sphinx page, via the ``.. lobster-traceability-report::``
directive.

Unlike ``score_source_code_linker`` (which turns ``bazel-testlogs/**/test.xml``
into sphinx-needs at build time), this extension reads a fixed, already-built
JSON file straight off disk when the directive runs. That keeps the Bazel
target that actually produces the JSON (e.g. a ``component()``/
``dependable_element()`` instance, which is ``testonly`` because it depends on
``cc_test`` targets) out of the (non-testonly) ``docs()`` Bazel dependency
graph entirely - the docs build never needs a Bazel-level dependency on it,
only the file to exist on disk, exactly like the bazel-testlogs scan does for
test results.
"""

from sphinx.application import Sphinx

from src.extensions.score_lobster_report.directive import (
    LobsterTraceabilityReportDirective,
)


def setup(app: Sphinx) -> dict[str, object]:
    app.add_directive(
        "lobster-traceability-report", LobsterTraceabilityReportDirective
    )

    return {
        "version": "1.0.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
