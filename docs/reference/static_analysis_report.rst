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
.. _docs_static_analysis_report:

Static analysis report
======================

The CLI used by ``bazel run :docs`` and ``:live_preview`` summarizes SARIF files
before Sphinx starts and writes ``<build-output>/static_analysis_summary.json``.
The ``score-static-analysis-report`` directive in the module verification report
renders this summary per component.

Input
-----

The CLI reads ``static-analysis-report/`` relative to the workspace root:

- ``*.sarif`` directly in the directory describe the workspace itself.
- Every file in a subdirectory named after a repository, e.g.
  ``static-analysis-report/score_baselibs+/``, describes that repository analysed
  as its own Bazel workspace. Its paths are relative to that repository, and
  findings outside it are ignored. Tools need not merge their output, e.g. the
  per-target reports of rules_lint can be copied as they are.

Empty and non-SARIF files are skipped. Results of kind ``pass`` or
``notApplicable`` are not findings.

Processing
----------

#. **Path cleanup.** ``uriBaseId`` chains are resolved. Bazel prefixes
   (``.../execroot/<workspace>/``, ``./``, ``bazel-out/<config>/bin/``) are
   removed, and a ``_virtual_includes`` copy of a header is mapped back to its
   source file.
#. **De-duplication.** A finding is identified by tool, rule, file, line, column
   and message. Linters running per target report a shared header once per
   including target; it is counted once and stays open if any copy is open.
#. **Rule identification.** See :ref:`static_analysis_rule_id`.
#. **Classification.** See :ref:`static_analysis_classification`.
#. **Assignment.** Findings are assigned to components through the same
   code-file lists as the coverage report. Findings in files no component owns
   are counted as unassigned. Findings with an accepted SARIF suppression are
   counted as suppressed and not classified.

.. _static_analysis_rule_id:

Rule identification
-------------------

#. The result's ``ruleId`` (or ``rule.id``), as written by CodeQL or clippy.
#. Otherwise, for tools whose rules_lint SARIF has no rule ID, the message text:

   - clang-tidy: the check name in brackets at the end, e.g.
     ``... [bugprone-use-after-move]`` gives ``bugprone-use-after-move``.
   - ruff: the code at the start, e.g. ``S603 ...`` gives ``S603``.

#. Otherwise ``unknown``.

.. _static_analysis_classification:

Classification
--------------

Every finding gets one of the classes required by
``gd_req__verification_sca_classification``: critical, high, medium or low.
The sources below are checked in order; the first one that applies decides.

.. list-table::
   :header-rows: 1
   :widths: 5 25 15 20 20 15

   * - #
     - Source
     - critical
     - high
     - medium
     - low
   * - 1
     - Rule property ``security-severity`` (e.g. CodeQL security queries)
     - 9.0 or more
     - 7.0 to 8.9
     - 4.0 to 6.9
     - below 4.0
   * - 2
     - Rule tag ``external/misra/obligation/<obligation>``
     -
     - mandatory
     - required
     - advisory
   * - 3a
     - clang-tidy check family
     -
     - ``bugprone``, ``cert``, ``clang-analyzer``, ``concurrency``
     - ``clang-diagnostic``, ``cppcoreguidelines``, ``hicpp``, ``misc``,
       ``performance``
     - ``google``, ``modernize``, ``portability``, ``readability``
   * - 3b
     - ruff code prefix
     -
     - ``S``, ``B``
     - ``F``, ``PL``, other prefixes
     - ``E``, ``W``, ``I``, ``N``, ``D``, ``UP``, ``SIM``, ``RUF``
   * - 4
     - SARIF ``level`` of the result, else of the rule
     -
     - ``error``
     - ``warning``, or no level
     - ``note``, ``none``

Only ``security-severity`` yields critical. A clang-tidy check of another family
(e.g. ``llvm-``) falls through to the level. The clang-tidy and ruff mappings are
preliminary: rules_lint reports every clang-tidy check as ``warning`` and every
ruff rule as ``error``, so their level says nothing.

MISRA obligation
~~~~~~~~~~~~~~~~

MISRA C++:2023 assigns every guideline an obligation: *mandatory* (no deviation
permitted), *required* (deviation only with a documented deviation record) or
*advisory* (recommended). The CodeQL coding standards packs write it as a rule
tag, for example:

.. code-block:: json

   {
     "id": "cpp/misra/a-mixed-use-macro-argument-subject-to-expansion",
     "properties": {
       "tags": [
         "external/misra/id/rule-19-3-3",
         "external/misra/obligation/required"
       ]
     },
     "defaultConfiguration": { "level": "error" }
   }

This rule is classified medium. Its level ``error`` would give high, but the
obligation is checked first.

Supported tools
~~~~~~~~~~~~~~~

Any tool writing SARIF is supported; without a more specific source its findings
are classified by level.

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - Tool
     - Rule ID
     - Classified by
   * - CodeQL with MISRA coding standards packs
     - ``ruleId``
     - MISRA obligation; ``security-severity`` for security queries
   * - clang-tidy (rules_lint, driver ``ClangTidy``)
     - message text
     - check family, else level
   * - ruff (rules_lint)
     - message text
     - code prefix
   * - clippy (rules_lint)
     - ``ruleId``
     - level (rules_lint reports ``warning``)
   * - other SARIF tools
     - ``ruleId``
     - ``security-severity``, else level

Stability
~~~~~~~~~

The class depends only on the rule: its metadata, the tool, the rule ID and the
SARIF level. The same rule gets the same class in every run, independent of
file, component, safety rating or number of findings. It changes only with

- a new version of the tool or rule pack that changes the rule's metadata,
- a new version of docs-as-code that changes the mappings above, or
- for tools classified by level, a tool configuration that changes the reported
  level (e.g. a clippy lint set to ``deny`` reports ``error``).

Output
------

``static_analysis_summary.json`` lists the tools with their number of findings,
the number of unassigned findings and, per component (primary Need), the
selected and affected files, the open findings per class, the suppressed
findings and the ten most critical rules.

In the module verification report, ``.. score-static-analysis-report:: <need id>``
shows the open findings per class as a bar chart; with ``:rules:`` it shows the
table of the most critical rules. Without any SARIF input it states that no
static analysis data is available.
