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

Use this guide in repositories that consume docs-as-code as a Bazel
dependency.

Goals:

1. Publish traceability dashboards from repository needs.
2. Export machine-readable metrics.
3. Enforce CI thresholds with ``traceability_gate``.

What You Get
------------

With the ``docs(...)`` macro and ``score_metamodel`` as well as the ```score_metrics`` extensions enabled, your
repository can:

- build an HTML dashboard from its own Sphinx needs,
- include external needs from other repositories when desired,
- export ``needs.json`` and ``metrics.json`` for machine-readable reporting,
- gate CI on traceability thresholds via ``traceability_gate``.

Configuration
-------------

Default Behavior (No Configuration Needed)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, ``score_metrics`` autodiscovers requirement types from the
repository needs present in the current build.
Requirement types are identified from ``needs_types`` entries tagged with ``requirement``.

This is the recommended setup for most repositories.

Optional Override for Requirement Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If a repository needs to force a specific set of requirement types, set an
explicit override in ``docs/conf.py``:

.. code-block:: python

   score_metrics_requirement_types = "feat_req,comp_req,aou_req"

When this setting is provided, the explicit list is used instead of
autodiscovery.

Use ``score_metrics_include_external_needs = True`` in repositories that
intentionally aggregate requirements across module dependencies, such as
integration repositories, or combine it with the optional feature scope below.

Optional External Feature Scope
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A module repository can report on feature requirements maintained in another
repository, such as ``score``, without counting unrelated external requirements.
First import that repository's needs data through the existing external-needs
configuration, then configure the metrics in ``docs/conf.py``:

.. code-block:: python

   score_metrics_include_external_needs = True
   score_metrics_requirement_types = "feat_req,comp_req,aou_req"
   score_metrics_external_feature_ids = ["feat__lifecycle"]

Replace the example feature ID with the exact ID referenced by the imported
feature requirements' ``satisfied_by`` links. Multiple feature IDs are supported.
All local requirements of the selected requirement types remain included.
External requirements are included only if they are ``feat_req`` needs with a
``satisfied_by`` link to at least one selected feature. Requirements without
tests are still counted; unrelated external requirements are excluded.
Local tests can link to the imported requirements through ``fully_verifies``
or ``partially_verifies`` as usual. The metrics selection does not remove
imported needs from the documentation or from test-reference resolution.

This feature is opt-in: ``score_metrics_external_feature_ids`` defaults to
``[]``, preserving the existing local-only or full-aggregation behavior.
The scope has no effect while ``score_metrics_include_external_needs`` is
``False``. It does not import external needs automatically or change the
configured requirement types.

Building the Dashboard
----------------------

After building/running any docs and test command (i.e. ``bazel build //:needs_json`` or ``bazel run //:docs_check``, ``bazel run //:docs``, ``bazel test //...``):

The documentation build writes ``metrics.json`` via ``score_metrics``, and the ``needs_json`` artifact contains:

- ``_build/needs.json``
- ``_build/metrics.json``

The dashboard charts and the CI gate both use the same computed metrics.

``metrics.json`` Content
~~~~~~~~~~~~~~~~~~~~~~~~

The exported file contains a versioned set of fields:

- ``schema_version`` – schema version identifier.
- ``generated_by`` – identifier of the producer that generated this file.
- ``overall_metrics`` – requirement coverage aggregated over all requirement types.
- ``metrics_by_type`` – the same coverage numbers per requirement type.
- ``tests`` – testcase linkage statistics, including broken test references.
- ``verification_metrics`` – per-component verification status and coverage metrics
  for use by verification reports. Contains status distribution (valid, valid_inspected,
  invalid) and test coverage (fully_covered, partially_covered, not_covered) for
  both requirements and architecture elements, organized by component ID.

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

- No setting needed. Local-only scope is the default.
- Gate only on the needs owned by the repository itself.
- Use this for per-module implementation progress and traceability.

**Integration repository**

- Set ``score_metrics_include_external_needs = True``.
- Aggregate requirements across module dependencies when that is the intended
  repository purpose.
- Use this for system or integration-level dashboards.

CI Quality Gate
---------------

Any docs build (``bazel run //:docs``, ``bazel run //:docs_check``, etc.)
writes ``metrics.json`` alongside the build output. Run the gate on the
exported metrics:

.. code-block:: bash

   bazel run //:docs && \
   bazel run //:traceability_gate -- \
      --metrics-json bazel-bin/needs_json/_build/needs/metrics.json \
      --min-req-code 70 \
      --min-req-test 70 \
      --min-req-fully-linked 60 \
      --min-tests-linked 70

In CI, wire targets through Bazel dependencies so test execution and
docs generation happen before the gate target.

In larger repositories, define a dedicated wrapper target for your standard
gate thresholds so CI calls a single Bazel target.

Useful flags:

- ``--require-all-links`` for strict 100 percent gating

Recommended Rollout
-------------------

For a new consumer repository:

1. Start with local-only metrics.
2. Enable ``code_targets`` and verify ``source_code_link`` coverage first.
3. Add test metadata and verify ``testlink`` coverage.
4. Introduce modest thresholds in CI.
5. Raise thresholds over time as the repository matures.

..
   ╓                                                          ╖
   ║ Some portions generated by Github Copilot                ║
   ╙                                                          ╜

Needpie Usage Guide (Quick and Practical)
-----------------------------------------

Use these examples as ready-to-copy templates for dashboard-style pie charts.

Tips for readable charts
~~~~~~~~~~~~~~~~~~~~~~~~

- Keep labels short and audience-friendly.
- Put the most important category first.
- Use high-contrast colors that are easy to distinguish.
- Avoid red/green-only combinations when possible.

Recommended color palette
^^^^^^^^^^^^^^^^^^^^^^^^^

This palette is generally easier to read:

- ``#D32F2F`` (red)
- ``#F28E2B`` (orange)
- ``#59A14F`` (green)
- ``#B07AA1`` (purple)
- ``#FFC107`` (yellow)
- ``#4E79A7`` (blue)

Example 1: Overall view (including remaining/unlinked)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: rst

   .. needpie:: Overall Requirement Coverage (non-overlapping)
      :labels: Remaining (no links), Test Link Only, Code Link Only, Fully Linked (Both)
      :colors: #D32F2F, #F28E2B, #FFC107, #59A14F
      :filter-func: score_metrics.sphinx_filters.get_non_overlapping_link_metrics

This chart shows:

- remaining requirements (calculated from total),
- requirements with test link,
- requirements with code link,
- fully linked requirements.

.. needpie:: Overall Requirement Coverage (non-overlapping)
   :labels: Remaining (no links), Test Link Only, Code Link Only, Fully Linked (Both)
   :colors: #D32F2F, #F28E2B, #FFC107 , #59A14F
   :filter-func: score_metrics.sphinx_filters.get_non_overlapping_link_metrics

Example 2: Focused view (no total-based remainder)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This chart shows direct values only (no remaining slice):

- tool requirements with test link,
- tool requirements with code link,
- overall fully linked requirements.

.. needpie:: Tool Requirements Snapshot
   :labels: Tool Req With Test Link, Tool Req With Code Link, Fully Linked (Overall)
   :colors: #F28E2B, #FFC107, #59A14F
   :filter-func: score_metrics.sphinx_filters.get_just_metrics(metrics_by_type:tool_req:with_test_link,metrics_by_type:tool_req:with_code_link,overall_metrics:fully_linked)

Presentation checklist
~~~~~~~~~~~~~~~~~~~~~~

Before publishing, quickly verify:

- labels are understandable for non-technical readers,
- colors are distinct and readable on your page theme,
- title clearly says what the chart represents.
