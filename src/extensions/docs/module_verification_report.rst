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
