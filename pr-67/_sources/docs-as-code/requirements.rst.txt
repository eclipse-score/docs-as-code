.. _requirements:

=================================
Requirements (Process Compliance)
=================================

Overview
--------

This section provides an overview of current process requirements and their implementation status.

.. needtable::
  :filter: c.this_doc()
  :columns: id;title;implemented
  :style: datatables

.. needpie:: Docs-As-Code Requirements Status
  :labels: Implemented, Partial, Not Implemented
  :colors: green,orange,red

  implemented == 'YES'
  implemented == 'PARTIAL'
  implemented == 'NO'

.. needpie:: Process Requirements Needing Clarification
  :labels: Yes, No
  :colors: red, green

  'tool_req__docs' in id and "YES" in parent_has_problem
  'tool_req__docs' in id and "YES" not in parent_has_problem


.. note::
  To stay consistent with sphinx-needs (the tool behind docs-as-code), we'll use `need`
  for any kind of model element like a requirement, an architecture element or a
  feature description.

----------------------
🏗 Model Types
----------------------

The following types of requirements, documents, workflows, architecture elements etc are supported.

.. tool_req:: Requirements Types
  :id: tool_req__docs_req_types
  :implemented: YES
  :satisfies: PROCESS_gd_req__req__structure
  :parent_has_problem: YES: std_req not mentioned
  :parent_covered: YES: Together with tool_req__docs_linkage

  Docs-as-Code shall support the following requirement types:

  * Stakeholder requirement (stkh_req)
  * Feature requirement (feat_req)
  * Component requirement (comp_req)
  * Assumption of use requirement (aou_req)
  * Process requirement (gd_req)
  * Tool requirement (tool_req)

.. tool_req:: Document Types
  :id: tool_req__docs_doc_types
  :implemented: YES

  Docs-as-Code shall support the following document types:

  * Generic Document (document)

.. tool_req:: Workflow Types
  :id: tool_req__docs_wf_types
  :implemented: YES

  Docs-as-Code shall support the following workflow types:

  * Workflow (wf)

.. tool_req:: Standard Requirement Types
  :id: tool_req__docs_std_req_types
  :implemented: YES
  :parent_has_problem: YES: Requirement not found

  Docs-as-Code shall support the following requirement types:

  * Standard requirement (std_req)

.. tool_req:: Architecture Types
  :id: tool_req__docs_arch_types
  :satisfies:
     PROCESS_gd_req__arch__hierarchical_structure,
     PROCESS_gd_req__arch__viewpoints,
     PROCESS_gd_req__arch__build_blocks,
     PROCESS_gd_req__arch__build_blocks_corr
  :implemented: YES
  :parent_has_problem: YES: Referenced in https://github.com/eclipse-score/process_description/issues/34
  :parent_covered: NO
  :status: invalid

.. warning::
   **OPEN ISSUE** → Architecture types are not yet understood
   See: https://github.com/eclipse-score/process_description/issues/34

   The list below is tentative at best.

  Docs-as-Code shall support the following architecture types:

  * Feature Architecture Static View (feat_arch_static) - does this count as an architecture type, or is it a view?
  * Feature Architecture Dynamic View (feat_arch_dyn) - the views below have view in their type name!!
  * Logical Architecture Interfaces (logic_arc_int) - That's a single interface and not "interfaces"? Or is it a view?
  * Logical Architecture Interface Operation (logic_arc_int_op)
  * Module Architecture Static View (mod_view_static)
  * Module Architecture Dynamic View (mod_view_dyn)
  * Component Architecture Static View (comp_arc_sta)
  * Component Architecture Dynamic View (comp_arc_dyn)
  * Component Architecture Interfaces (comp_arc_int)
  * Component Architecture Interface Operation (comp_arc_int_op)
  * Real interface?? (see gd_req__arch__build_blocks_corr)
  * Feature Architecture Interface?? (see gd_req__arch__traceability)


----------------------
📛 ID Rules
----------------------

.. tool_req:: Enforces need ID uniqueness
  :id: tool_req__docs_attr_id
  :implemented: YES
  :satisfies:
     PROCESS_gd_req__req__attr_uid,
     PROCESS_gd_req__tool__attr_uid,
     PROCESS_gd_req__arch__attribute_uid
  :parent_has_problem: NO
  :parent_covered: YES: together with tool_req__docs_attr_id_scheme

  Docs-as-Code shall enforce that all Need IDs are globally unique across all included
  documentation instances.

  .. note::
     Within each docs-instance (as managed by sphinx-needs), IDs are guaranteed to be unique.
     When linking across instances, unique prefixes are automatically applied to maintain global uniqueness.

.. tool_req:: Enforces need ID scheme
  :id: tool_req__docs_attr_id_scheme
  :implemented: YES
  :satisfies: PROCESS_gd_req__req__attr_uid, PROCESS_gd_req__arch__attribute_uid
  :parent_has_problem: YES: Parents are not aligned
  :parent_covered: YES: together with tool_req__docs_attr_id

  Docs-as-Code shall enforce that Need IDs follow the following naming scheme:

  * A prefix indicating the need type (e.g. `feature__`)
  * A middle part indicating the hierarchical structure of the need:
     * For requirements: a portion of the feature tree or a component acronym
     * For architecture elements: the final part of the feature tree
  * Additional descriptive text to ensure human readability

  This scheme applies to all requirement types defined in :need:`tool_req__docs_req_types`.

----------------------
🧾 Title Requirements
----------------------

.. tool_req:: Enforces title wording rules
  :id: tool_req__docs_attr_title
  :implemented: YES
  :satisfies: PROCESS_gd_req__requirements_attr_title
  :parent_has_problem: NO
  :parent_covered: NO: Can not ensure summary

  Docs-as-Code shall enforce that requirement titles do not contain the following words:

  * shall
  * must
  * will

  This rule applies to all requirement types defined in :need:`tool_req__docs_req_types`.

---------------------------
📝 Description Requirements
---------------------------

.. tool_req:: Enforces presence of description
  :id: tool_req__docs_attr_description
  :implemented: NO
  :parent_covered: NO: Can not cover 'ISO/IEC/IEEE/29148'

  Docs-as-Code shall enforce that each requirement contains a description (content).

  This rule applies to all requirement types defined in :need:`tool_req__docs_req_types`.

-------------------------
🧠 Rationale Requirements
-------------------------

.. tool_req:: Enforces rationale attribute
  :id: tool_req__docs_attr_rationale
  :implemented: YES
  :parent_covered: NO: Can not ensure correct reasoning
  :satisfies: PROCESS_gd_req__req__attr_rationale

  Docs-as-Code shall enforce that each stakeholder requirement contains a ``rationale`` attribute.

--------------------------
🏷️ Requirement Type Rules
--------------------------

.. tool_req:: Enforces requirement type classification
  :id: tool_req__docs_attr_type
  :implemented: YES
  :parent_has_problem: YES: tool_req shall not have 'reqtype' as discussed
  :satisfies: PROCESS_gd_req__req__attr_type

  Docs-as-Code shall enforce that each requirement has a ``reqtype`` attribute with one
  of the following values:

  * Functional
  * Interface
  * Process
  * Legal
  * Non-Functional

  This rule applies to all requirement types defined in :need:`tool_req__docs_req_types`.

----------------------------
🔐 Security Classification
----------------------------

.. tool_req:: Enforces security classification
  :id: tool_req__docs_attr_security
  :implemented: YES
  :satisfies:
     PROCESS_gd_req__requirements_attr_security,
     PROCESS_gd_req__arch_attr_security,
  :parent_has_problem: YES: Architecture talks about requirements. Parents not aligned.

  Docs-as-Code shall enforce that the ``security`` attribute has one of the following values:

  * YES
  * NO

  This rule applies to:

  * all requirement types defined in :need:`tool_req__docs_req_types`, except process requirements.
  * all architecture elements (TODO; see https://github.com/eclipse-score/process_description/issues/34)

.. tool_req:: Restrict linakge of security architecture elements
  :id: tool_req__docs_arch_security_linkage
  :implemented: NO
  :parent_covered: YES
  :satisfies: PROCESS_gd_req__arch__linkage_security_trace

  Docs-as-Code shall enforce that architecture elements with ``security == YES`` are
  only linked to other architecture elements with ``security == YES``.

---------------------------
🛡️ Safety Classification
---------------------------

.. tool_req:: Enforces safety classification (requirements, architecture)
  :id: tool_req__docs_attr_safety
  :implemented: YES
  :parent_covered: YES
  :parent_has_problem: YES: Architecture talks about requirements. Parents not aligned
  :satisfies:
     PROCESS_gd_req__req__attr_safety,
     PROCESS_gd_req__arch__attr_safety

  Docs-as-Code shall enforce that every requirement of type
  :need:`tool_req__docs_req_types` (except process requirements) and all architecture
  elements have a ``safety`` attribute with one of the following values:

  * QM
  * ASIL_B
  * ASIL_D

----------------------------
📈 Status Classification
----------------------------

.. tool_req:: Enforces status classification (requirements, architecture)
  :id: tool_req__docs_attr_status
  :implemented: YES
  :parent_has_problem: YES: Architecture talks about requirements
  :parent_covered: YES
  :satisfies:
    PROCESS_gd_req__req__attr_status,
    PROCESS_gd_req__arch__attr_status,

  Docs-as-Code shall enforce that every requirement of type
  :need:`tool_req__docs_req_types` and all architecture elements have a ``status``
  attribute with one of the following values:

  * valid
  * invalid

-------------------------
📄 Document Headers
-------------------------

.. NOTE: Header_service trigger/working execution is disabled
.. tool_req:: Mandatory Document attributes
  :id: tool_req__docs_doc_attr
  :implemented: NO
  :satisfies:
   PROCESS_gd_req__doc_author,
   PROCESS_gd_req__doc_approver,
   PROCESS_gd_req__doc_reviewer,
  :parent_covered: NO
  :parent_has_problem: YES: Which need type to use for this?

  Docs-as-Code shall enforce that each document model element has the following attributes:

  * author
  * approver
  * reviewer
.. tool_req:: Document author is autofilled
  :id: tool_req__docs_doc_autofill_author
  :implemented: NO
  :satisfies: PROCESS_gd_req__doc_author
  :parent_covered: YES: Together with tool_req__docs_doc_attr
  :parent_has_problem: YES: Unclear how the contribution % is counted and how to accumulate %. Committer is a reserved role.

  Docs-as-Code shall provide an automatic mechanism to determine document authors.

  Contributors responsible for more than 50% of the content shall be considered the
  document author. Contributors are accumulated over all commits to the file containing
  the document.

.. tool_req:: Document approver is autofilled
  :id: tool_req__docs_doc_attr_approver
  :implemented: NO
  :satisfies: PROCESS_gd_req__doc_approver
  :parent_covered: YES: Together with tool_req__docs_doc_attr
  :parent_has_problem: YES: CODEOWNER is Github specific.

  Docs-as-Code shall provide an automatic mechanism to determine the document approver.

  The approver shall be the last approver listed in *CODEOWNERS* of the file containing
  the document. The determination is based on the last pull request (PR) that modified
  the relevant file.

.. tool_req:: Document reviewer is autofilled
  :id: tool_req__docs_doc_attr_reviewer
  :implemented: NO
  :satisfies: PROCESS_gd_req__doc_reviewer
  :parent_covered: YES: Together with tool_req__docs_doc_attr
  :parent_has_problem: NO

  Docs-as-Code shall provide an automatic mechanism to determine the document reviewers.

  The ``reviewer`` attribute shall include all reviewers who are not listed as
  approvers. The determination is based on the last pull request (PR) that modified the
  relevant file.

-------------------------
📌 Requirement Covered
-------------------------

.. tool_req:: Enables marking requirements as "covered"
  :id: tool_req__docs_covered
  :implemented: NO
  :satisfies: PROCESS_gd_req__req__attr_req_cov
  :parent_has_problem: YES: Not understandable what is required.

  .. warning::
     This requirement is not yet specified. The corresponding parent requirement is
     unclear and must be clarified before a precise tool requirement can be defined.

.. tool_req:: Support requirements test coverage
  :id: tool_req__docs_req_test_cov
  :implemented: PARTIAL
  :parent_covered: YES
  :satisfies: PROCESS_gd_req__req__attr_test_covered

  Docs-As-Code shall allow for every need of type :need:`tool_req__docs_req_types` to
  have a ``testcovered`` attribute, which must be one of:

  * Yes
  * No

-------------------------
🔗 Requirement Linkage
-------------------------

.. tool_req:: Enables needs linking via satisfies attribute
  :id: tool_req__docs_satisfies
  :implemented: PARTIAL
  :satisfies: PROCESS_gd_req__req__linkage
  :parent_covered: YES
  :parent_has_problem: YES: Mandatory for all needs? Especially some tool_reqs do not have a process requirement.

  Docs-as-Code shall enforce that linking between model elements via the ``satisfies``
  attribute follows defined rules.

  Allowed source and target combinations are defined in the following table:

  .. table::
     :widths: auto

     ========================  ===========================
     Requirement Type           Allowed Link Target
     ========================  ===========================
     Feature Requirements       Stakeholder Requirements
     Component Requirements     Feature Requirements
     Process Requirements       Workflows
     Tooling Requirements       Process Requirements
     ========================  ===========================

.. tool_req:: Mandatory Architecture Attribute: fulfils
  :id: tool_req__docs_arch_attr_fulfils
  :implemented: YES
  :satisfies:
   PROCESS_gd_req__arch__linkage_requirement_type,
   PROCESS_gd_req__arch__attr_fulfils,
   PROCESS_gd_req__arch__traceability,
  :parent_covered: YES
  :parent_has_problem: YES: Attribute is not mentioned. Link direction not clear. Fig. 22 does not contain 'fulfils'

  Docs-as-Code shall enforce that linking via the ``fulfils`` attribute follows defined rules.

  Allowed source and target combinations are defined in the following table:

  .. table::
     :widths: auto

     ====================================  ==========================================
     Requirement Type                       Allowed Link Target
     ====================================  ==========================================
     Functional feature requirements        Static / dynamic feature architecture
     Interface feature requirements         Interface feature architecture
     Functional component requirements      Static / dynamic component architecture
     Interface component requirements       Interface component architecture
     ====================================  ==========================================

.. tool_req:: Mandate links for safety requirements
  :id: tool_req__docs_req_saftety_link
  :implemented: PARTIAL
  :satisfies: PROCESS_gd_req__arch__linkage_requirement
  :parent_covered: YES
  :parent_has_problem: NO

  Docs-as-Code shall enforce that architecture model elements of type
  :need:`tool_req__docs_arch_types` with ``safety != QM`` are linked to requirements of
  type :need:`tool_req__docs_req_types` that are also safety relevant (``safety !=
  QM``).

.. tool_req:: Restrict links for safety requirements
  :id: tool_req__docs_req_saftety_link_trace
  :implemented: PARTIAL
  :satisfies: PROCESS_gd_req__arch__linkage_safety_trace
  :parent_covered: NO
  :parent_has_problem: NO

  Docs-as-Code shall enforce that architecture model elements of type
  :need:`tool_req__docs_arch_types` with ``safety != QM`` can only be linked to other
  architecture model elements with ``safety != QM``.

----------------------
📊 Diagramm Related
----------------------

.. tool_req:: Support Diagramm drawing of architecture
  :id: tool_req__docs_arch_diag_draw
  :implemented: YES
  :satisfies: PROCESS_doc_concept__arch__process, PROCESS_gd_req__arch__viewpoints
  :parent_covered: YES
  :parent_has_problem: NO

  Docs-as-Code shall enable the rendering of diagrams for the following architecture views:

  * Feature View & Component View:
     * Static View
     * Dynamic View
     * Interface View
  * Software Module View
  * Platform View

----------------
🧬 Code Linkage
----------------

.. tool_req:: Supports linking to source code
  :id: tool_req__docs_attr_impl
  :implemented: PARTIAL
  :parent_covered: YES
  :satisfies: PROCESS_gd_req__req__attr_impl

  Docs-as-Code shall allow source code to link to requirements.

  A backlink to the corresponding source code location in GitHub shall be generated in
  the output as an attribute of the linked requirement.

.. tool_req:: Supports linking to test cases
  :id: tool_req__docs_test_case_linkage
  :implemented: NO
  :parent_has_problem: YES: Test vs Testcase unclear. Direction unclear. Goal unclear.
  :satisfies: PROCESS_gd_req__req__attr_testlink

  Docs-as-Code shall allow requirements of type :need:`tool_req__docs_req_types` to
  include a ``testlink`` attribute.

  This attribute shall support linking test cases to requirements.

------------------------------
🏗 Tool Verification Reports
------------------------------

.. they are so different, that they need their own section

.. tool_req:: Tool Verification Report
  :id: tool_req__docs_tvr_uid
  :implemented: NO
  :parent_covered: NO
  :satisfies: PROCESS_gd_req__tool__attr_uid

  Docs-as-Code shall support the definition and management of Tool Verification Reports
  (``tool_verification_report``).

.. tool_req:: tool verification report: Enforce safety classification
  :id: tool_req__docs_tvr_safety
  :implemented: NO
  :parent_has_problem: YES: Safety affected vs Safety relevance
  :parent_covered: YES
  :satisfies: PROCESS_gd_req__tool__attr_safety_affected

  Docs-as-Code shall enforce that every Tool Verification Report includes a
  ``safety_affected`` attribute with one of the following values:

  * YES
  * NO

.. tool_req:: tool verification report: enforce security classification
  :id: tool_req__docs_tvr_security
  :implemented: NO
  :parent_covered: YES
  :parent_has_problem: YES: Safety affected vs Safety relevance
  :satisfies: PROCESS_gd_req__tool_attr_security_affected

  Docs-as-Code shall enforce that every Tool Verification Report includes a
  ``security_affected`` attribute with one of the following values:

  * YES
  * NO

.. tool_req:: tool verification report: enforce status classification (tool verification report)
  :id: tool_req__docs_tvr_status
  :implemented: NO
  :satisfies: PROCESS_gd_req__tool__attr_status
  :parent_has_problem: NO
  :parent_covered: YES

  Docs-as-Code shall enforce that every Tool Verification Report includes a ``status``
  attribute with one of the following values:

  * draft
  * evaluated
  * qualified
  * released
  * rejected

.. needextend:: c.this_doc() and type == 'tool_req'
  :safety: ASIL_B
  :security: NO

.. needextend:: c.this_doc() and type == 'tool_req' and "YES" in parent_has_problem
  :status: invalid

.. needextend:: c.this_doc() and type == 'tool_req' and not status
  :status: valid
