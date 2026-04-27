..
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

Build Dashboards and Quality Gates
==================================

This guide is for repositories that *consume* docs-as-code as a Bazel
dependency. Examples are module repositories and integration repositories that
want to:

1. publish their own traceability dashboards,
2. export ``metrics.json`` during documentation builds, and
3. enforce quality gates in CI.

The docs-as-code repository itself documents tooling coverage. Consumer
repositories use the same extensions to document *their own* requirements,
architecture, source-code links, and verification evidence.

What You Get
------------

When a consumer repository integrates docs-as-code correctly, it can:

- build an HTML dashboard from its own Sphinx needs,
- include external needs from other repositories when desired,
- export ``needs.json`` and ``metrics.json`` for machine-readable reporting,
- gate CI on traceability thresholds via ``traceability_gate``.

Typical Setup
-------------

1. Add docs-as-code as a Bazel dependency as described in :ref:`setup`.
2. Define the documentation target via the ``docs(...)`` macro.
3. Provide process or upstream needs via the ``data`` argument when cross-repo
   traceability is required.
4. Provide implementation sources via ``scan_code`` so ``source_code_link`` can
   be generated.
5. Add test metadata so ``testlink`` and testcase needs can be generated.

Minimal Consumer Example
------------------------

In ``BUILD``:

.. code-block:: starlark

   load("@score_docs_as_code//:docs.bzl", "docs")

   filegroup(
       name = "module_sources",
       srcs = glob([
           "src/**/*.py",
           "src/**/*.cpp",
           "src/**/*.h",
           "src/**/*.rs",
       ]),
   )

   docs(
       source_dir = "docs",
       data = [
           "@score_process//:needs_json",
       ],
       scan_code = [":module_sources"],
   )

In ``docs/conf.py``:

.. code-block:: python

   score_metamodel_requirement_types = "feat_req,comp_req,aou_req"
   score_metamodel_include_external_needs = False

Use ``score_metamodel_include_external_needs = True`` only in repositories that
intentionally aggregate traceability across dependencies, such as integration
repositories.

Building the Dashboard
----------------------

Run:

.. code-block:: bash

   bazel run //:docs

This generates HTML output under ``_build/``.

Run:

.. code-block:: bash

   bazel build //:needs_json

This generates machine-readable output under:

- ``bazel-bin/needs_json/_build/needs/needs.json``
- ``bazel-bin/needs_json/_build/needs/metrics.json``

The HTML dashboard and the exported ``metrics.json`` are backed by the same
traceability metric implementation, so the charts and the CI gate evaluate the
same data.

Inputs for Linkage Metrics
--------------------------

To get meaningful dashboard and gate values, consumer repositories typically
need three inputs:

1. Requirement and architecture needs in the documentation itself.
2. Source code references via :doc:`source_to_doc_links`.
3. Test metadata via :doc:`test_to_doc_links`.

If one of those inputs is missing, the related chart or gate metric will remain
empty or low.

Choosing Local vs Aggregated Views
----------------------------------

There are two common modes:

**Module repository**

- Set ``score_metamodel_include_external_needs = False``.
- Gate only on the needs owned by the repository itself.
- Use this for per-module implementation progress and traceability.

**Integration repository**

- Set ``score_metamodel_include_external_needs = True``.
- Aggregate requirements across module dependencies when that is the intended
  repository purpose.
- Use this for system or integration-level dashboards.

CI Quality Gate
---------------

After building ``//:needs_json``, run the gate on the exported metrics:

.. code-block:: bash

   bazel run //scripts_bazel:traceability_gate -- \
      --metrics-json bazel-bin/needs_json/_build/needs/metrics.json \
      --min-req-code 70 \
      --min-req-test 70 \
      --min-req-fully-linked 60 \
      --min-tests-linked 70

Useful flags:

- ``--require-all-links`` for strict 100 percent gating
- ``--fail-on-broken-test-refs`` to fail when testcase references point to
  unknown requirement IDs

Recommended Rollout
-------------------

For a new consumer repository:

1. Start with local-only metrics.
2. Enable ``scan_code`` and verify ``source_code_link`` coverage first.
3. Add test metadata and verify ``testlink`` coverage.
4. Introduce modest thresholds in CI.
5. Raise thresholds over time as the repository matures.

Related Guides
--------------

- :ref:`setup`
- :doc:`other_modules`
- :doc:`source_to_doc_links`
- :doc:`test_to_doc_links`
