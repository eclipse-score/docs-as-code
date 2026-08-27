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

.. _module-verification-report-example:

==========================================
Module Verification Report: Live Example
==========================================

This page renders a real report. Everything below the "Rendered report" heading
is produced by a single ``mod_ver_report`` directive — look at the sidebar and
the local contents to see that its sections are ordinary RST sections.

See :ref:`module-verification-report` for the reference documentation.

.. note::

   The architecture needs on this page exist only to give the example something
   to point at. They are not part of the Docs-as-Code architecture.

The module being reported on
============================

A module with two components:

.. feat:: Example Baselibs Feature
   :id: feat__example_baselibs
   :version: 1
   :security: NO
   :safety: QM
   :status: valid

   Container feature for the example components.

.. comp:: Example JSON Component
   :id: comp__example_baselibs_json
   :version: 1
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: feat__example_baselibs

   Parses and serialises JSON.

.. comp:: Example Bit Manipulation Component
   :id: comp__example_baselibs_bits
   :version: 1
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: feat__example_baselibs

   Bit-level helpers.

.. comp_arc_sta:: Example JSON Package Diagram
   :id: comp_arc_sta__example_feature__json
   :version: 1
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: comp__example_baselibs_json

   An architecture view of the JSON component. It shows up in the JSON
   component's table below because it links to that component.

.. comp_arc_sta:: Example Bit Manipulation Package Diagram
   :id: comp_arc_sta__example_feature__bits
   :version: 1
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: comp__example_baselibs_bits

   An architecture view of the bit manipulation component.

.. workproduct:: Example Baselibs Test Report
   :id: wp__example_baselibs_test_report
   :version: 1
   :status: valid

   Stands in for the artefact backing the verification report. The report links
   to it with ``evidence``, so it appears in the report's Verification Evidence
   section.

.. mod:: Example Baselibs Module
   :id: mod__example_baselibs
   :version: 1
   :security: NO
   :safety: QM
   :status: valid
   :includes: comp__example_baselibs_json, comp__example_baselibs_bits

   The module the report below is about.

What the author writes
======================

One Need. That is the whole input for the page you see below it:

.. code-block:: rst

   .. mod_ver_report:: Example Baselibs Verification Report
      :id: mod_vrep__example_feature__baselibs
      :version: 1
      :belongs_to: mod__example_baselibs
      :covers: comp__example_baselibs_json, comp__example_baselibs_bits
      :safety: QM
      :security: NO
      :status: valid
      :verification_method: test_and_inspection
      :evidence: wp__example_baselibs_test_report
      :titles:
         comp__example_baselibs_json = JSON Utilities
         comp__example_baselibs_bits = Bit Manipulation

      Verification report for the example Baselibs module.

``:covers:`` is a real link field, so ``mod__example_baselibs`` gets a
``covered by`` backlink and the metamodel checks that the list matches the
module's ``includes`` in both directions. ``:titles:`` is optional; without it
the headings are derived from the component ids.

Rendered report
===============

.. mod_ver_report:: Example Baselibs Verification Report
   :id: mod_vrep__example_feature__baselibs
   :version: 1
   :belongs_to: mod__example_baselibs
   :covers: comp__example_baselibs_json, comp__example_baselibs_bits
   :safety: QM
   :security: NO
   :status: valid
   :verification_method: test_and_inspection
   :evidence: wp__example_baselibs_test_report
   :titles:
      comp__example_baselibs_json = JSON Utilities
      comp__example_baselibs_bits = Bit Manipulation

   Verification report for the example Baselibs module.

The sections are real
=====================

Each generated section carries an anchor namespaced with the report id, so it
can be referenced from anywhere like any other section:

.. code-block:: rst

   See :ref:`mod_vrep__example_feature__baselibs__comp__example_baselibs_json`.

Which renders as: :ref:`mod_vrep__example_feature__baselibs__comp__example_baselibs_json`
— the link text comes from the section title, because the target *is* a
section. The same anchors appear in the sidebar, in the local contents, in the
search index and in the LaTeX/PDF bookmarks.
