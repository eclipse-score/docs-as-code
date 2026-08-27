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
"""RST templates for the module verification report."""

from __future__ import annotations

COMPONENT_TEMPLATE = """
.. _{ref}:

{title}
{title_underline}

.. raw:: html

   <hr style="border-top: 2px solid #333333; margin: 0.5em 0 1.5em 0;">

Component Requirements Statistics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. grid:: 1 2 2 2
   :gutter: 3

   .. grid-item::

      .. needpie:: {title} Requirements Status
         :labels: valid, invalid
         :colors: #37a12d, #ca2828
         :legend:

         type == "comp_req" and "{comp_id}" in satisfied_by and status == "valid"
         type == "comp_req" and "{comp_id}" in satisfied_by and status == "invalid"

   .. grid-item::

      .. needpie:: {title} Requirements Test Coverage
         :labels: fully covered, partially covered, not covered
         :colors: #37a12d, #f0a500, #ca2828
         :legend:

         type == "comp_req" and "{comp_id}" in satisfied_by and ("fully_verifies_back" in locals() and len(fully_verifies_back) > 0)
         type == "comp_req" and "{comp_id}" in satisfied_by and ("partially_verifies_back" in locals() and len(partially_verifies_back) > 0) and not ("fully_verifies_back" in locals() and len(fully_verifies_back) > 0)
         type == "comp_req" and "{comp_id}" in satisfied_by and not ("fully_verifies_back" in locals() and len(fully_verifies_back) > 0) and not ("partially_verifies_back" in locals() and len(partially_verifies_back) > 0)

Component Architecture Statistics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. grid:: 1 2 2 2
   :gutter: 3

   .. grid-item::

      .. needpie:: {title} Architecture Elements Status
         :labels: valid, invalid
         :colors: #37a12d, #ca2828
         :legend:

         type in ["comp_arc_sta", "comp_arc_dyn"] and "{comp_id}" in belongs_to and status == "valid"
         type in ["comp_arc_sta", "comp_arc_dyn"] and "{comp_id}" in belongs_to and status == "invalid"

   .. grid-item::

      .. needpie:: {title} Architecture Elements Inspection Status
         :labels: inspected, not inspected
         :colors: #37a12d, #ca2828
         :legend:

         type in ["comp_arc_sta", "comp_arc_dyn"] and "{comp_id}" in belongs_to and "inspected" in tags
         type in ["comp_arc_sta", "comp_arc_dyn"] and "{comp_id}" in belongs_to and "inspected" not in tags

Requirements Traceability
^^^^^^^^^^^^^^^^^^^^^^^^^

The following table lists all requirements of this component together with their
verification status and the tests that (fully or partially) verify them:

.. dropdown:: Show requirements table
   :animate: fade-in

   .. needtable::
      :filter: type == "comp_req" and "{comp_id}" in satisfied_by
      :style: table
      :columns: id;title;safety;status;fully_verifies_back;partially_verifies_back
      :colwidths: 13,22,8,10,23,24
      :sort: id
{coverage_block}
Architectural Elements
^^^^^^^^^^^^^^^^^^^^^^

The following table lists the architectural elements of this component
together with their inspection status. Elements that have been formally
inspected carry the ``inspected`` tag; elements without that tag have not
yet been inspected.

.. dropdown:: Show architectural elements table
   :animate: fade-in

   .. needtable::
      :filter: type in ["comp_arc_sta", "comp_arc_dyn"] and "{comp_id}" in belongs_to
      :style: table
      :columns: id;title;safety;status;tags
      :colwidths: 25,30,10,15,20
      :sort: id

Verification & Safety Analysis Documents
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Presence of the standard verification and safety analysis work products for
this component. A dash (``\u2014``) means the corresponding document is missing.

.. dropdown:: Show work products table
   :animate: fade-in

   .. list-table::
      :header-rows: 1
      :widths: 30 25 25 20
      :class: wp-doc-table

      * - Work Product
        - Kind
        - Realized by
        - Status
{workproduct_rows}
"""


COMPONENT_COVERAGE_TEMPLATE = """
Test Coverage
^^^^^^^^^^^^^

Per-source-file line and branch coverage aggregated from the LCOV report
produced by ``bazel coverage``.

.. dropdown:: Show test coverage table
   :animate: fade-in
{coverage_body}
"""


COVERAGE_TABLE_HEADER = """
   .. list-table::
      :header-rows: 1
      :widths: 45 10 10 10 10 10 10

      * - Source
        - Lines found
        - Lines hit
        - Line %
        - Branches found
        - Branches hit
        - Branch %
"""


COVERAGE_EMPTY_BODY = """
   .. note::

      No coverage data available for this component. Run ``bazel coverage``
      with the corresponding targets and rebuild the docs to populate this
      table.
"""


# Emits an actual sphinx-needs ``mod_ver_report`` need (see metamodel.yaml)
# so the module verification report is machine-readable, not just a rendered
# RST page. Only the four type-specific *mandatory* options + the globally
# mandatory ``version`` + the mandatory ``belongs_to`` link are set here —
# score_metamodel's generic need-link/option validation (the same mechanism
# used for every other need type) takes over from there.
MOD_VER_REPORT_TEMPLATE = """\
.. mod_ver_report:: {title}
   :id: {report_id}
   :version: {version}
   :safety: {safety}
   :security: {security}
   :status: {status}
   :verification_method: {verification_method}
   :belongs_to: {module_id}
   :components: {components}
   :features: {features}

"""


FEATURE_TEMPLATE = """\
{feature_heading}
{feature_heading_underline}

.. needtable::
   :filter: id == "{feature_id}"
   :columns: title as "Name";id as "Id";safety;security;status
   :style: table

Feature Requirements Statistics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. grid:: 1 2 2 2
   :gutter: 3

   .. grid-item::

      .. needpie:: Feature Requirements Status
         :labels: valid, invalid
         :colors: #37a12d, #ca2828
         :legend:

         type == "feat_req" and "{feature_id}" in satisfied_by and status == "valid"
         type == "feat_req" and "{feature_id}" in satisfied_by and status == "invalid"

   .. grid-item::

      .. needpie:: Feature Requirements Test Coverage
         :labels: fully covered, partially covered, not covered
         :colors: #37a12d, #f0a500, #ca2828
         :legend:

         type == "feat_req" and "{feature_id}" in satisfied_by and ("fully_verifies_back" in locals() and len(fully_verifies_back) > 0)
         type == "feat_req" and "{feature_id}" in satisfied_by and ("partially_verifies_back" in locals() and len(partially_verifies_back) > 0) and not ("fully_verifies_back" in locals() and len(fully_verifies_back) > 0)
         type == "feat_req" and "{feature_id}" in satisfied_by and not ("fully_verifies_back" in locals() and len(fully_verifies_back) > 0) and not ("partially_verifies_back" in locals() and len(partially_verifies_back) > 0)

.. dropdown:: Show requirements table
   :animate: fade-in

   .. needtable::
      :filter: type == "feat_req" and "{feature_id}" in satisfied_by
      :style: table
      :columns: id;title;safety;status;fully_verifies_back;partially_verifies_back
      :colwidths: 13,22,8,10,23,24
      :sort: id

Feature Architecture Statistics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. grid:: 1 2 2 2
   :gutter: 3

   .. grid-item::

      .. needpie:: Feature Architecture Elements Status
         :labels: valid, invalid
         :colors: #37a12d, #ca2828
         :legend:

         type in ["feat_arc_sta", "feat_arc_dyn"] and "{feature_id}" in belongs_to and status == "valid"
         type in ["feat_arc_sta", "feat_arc_dyn"] and "{feature_id}" in belongs_to and status == "invalid"

   .. grid-item::

      .. needpie:: Feature Architecture Elements Inspection Status
         :labels: inspected, not inspected
         :colors: #37a12d, #ca2828
         :legend:

         type in ["feat_arc_sta", "feat_arc_dyn"] and "{feature_id}" in belongs_to and "inspected" in tags
         type in ["feat_arc_sta", "feat_arc_dyn"] and "{feature_id}" in belongs_to and "inspected" not in tags

.. dropdown:: Show architectural elements table
   :animate: fade-in

   .. needtable::
      :filter: type in ["feat_arc_sta", "feat_arc_dyn"] and "{feature_id}" in belongs_to
      :style: table
      :columns: id;title;safety;status;tags
      :colwidths: 25,30,10,15,20
      :sort: id

Feature Inspection Statistics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Presence of the feature-level inspection work products.

.. dropdown:: Show work products table
   :animate: fade-in

   .. list-table::
      :header-rows: 1
      :widths: 30 25 25 20
      :class: wp-doc-table

      * - Work Product
        - Kind
        - Realized by
        - Status
{feature_workproduct_rows}
"""


COMPONENTS_HEADER = """\
Components
----------

"""


# Hide the auto-generated header / chrome of the inner ``.. needtable::``
# widgets that render the "Realized by" / "Status" cells of the WP tables.
# Without this the cells show a nested table with its own "ID" / "Status"
# header row and datatables toolbar, which is visually noisy for a single
# value. Scoped to ``.wp-doc-table`` set as the outer list-table's class.
WP_TABLE_CSS = """\
.. raw:: html

   <style>
   .wp-doc-table td .needstable_wrapper,
   .wp-doc-table td .pst-scrollable-table-container {
       margin: 0; padding: 0; overflow: visible;
   }
   .wp-doc-table td table.NEEDS_TABLE,
   .wp-doc-table td table.NEEDS_DATATABLES {
       border: 0; margin: 0; box-shadow: none; background: transparent;
       width: auto;
   }
   .wp-doc-table td table.NEEDS_TABLE thead,
   .wp-doc-table td table.NEEDS_DATATABLES thead { display: none; }
   .wp-doc-table td table.NEEDS_TABLE tbody tr,
   .wp-doc-table td table.NEEDS_DATATABLES tbody tr { background: transparent; }
   .wp-doc-table td table.NEEDS_TABLE tbody td,
   .wp-doc-table td table.NEEDS_DATATABLES tbody td {
       border: 0; padding: 0; background: transparent;
   }
   .wp-doc-table td .dataTables_wrapper .dataTables_length,
   .wp-doc-table td .dataTables_wrapper .dataTables_filter,
   .wp-doc-table td .dataTables_wrapper .dataTables_info,
   .wp-doc-table td .dataTables_wrapper .dataTables_paginate { display: none; }
   </style>
"""


OVERVIEW_TEMPLATE = """\
Component Overview
~~~~~~~~~~~~~~~~~~

.. needtable::
   :filter: id in {ids_literal}
   :columns: id as "Component";safety;security;status
   :style: table
   :sort: id
"""


DEFAULT_WORKPRODUCTS = [
    {
        "key": "requirements_inspect",
        "label": "Requirements Inspection",
        "wp_id": "wp__requirements_inspect",
    },
    {
        "key": "sw_arch_verification",
        "label": "Architecture Inspection",
        "wp_id": "wp__sw_arch_verification",
    },
    {
        "key": "sw_implementation_inspection",
        "label": "Implementation Inspection",
        "wp_id": "wp__sw_implementation_inspection",
    },
    {"key": "sw_component_dfa", "label": "DFA", "wp_id": "wp__sw_component_dfa"},
    {"key": "sw_component_fmea", "label": "FMEA", "wp_id": "wp__sw_component_fmea"},
]


DEFAULT_FEATURE_WORKPRODUCTS = [
    {
        "key": "requirements_inspect",
        "label": "Requirements Inspection",
        "wp_id": "wp__requirements_inspect",
    },
    {
        "key": "sw_arch_verification",
        "label": "Architecture Inspection",
        "wp_id": "wp__sw_arch_verification",
    },
]
