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

   The needs on this page exist only to give the example something to point at.
   They are not part of the Docs-as-Code architecture.

The world being reported on
===========================

A feature with a requirement and an architecture element, a module with two
components, a component requirement covered by a test, and an inspection
document realising a work product:

.. feat:: Example Baselibs Feature
   :id: feat__example_baselibs
   :version: 1
   :security: NO
   :safety: QM
   :status: valid

   Container feature for the example components.

.. feat_req:: Example Baselibs Feature Requirement
   :id: feat_req__example_feature__baselibs
   :version: 1
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :valid_from: v1.0
   :satisfied_by: feat__example_baselibs

   The feature shall provide basic library utilities.

.. feat_arc_sta:: Example Baselibs Feature Package Diagram
   :id: feat_arc_sta__example_feature__baselibs
   :version: 1
   :security: NO
   :safety: QM
   :status: valid
   :tags: inspected
   :includes: logic_arc_int__example_feature__baselibs
   :belongs_to: feat__example_baselibs

   Feature-level architecture view. Carries the ``inspected`` tag, so it shows
   up as inspected in the feature architecture statistics.

.. logic_arc_int:: Example Baselibs Logical Interface
   :id: logic_arc_int__example_feature__baselibs
   :version: 1
   :security: NO
   :safety: QM
   :status: valid

   Referenced by the feature package diagram above.

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

.. comp_req:: Example JSON Round-Trip Requirement
   :id: comp_req__example_feature__json_roundtrip
   :version: 1
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :satisfied_by: comp__example_baselibs_json

   The component shall serialise and parse a document without loss.

.. comp_arc_sta:: Example JSON Package Diagram
   :id: comp_arc_sta__example_feature__json
   :version: 1
   :security: NO
   :safety: QM
   :status: valid
   :tags: inspected
   :belongs_to: comp__example_baselibs_json

   Architecture view of the JSON component.

.. comp_arc_sta:: Example Bit Manipulation Package Diagram
   :id: comp_arc_sta__example_feature__bits
   :version: 1
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: comp__example_baselibs_bits

   Architecture view of the bit manipulation component. Deliberately *not*
   tagged ``inspected``, so the inspection pie chart is not all green.

.. mod:: Example Baselibs Module
   :id: mod__example_baselibs
   :version: 1
   :security: NO
   :safety: QM
   :status: valid
   :includes: comp__example_baselibs_json, comp__example_baselibs_bits

   The module the report below is about.

.. document:: Example JSON Requirements Inspection
   :id: doc__example_json_req_inspect
   :version: 1
   :security: NO
   :safety: QM
   :status: valid
   :realizes: wp__requirements_inspect

   The document realising the ``wp__requirements_inspect`` work product from
   the process description. It is matched into the JSON component's work
   product table because its id contains the component slug.

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
      :titles:
         comp__example_baselibs_json = JSON Utilities
         comp__example_baselibs_bits = Bit Manipulation

      Verification report for the example Baselibs module.

``:covers:`` is a real link field, so ``mod__example_baselibs`` gets a
``covered by`` backlink and the metamodel checks that the list matches the
module's ``includes`` in both directions.

``:titles:`` is the one presentation-only option: it names each component
section. Without it the headings are derived from the component ids
(``comp__example_baselibs_json`` → "Example Baselibs Json"). The feature the
statistics are about is derived the same way the upstream template derives it,
by rewriting ``mod__example_baselibs`` to ``feat__example_baselibs``.

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

Which renders as:
:ref:`mod_vrep__example_feature__baselibs__comp__example_baselibs_json`
— the link text comes from the section title, because the target *is* a
section. The same anchors appear in the sidebar, in the local contents, in the
search index and in the LaTeX/PDF bookmarks.

The rubrics *inside* a component section (Requirements Statistics, Test
Coverage, …) are deliberately not sections: no navigation is needed below the
component level, and a flat list keeps the sidebar readable.
