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

.. _module_verification_report:

Module Verification Report extension
====================================

``score_module_verification_report`` provides the
``.. module-verification-report::`` directive, which expands into the
standard per-module verification report: a feature summary, a component
overview table, and one detailed section per component. Traceability is
resolved by sphinx-needs at render time — the directive only emits
``.. needtable::`` / ``.. needpie::`` widgets with the right filters.

The extension is part of the :ref:`score_sphinx_bundle<extensions>`.
No external config file is required for the common case.

Typical usage (``verification_report/module_verification_report.rst``):

.. code-block:: rst

   .. module-verification-report::
      :module-id: mod__mymodule
      :components: comp__mymodule_a, comp__mymodule_b

.. _mvr_directive:

Options
-------

.. list-table::
   :header-rows: 1
   :widths: 22 12 66

   * - Option
     - Required
     - Description

   * - ``:module-id:``
     - yes
     - sphinx-needs id of the ``.. mod::`` need (e.g. ``mod__mymodule``).
       Drives defaults for ``:feature-id:`` and ``:component-prefix:``.

   * - ``:components:``
     - yes
     - Comma-separated list of ``.. comp::`` need ids. Multi-line values
       are supported. Optional ``[version==N]`` qualifiers are stripped.

   * - ``:feature-id:``
     - no
     - sphinx-needs id of the ``.. feat::`` need. Default:
       ``feat__<module-short>`` (derived from ``:module-id:``).

   * - ``:component-prefix:``
     - no
     - Prefix stripped from each component id to derive its slug (used
       for section headings and document-id matching). Default:
       ``comp__<module-short>_``.

   * - ``:safety:``
     - yes
     - ASIL classification of the module. One of ``QM`` or ``ASIL_B``.

   * - ``:security:``
     - yes
     - Whether the module is security-relevant. One of ``YES`` or ``NO``.

   * - ``:status:``
     - yes
     - Review status of the report. One of ``valid`` or ``invalid``.

   * - ``:verification-method:``
     - yes
     - Free-text description of how the module was verified, e.g.
       ``test_and_inspection``.

   * - ``:version:``
     - no
     - Version of the emitted ``mod_ver_report`` need. Default: ``1``.

Metamodel validation
--------------------

``:safety:``, ``:security:``, ``:status:``, ``:verification-method:`` and
``:version:`` are not just directive options — the directive uses them to
emit a single sphinx-needs ``mod_ver_report`` need (id
``mod_vrep__<module-short>__report``, linked ``belongs_to`` the module's
``.. mod::`` need). This need type, its id format and the allowed values
for each option are declared in ``score_metamodel``'s ``metamodel.yaml``
(``mod_ver_report`` entry).

Every generated need is checked against that definition by the
``score_metamodel`` Sphinx extension as part of the regular build. If any
value does not match the expected pattern (e.g. ``:safety: ASIL_D``, which
is not one of ``QM``/``ASIL_B``), a mandatory option is missing, or the id
does not follow the required ``<prefix>__<abbreviation>__<element>``
scheme, ``score_metamodel`` reports a warning. Since the documentation
build runs Sphinx with ``-W`` (warnings treated as errors), any such
mismatch aborts the build instead of silently producing an inconsistent
report.

Running tests and docs together: ``docs_and_test``
----------------------------------------------------

A verification report is only meaningful if it reflects a fresh test run.
Bazel itself has no way to make a build target depend on a test's
*execution*, so ``score_docs_as_code`` ships a small macro,
``docs_and_test`` (``@score_docs_as_code//:bzl/docs_and_test.bzl``), that
chains the two steps outside the dependency graph:

.. code-block:: python

   load("@score_docs_as_code//:bzl/docs_and_test.bzl", "docs_and_test")

   docs_and_test(
       name = "module_verification_report",
       test_targets = ["//score/..."],
       docs_target = "//:docs",
   )

Calling the macro declares two ``py_binary`` targets (declaration only —
neither runs anything at ``BUILD``-load time):

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Target
     - What ``bazel run`` does

   * - ``<name>``
     - Runs ``bazel coverage`` (or ``bazel test``) on ``test_targets``,
       then ``bazel run <docs_target>`` (default ``//:docs``) — builds
       static HTML.

   * - ``<name>_preview``
     - Same test/coverage step, then ``bazel run <preview_target>``
       (default ``//:live_preview``) — starts the live-reloading preview
       server instead of just building HTML. Omitted if
       ``preview_target = None`` is passed to the macro.

Each target is fully independent: running one does not run the other, and
running either does not build/execute both. The driver aborts the whole
pipeline on the first non-zero exit code, so a failing test (or coverage
run) prevents a stale or incomplete report from being built.

By default (``coverage = True``) the test step is
``bazel coverage --combined_report=lcov``, whose aggregated LCOV file is
what the ``.. module-verification-report::`` directive reads (via the
``mvr_coverage_lcov`` Sphinx config value) to render the coverage
statistics in the report. Set ``coverage = False`` to fall back to plain
``bazel test`` — faster, but without coverage numbers in the report.

Extra Bazel flags for the nested test/coverage invocation (e.g. a
``--config``) are not hard-coded in the macro; pass them after ``--`` on
the command line::

   bazel run //:module_verification_report -- \
       --test-flag=--config=bl-aarch64-linux

``--test-flag`` is repeatable and forwarded as-is to the underlying
``bazel test``/``bazel coverage`` call.
