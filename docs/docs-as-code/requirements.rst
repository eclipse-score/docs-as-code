.. _requirements:

=================================
Requirements (Process Compliance)
=================================

Overview
--------

.. needtable::
   :filter: c.this_doc()
   :columns: id;title;implemented
   :style: datatables

Details
----------------------

.. note::
   To stay consistent with sphinx-needs (the tool behind docs-as-code), we'll use `need`
   for any kind of model element like a requirement, an architecture element or a
   feature description.

----------------------
📛 ID Rules
----------------------

.. tool_req:: Enforces need ID uniqueness
   :id: tool_req__attr_id
   :implemented: YES
   :satisfies:
      PROCESS_gd_req__req__attr_uid,
      PROCESS_gd_req__tool__attr_uid,

   Need IDs must be globally unique.

   .. note::
      Implementation note (in some sort of DR in the future??).
      IDs are unique within one docs-instance, this is guaranteed by sphinx-needs.
      Several docs-instances are always independent. When they are linked, they always
      receive unique prefixes for their IDs.

.. tool_req:: Enforces need ID scheme
   :id: tool_req__attr_id
   :implemented: YES
   :satisfies: PROCESS_gd_req__req__attr_uid

   Need IDs must:
   - Start with the need type (e.g. ``feature__``)
   - Include the feature name (for feature requirements)
   - Have additional text

   This applies to needs of type:
   - Stakeholder requirements
   - Feature requirements
   - Component requirements

----------------------
🧾 Title Requirements
----------------------

.. tool_req:: Enforces title wording rules
   :id: tool_req__attr_title
   :implemented: PARTIAL
   :satisfies: PROCESS_gd_req__requirements_attr_title


   Titles must not contain the words:
   - ``shall``
   - ``must``
   - ``will``

   Applies to:
   - stakeholder requirements
   - feature requirements
   - component requirements

   .. warning::
      Process requirement forbids only ``shall``.



--------------------------
📝 Description Requirements
--------------------------

.. tool_req:: Enforces presence of description
   :id: tool_req__attr_description
   :implemented: NO
   :satisfies: PROCESS_gd_req__requirements_attr_description

   Each requirement must contain a non-empty description.

   Applies to:
   * Stakeholder requirement
   * Feature requirement
   * Component requirement
   * Assumption of use requirement
   * Process requirement

   .. warning::
      All those "applies to" need to be matched exactly against available types,
      e.g. "process requirement" is quite vague.

------------------------
🧠 Rationale Requirements
------------------------

.. tool_req:: Enforces rationale attribute
   :id: tool_req__attr_rationale
   :implemented: YES
   :satisfies: PROCESS_gd_req__req__attr_rationale

   Each stakeholder requirement must contain a non-empty ``rationale`` attribute.

-------------------------
🏷️ Requirement Type Rules
-------------------------

.. tool_req:: Enforces requirement type classification
   :id: tool_req__attr_type
   :implemented: YES
   :satisfies: PROCESS_gd_req__req__attr_type

   The ``reqtype`` attribute must be one of:
   - Functional
   - Interface
   - Process
   - Legal
   - Non-Functional

   Applies to:
   * Stakeholder requirement
   * Feature requirement
   * Component requirement
   * Assumption of use requirement
   * Process requirement

----------------------------
🔐 Security Classification
----------------------------

.. tool_req:: Enforces security classification
   :id: tool_req__attr_security
   :implemented: YES
   :satisfies:
      PROCESS_gd_req__requirements_attr_security,
      PROCESS_gd_req__arch_attr_security,

   The ``security`` attribute must be one of:
   - YES
   - NO

   It is mandatory for:
   - stakeholder requirements
   - feature requirements
   - component requirements
   - assumption of use requirements
   - process requirements
   - Tool Verification Report

   .. warning::
      the architecture requirement does not talk about architecture elements, but about requirements.

---------------------------
🛡️ Safety Classification
---------------------------

.. tool_req:: Enforces safety classification
   :id: tool_req__attr_safety
   :implemented: YES
   :satisfies: PROCESS_gd_req__req__attr_safety

   Needs of type:
   - stakeholder requirements
   - feature requirements
   - component requirements
   - assumption of use requirements
   - process requirements
   - Tool Verification Report

   shall have a automotive safety integrity level (``safety``) identifier:
   - QM
   - ASIL_B
   - ASIL_D

   .. warning::
      the architecture requirement does not talk about architecture elements, but about requirements.

----------------------------
📈 Status Classification
----------------------------

.. tool_req:: Enforces status classification (1st part)
   :id: tool_req__attr_status
   :implemented: YES
   :satisfies:
     PROCESS_gd_req__req__attr_status,
     PROCESS_gd_req__arch__attr_status,

   Needs of type:
   - stakeholder requirements
   - feature requirements
   - component requirements
   - assumption of use requirements
   - process requirements
   - Tool Verification Report

   shall have an ``status`` attribute, which must be one of:
   - valid
   - invalid
   .. warning::
      the architecture requirement does not talk about architecture elements, but about requirements.

.. tool_req:: Enforces status classification (tool Verification Report)
   :id: tool_req__attr_status_tool_verification
   :implemented: YES
   :satisfies: PROCESS_gd_req__tool__attr_status

   The Tool Verification Report shall have an ``status`` attribute, which must be one of:
      * draft
      * evaluated
      * qualified
      * released
      * rejected

-------------------------
🔗 "requirement covered"
-------------------------

.. tool_req:: Enables marking requirements as "covered"
   :id: tool_req__linking
   :implemented: PARTIAL
   :satisfies: PROCESS_gd_req__req__linkage
   :status: invalid

   To be clarified.

----------------
📎 Code Linkage
----------------

.. tool_req:: Supports linking to source code
   :id: tool_req__attr_impl
   :implemented: PARTIAL
   :satisfies: PROCESS_gd_req__req__attr_impl

   Source code can link to requirements.

--------------------------
🏗 Requirement Level Types
--------------------------

.. tool_req:: Supports multiple requirement levels
   :id: tool_req__requirement_levels
   :implemented: YES
   :satisfies: PROCESS_gd_req__req__attr_uid

   The tool supports the following requirement levels:
   - Stakeholder requirements
   - Feature requirements
   - Component requirements
   - Assumption of use requirements
   - Process requirements


.. needextend:: c.this_doc() and type == 'tool_req'
   :safety: QM
   :security: NO
   :reqtype: Functional


.. needextend:: c.this_doc() and type == 'tool_req' and not status
   :status: valid


--------------------------
🏗 Metamodel
--------------------------

.. tool_req:: Supports requirement metamodel
   :id: tool_req__metamodel
   :implemented: YES
   :satisfies:
      PROCESS_gd_req__req__structure,
      PROCESS_gd_req__requirements_attr_description,
      PROCESS_gd_req__req__attr_type,
      PROCESS_gd_req__requirements_attr_security,
      PROCESS_gd_req__req__attr_safety,
      PROCESS_gd_req__req__attr_status,
      PROCESS_gd_req__req__attr_rationale,
      PROCESS_gd_req__req__linkage,
      PROCESS_gd_req__req__attr_mandatory,
      PROCESS_gd_req__req__linkage_fulfill,
      PROCESS_gd_req__req__linkage_architecture,
      PROCESS_gd_req__arch__build_blocks,
      PROCESS_gd_req__arch__build_blocks_corr,
      PROCESS_gd_req__arch_attr_security,
      PROCESS_gd_req__arch__attr_safety,
      PROCESS_gd_req__arch__attr_status,
      PROCESS_gd_req__arch__attr_fulfils,
      PROCESS_gd_req__arch__traceability,

   The docs-as-code metamodel shall enforce process requirements.

   .. note:: only process requirements which are fully covered by metamodel.yml are linked to this catch-all requirement!

.. tool_req:: Supports requirement metamodel (partially implemented)
   :id: tool_req__metamodel_partial
   :implemented: PARTIAL
   :satisfies:
      PROCESS_gd_req__requirements_attr_title,
      PROCESS_gd_req__req__attr_desc_weak,
      PROCESS_gd_req__req__attr_req_cov,
      PROCESS_gd_req__req__attr_test_covered,

   The docs-as-code metamodel shall enforce process requirements.

   .. note:: once implemented, move the satisfies-links to tool_req__metamodel. This list contains not fully implemented or non understood requirements.
