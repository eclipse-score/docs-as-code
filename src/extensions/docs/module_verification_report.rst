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
``.. module-verification-report::`` directive, which emits the module's
``mod_ver_report`` need. The report body — a feature summary, a component
overview table, and one detailed section per component — is a Sphinx-Needs
content template (``src/needs_templates/mod_ver_report.need``) that the need
selects via ``:template:``. Traceability is resolved by sphinx-needs at render
time: the template only emits ``.. needtable::`` / ``.. needpie::`` widgets
with the right filters.

The extension is part of the :ref:`score_sphinx_bundle<extensions>`.
No external config file is required for the common case.

Typical usage (``verification_report/module_verification_report.rst``):

.. code-block:: rst

   .. module-verification-report::
      :module-id: mod__mymodule
      :components: comp__mymodule_a, comp__mymodule_b
      :features: feat__mymodule
      :safety: QM
      :security: YES
      :status: valid
      :verification-method: test_and_inspection

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
       Also names the module whose component-id prefix
       (``comp__<module-short>_``) the template strips to derive component
       slugs and titles.

   * - ``:components:``
     - yes
     - Comma-separated list of ``.. comp::`` need ids. Named after the
       ``components`` link of the ``mod_ver_report`` need type, which it
       populates verbatim. Multi-line values are supported. Optional
       ``[version==N]`` qualifiers are stripped.

   * - ``:features:``
     - yes
     - Comma-separated list of ``.. feat::`` need ids. Named after the
       ``features`` link of the ``mod_ver_report`` need type, which it
       populates verbatim. Usually a single id; one ``Feature`` section is
       rendered per entry. Not derived from ``:module-id:`` — guessing a
       mandatory traceability link would silently produce a dangling link
       whenever the guess is wrong.

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
``.. mod::`` need). ``:components:`` and ``:features:`` are passed straight
through to the need's ``components`` and ``features`` links, which
``metamodel.yaml`` declares mandatory and types to ``comp`` / ``feat``. This
need type, its id format and the allowed values for each option are declared
in ``score_metamodel``'s ``metamodel.yaml`` (``mod_ver_report`` entry).

Every generated need is checked against that definition by the
``score_metamodel`` Sphinx extension as part of the regular build. If any
value does not match the expected pattern (e.g. ``:safety: ASIL_D``, which
is not one of ``QM``/``ASIL_B``), a mandatory option is missing, or the id
does not follow the required ``<prefix>__<abbreviation>__<element>``
scheme, ``score_metamodel`` reports a warning. Since the documentation
build runs Sphinx with ``-W`` (warnings treated as errors), any such
mismatch aborts the build instead of silently producing an inconsistent
report.

Graph consistency
-----------------

Because the emitted need records which architecture needs the report
describes, the report can be cross-checked against them. That is done by
``score_metamodel``'s ``check_mod_ver_report_links`` graph check
(``src/extensions/score_metamodel/checks/mod_ver_report_checks.py``), which
runs together with every other metamodel check — there is no separate
build-finished pass any more.

It enforces two rules per ``mod_ver_report`` need:

#. The need's ``components`` and the module's ``:includes:`` must be the same
   set. The report and the module are two independent statements about which
   components make up the module; if they disagree, one of them is stale. Both
   directions are warnings: a report that skips a component of its module is
   exactly as wrong as one that describes a component the module does not
   have.
#. Every listed component must ``:belongs_to:`` one of the listed features. A
   report naming ``:features: feat__x`` and ``:components: comp__y`` asserts
   that ``comp__y`` is part of ``feat__x``; the ``.. comp::`` need has to say
   so too.

Ids in ``:components:`` or ``:features:`` that do not resolve to a need are
reported as well. Every problem is reported as a warning rather than raised,
so one build surfaces all of them.

Like every other graph check, it can be disabled or run in isolation via the
``score_metamodel_checks`` config value, e.g.
``score_metamodel_checks = "check_mod_ver_report_links"``.

The report template
-------------------

The body lives in ``src/needs_templates/mod_ver_report.need`` and is rendered
by Sphinx-Needs, not by this extension. Two consequences are worth knowing:

*Templates render during the read phase*, when the need is created and the
needs graph does not exist yet. The template therefore never looks other needs
up. It reads ``belongs_to`` / ``components`` / ``features`` off the need
itself, derives component slugs and titles from the ids by string
manipulation, and leaves everything else to ``needtable`` / ``needpie``, which
resolve at write time.

*A need's content cannot open new sections*, so the report uses
``.. rubric::`` where a standalone page would use headings. Rubrics carry no
TOC entries; each component section is still a link target
(``comp-<slug-with-dashes>``).

Coverage is the one thing the template cannot reach on its own — LCOV data is
a file on disk, not a need. ``render_context.py`` registers a
``mvr_coverage(slug)`` helper in ``needs_render_context`` that returns
ready-made table rows for a component, or an empty string when there is no
match, and the template renders either the table or a "no coverage data" note.
The LCOV file is parsed once per build, on first use.
