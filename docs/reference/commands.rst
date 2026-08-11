.. ----------------------------------------------------------------------------
   Copyright (c) 2026 Contributors to the Eclipse Foundation

   See the NOTICE file(s) distributed with this work for additional
   information regarding copyright ownership.

   This program and the accompanying materials are made available under the
   terms of the Apache License Version 2.0 which is available at
   https://www.apache.org/licenses/LICENSE-2.0

   SPDX-License-Identifier: Apache-2.0
.. ----------------------------------------------------------------------------

Commands
========

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Target
     - What it does
   * - ``bazel run //:docs``
     - Builds documentation (also writes ``metrics.json``)
   * - ``bazel run //:docs_check``
     - Verifies documentation correctness
   * - ``bazel run //:docs_link_check``
     - Lists broken links
   * - ``bazel run //:traceability_gate``
     - Reads the pre-computed ``metrics.json`` and fails if coverage
       thresholds are not met. Use with ``--metrics-json``,
       ``--min-req-code``, ``--min-req-test``, ``--min-req-fully-linked``,
       ``--min-tests-linked`` flags.
   * - ``bazel run //:live_preview``
     - Creates a live preview of the documentation viewable in a local
       server
   * - ``bazel run //:ide_support``
     - Sets up a Python venv for esbonio (Remember to restart VS Code!)

Internal targets (do not use directly)
--------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Target
     - What it does
   * - ``bazel build //:needs_json``
     - Creates a ``needs.json`` file
   * - ``bazel build //:docs_sources``
     - Provides all the documentation source files
