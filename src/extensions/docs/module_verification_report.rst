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

``score_module_verification_report`` provides a single Sphinx directive,
``.. module-verification-report::``, that expands into the standard
per-module verification report body: one feature-level section, one
component overview table, and one detailed section per component. The
extension does **not** re-implement any traceability logic — every
attribute, link and status shown in the report is resolved by
sphinx-needs at render time from ``.. needtable::`` / ``.. needpie::``
widgets that the directive emits.

Typical use is in a module's ``verification_report/module_verification_report.rst``:

.. code-block:: rst

   Auto-generated Report
   ---------------------

   .. module-verification-report::
      :module-id: mod__mymodule

A separate config file is only needed for the rare case of non-default
workproducts or per-component doc-id overrides (see ``:config:`` below).

The extension is shipped as part of the
:ref:`score_sphinx_bundle<extensions>`; consumers only need to add
``score_docs_as_code`` and reference the directive.

At a glance
-----------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Aspect
     - Contract

   * - Directive
     - ``.. module-verification-report::`` — no arguments, no content;
       ``:module-id:`` is the only required option for the common case.

   * - Key options
     - ``:module-id:``, ``:feature-id:``, ``:component-prefix:`` as
       direct RST options; ``:config:`` YAML for advanced overrides only.

   * - Reads from the source tree
     - Every ``.. mod::`` and ``.. comp::`` need, discovered by a
       shallow regex scan at ``env-before-read-docs`` time.

   * - Reads from JSON
     - ``<srcdir>/reporting/coverage_summary.json`` (optional; produced
       by ``tools/extract_coverage.py``).

   * - Delegates to sphinx-needs
     - Status, safety, security, requirement / architecture element
       tables, pie charts, "Realized by" cells.

   * - Parallel-read safe
     - Yes (``parallel_read_safe = True``). The filesystem scan is
       reproducible in every worker.

.. _mvr_directive:

Directive reference
-------------------

.. code-block:: rst

   .. module-verification-report::
      :module-id: mod__mymodule
      :feature-id: feat__mymodule      # optional — derived from module-id
      :component-prefix: comp__my_    # optional — derived from module-id
      :config: path/to/overrides.yaml  # optional — for WP overrides only

**Arguments**
   None.

**Content**
   None (``has_content = False``).

**Options**

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Option
     - Meaning

   * - ``:module-id:``
     - The sphinx-needs id of the ``.. mod::`` need that owns this
       report. Effectively required — omitting it leaves ``module_id``
       as the empty string and the ``.. mod::`` lookup will fail.
       **Takes precedence** over the same field in ``:config:``.

   * - ``:feature-id:``
     - The sphinx-needs id of the ``.. feat::`` need for the feature
       section. Defaults to ``feat__<module-short>`` (derived from
       ``:module-id:`` by stripping the ``mod__`` prefix).
       **Takes precedence** over ``:config:``.

   * - ``:component-prefix:``
     - Prefix used to strip the module slug from each component id when
       generating short slugs for anchors and coverage lookup. Defaults
       to ``comp__<module-short>_``. **Takes precedence** over
       ``:config:``.

   * - ``:config:``
     - Optional path to a YAML config file, resolved relative to
       ``srcdir``. In the common case this option is **not needed** — it
       is only required for non-default workproduct lists or
       per-component doc-id overrides. ``module_id`` / ``feature_id`` /
       ``component_prefix`` in the file are ignored when the
       corresponding directive option is set.

**Errors** (fatal — the directive returns an ``error`` node):

* ``no '.. mod::' need with id '<module_id>' found in the source tree``
  — the config's ``module_id`` does not match any ``.. mod::`` directive
  visible under ``srcdir``.
* ``'<module_id>' has no resolvable components in ':includes:'`` — the
  ``.. mod::`` need was found but no whitelisted component id matched a
  ``.. comp::`` directive.

**Warnings** (non-fatal):

* ``'<module_id>' includes '<id>' but no matching '.. comp::' need was
  found`` — one entry of ``:includes:`` is dangling; the report still
  renders for the remaining components.
* ``config not found: <abs path>`` — the ``:config:`` path does not
  exist; the report falls back to defaults and will almost certainly
  fail the ``mod`` lookup.

.. _mvr_config:

Config file schema (advanced)
------------------------------

A ``:config:`` YAML file is only needed when the default workproducts do not
match or when specific components use non-standard document-id naming.
Fields that duplicate directive options (``module_id``, ``feature_id``,
``component_prefix``) are ignored when the corresponding RST option is set.

.. code-block:: yaml

   # Ignored if :module-id: is set on the directive.
   module_id: mod__<module>

   # Ignored if :component-prefix: is set. Default: ``comp__<module>_``.
   component_prefix: comp__<module>_

   # Ignored if :feature-id: is set. Default: ``feat__<module>``.
   feature_id: feat__<module>

   # Optional. Override the default five standard SCORE workproducts.
   workproducts:
     - key: <stable_short_key>          # only used for override lookup
       label: <human-readable label>    # shown in the "Kind" column
       wp_id: wp__<work_product>        # sphinx-needs id

   # Optional. Feature-level work products. Default: Requirements
   # Inspection + Architecture Inspection only.
   feature_workproducts:
     - key: ...
       label: ...
       wp_id: ...

   # Optional. Per-need overrides for the "Realized by" / "Status"
   # cells. Keyed by the ``.. comp::`` need id, or by the ``feat__``
   # need id for feature-level overrides.
   overrides:
     comp__<module>_<slug>:
       workproducts:
         # For each row you want to pin explicitly, map the WP ``key``
         # (see above) to the concrete document need id.
         requirements_inspect: doc__<something>_req_inspection
         sw_arch_verification: doc__<something>_arc_inspection
     feat__<module>:
       workproducts:
         requirements_inspect: doc__<feature>_req_inspection

.. _mvr_data_model:

Data model expectations
-----------------------

The extension looks up its subject through a chain of sphinx-needs
directives. Every id follows the ``<kind>__<slug>`` convention and every
link uses the field the sphinx-needs data model already defines.

.. list-table:: Needs the extension reads or filters by
   :header-rows: 1
   :widths: 15 20 65

   * - Directive
     - Where it lives
     - How the extension uses it

   * - ``.. mod::``
     - ``docs/module/index.rst`` (or wherever the module chooses)
     - Filesystem scan; ``:id:`` must equal ``module_id`` from the
       config. ``:includes:`` is a comma-separated list of the form
       ``comp__<slug>`` or ``comp__<slug>[version==<N>]`` — the
       whitelist of components rendered by the report.

   * - ``.. comp::``
     - Under any component's ``docs/`` folder
     - Filesystem scan; must appear in ``:includes:``. Its ``:id:``
       drives all component-scoped ``.. needtable::`` /
       ``.. needpie::`` filters (``"<comp_id>" in satisfied_by``, ``"<comp_id>" in belongs_to``).
       If ``[version==N]`` was requested in ``:includes:``, the
       ``.. comp::``'s ``:version:`` must match.

   * - ``.. feat::``
     - The module's feature documentation
     - Not scanned; resolved at render time by sphinx-needs. The
       "Feature" summary uses ``id == "<feature_id>"``; feature
       statistics filter ``feat_req`` / ``feat_arc_*`` by
       ``"<feature_id>" in belongs_to``.

   * - ``.. wp::``
     - Process repo (external)
     - Never scanned; the ``:need:\`wp__...\``` links assume the
       ``wp__*`` needs are registered on the external needs source.

   * - ``.. document::``
     - Anywhere; typically the ``verification_report/`` folders
     - Not scanned; resolved by sphinx-needs. Each "Realized by" cell
       is a ``.. needtable::`` filtered by
       ``type == "document" and "<slug_norm>" in id.replace("_", "")
       and "<wp_id>" in realizes``.

   * - ``.. comp_req::``, ``.. comp_arc_sta::``, ``.. comp_arc_dyn::``
     - Under the component
     - Not scanned; sphinx-needs handles the "Requirements Statistics"
       and "Architecture Statistics" pies and tables via filters on
       ``satisfied_by`` / ``belongs_to``.

   * - ``.. feat_req::``, ``.. feat_arc_sta::``, ``.. feat_arc_dyn::``
     - Under the feature
     - Same as above at the feature level.

.. _mvr_scan:

Filesystem scan (what the extension actually reads)
---------------------------------------------------

At ``env-before-read-docs`` the extension performs one recursive
``os.walk`` of ``env.srcdir`` and stores the result on
``env.module_verification_report_needs`` (see
:mod:`.scanner`). Only ``.rst`` files are considered; unreadable files
are silently skipped.

The scan captures every directive whose header matches
``^\.\. (mod|comp):: <title>`` and reads its ``:id:``,
``:includes:`` (mod only) and ``:version:`` (comp only) option lines.
**All other option lines are dropped** — safety, security, status,
tags, satisfies, etc. are resolved by sphinx-needs at render time from
the same source RST, so the scanner does not need to interpret them.

Rationale: querying ``SphinxNeedsData`` at directive-run time would
force ``parallel_read_safe = False`` and produce a "doing serial read"
warning that is fatal under ``-W``. A shallow regex scan is cheap,
reproducible in every worker of a parallel build, and only needs to
enumerate ids and titles.

.. _mvr_output:

What the report renders
-----------------------

Given a valid config the directive emits, in order:

1. **CSS block** — inline ``<style>`` scoped to the ``wp-doc-table``
   class, hiding the internal chrome (headers, datatables toolbar) of
   the nested ``.. needtable::`` widgets used in the WP tables.

2. **Feature** section — ``.. needtable::`` filtered by
   ``id == "<feature_id>"``; then Requirements Statistics
   (``needpie`` for status + verification coverage, plus a
   ``needtable`` in a dropdown), Architecture Statistics (status +
   inspection pie, plus a ``needtable``), and Inspection Statistics (a
   work-product presence table).

3. **Components** section — an ``H2`` heading followed by:

   a. **Component Overview** — ``.. needtable::`` filtered by
      ``id in [ ... ]`` over the whitelisted component ids, showing
      safety / security / status columns.

   b. One **per-component section** with, in order:

      * Requirements Statistics (pies + traceability table);
      * Architecture Statistics (pies + inspection table);
      * a **Verification & Safety Analysis Documents** work-product
        table.

The Unit Test Coverage section (`_COMPONENT_COVERAGE_SECTION_DISABLED`
in :mod:`.templates`) is currently disabled at the template level.
Re-enable by appending the fragment to ``COMPONENT_TEMPLATE`` and
passing ``coverage_intro=coverage_intro(comp, coverage_data)`` from
:func:`.rendering.render_component`.

.. _mvr_wp_rows:

Work-product row rendering
--------------------------

Each row of a "Verification & Safety Analysis Documents" (or feature
"Inspection Statistics") table has four columns: **Work Product**,
**Kind**, **Realized by**, **Status**. The first two are plain text
(``:need:`` link and the WP label from the config). The last two are
resolved either by an explicit override or by sphinx-needs:

* **Override** — when the config sets
  ``overrides[<need_id>].workproducts[<wp_key>] = <doc_id>``, the
  row renders

  .. code-block:: rst

     - :need:`<doc_id>`
     - :ndf:`copy('status', need_id='<doc_id>')`

* **Filter** (default) — both cells emit an identical inner
  ``.. needtable::`` with the filter

  .. code-block:: text

     type == "document"
       and "<slug_norm>" in id.replace("_", "")
       and "<wp_id>" in realizes

  where ``<slug_norm>`` is the component (or feature) slug with all
  underscores removed and lower-cased (see
  :func:`.rendering.normalize_slug`). This makes ``bit_manipulation``
  and ``bitmanipulation`` compare equal without per-component config.

If neither an override nor a matching document is present, the cells
are empty.

.. _mvr_coverage:

Coverage summary (optional)
---------------------------

The extension reads ``<srcdir>/reporting/coverage_summary.json`` — the
output of ``tools/extract_coverage.py`` — via
:func:`.coverage.load_coverage_summary`. Its top-level keys are
component slugs; each value has at least the fields ``lines_pct``,
``functions_pct``, ``branches_pct``.

The JSON is only used by the currently disabled Unit Test Coverage
section (see above). When that section is re-enabled,
:func:`.coverage.coverage_intro` decides between the "measured" and
the "specification-only" intro paragraph based on whether the component
slug has at least one non-null ``*_pct`` field.

Missing / malformed JSON is not an error: the loader returns ``{}``.

.. _mvr_architecture:

Extension architecture
----------------------

Implementation is split across six modules under
``src/extensions/score_module_verification_report/`` so that each layer
can be tested independently:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Module
     - Responsibility

   * - :mod:`.scanner`
     - Filesystem regex scan for ``.. mod::`` / ``.. comp::``,
       ``:includes:`` parsing, component whitelisting.
       Registers ``scan_source_tree`` on ``env-before-read-docs``.

   * - :mod:`.coverage`
     - ``coverage_summary.json`` loading and intro-paragraph selection.

   * - :mod:`.templates`
     - All RST template strings, the scoped WP-table CSS, and the
       default (component / feature) workproduct lists.

   * - :mod:`.rendering`
     - Pure functions that expand the templates:
       ``render_component``, ``render_feature``, ``render_overview``,
       ``render_report``, and the shared ``workproduct_rows`` helper.

   * - :mod:`.directive`
     - The ``ModuleVerificationReportDirective`` class. Loads the
       YAML config, calls the scanner / renderer, and
       ``nested_parse_with_titles`` the resulting RST into the
       document. Registers its docname in
       ``env.module_verification_report_docnames`` so the annotation
       hook knows which pages to touch.

   * - :mod:`.testcase_annotations`
     - ``doctree-resolved`` handler that appends a coloured
       ``(passed)`` / ``(failed)`` / ``(skipped)`` / ``(disabled)``
       badge to every ``testcase__…`` back-link on pages that rendered
       the directive. Sources the status from each testcase need's
       ``result`` field via ``sphinx_needs.data.SphinxNeedsData``. The
       hook is a no-op on pages the directive did not touch, when
       sphinx-needs is not initialised, or when a testcase need has an
       empty ``result``. Colour palette matches the pie-chart palette
       used by the report body.

   * - ``__init__.py``
     - Thin entry point exposing ``setup(app)``.

The public surface is intentionally minimal:

* the directive ``module-verification-report`` (added in ``setup``);
* the event handler
  ``scanner.scan_source_tree`` (connected to ``env-before-read-docs``
  in ``setup``);
* the cached attributes ``env.module_verification_report_needs`` and
  ``env.module_verification_report_docnames``.

All other functions are considered internal and covered by unit tests
under ``tests/``.

.. _mvr_limitations:

Known limitations
-----------------

* **Feature-only modules are not supported** — the extension hard-fails
  if it cannot find a ``.. mod::`` need with matching ``:id:`` and at
  least one resolvable component in its ``:includes:``. Repos like
  Lifecycle (feature-only, no ``comp``) currently need a small patch to
  the directive.
* **The scan is line-oriented** — a ``.. mod::`` / ``.. comp::``
  directive split across a line-continuation, or preceded by uncommon
  indentation, may be missed. All in-tree consumers use the canonical
  form documented above.
* **Nested tables render inside cells** — the ``.. needtable::`` widgets
  used in the WP rows are hidden by the scoped CSS block, but their
  DataTables initialisation still runs. Very large modules may see a
  measurable per-cell cost.

Testing
-------

Unit tests live under
``src/extensions/score_module_verification_report/tests/`` and are
grouped by module:

* ``test_scanner.py`` — every branch of ``scan_rst_needs``,
  ``module_includes``, ``discover_components``.
* ``test_coverage.py`` — JSON loading edge cases and the
  measured / spec-only intro decision.
* ``test_rendering.py`` — slug utilities, override vs. filter row
  rendering, and end-to-end ``render_report`` assembly.
* ``test_directive.py`` — option resolution logic: ``module-id`` /
  ``feature-id`` / ``component-prefix`` derivation and the precedence
  of directive options over config file values.
* ``test_testcase_annotations.py`` — the ``env-before-read-docs`` /
  ``env-purge-doc`` / ``env-merge-info`` lifecycle handlers plus every
  branch of ``annotate_testcase_results`` (colours, unknown result,
  every no-op guard).

Run them with the standard target::

   bazel test //src/extensions/score_module_verification_report:score_module_verification_report_tests
