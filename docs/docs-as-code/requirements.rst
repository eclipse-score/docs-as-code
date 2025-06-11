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


.. needpie:: Implemented Tool Requirements 
   :labels: Yes, Partial, No
   :colors: green,orange,red

   implemented == 'YES'
   implemented == 'PARTIAL'
   implemented == 'NO'

.. needpie:: Process needs clarification
   :labels: Yes, No
   :colors: red, green

   "YES" in parent_has_problem  and 'tool_req__docs' in id 
   "YES" not in parent_has_problem and 'tool_req__docs' in id 

Details
----------------------

.. note::
   To stay consistent with sphinx-needs (the tool behind docs-as-code), we'll use `need`
   for any kind of model element like a requirement, an architecture element or a
   feature description.

----------------------
🏗 Types
----------------------

.. tool_req:: Requirements Types
   :id: tool_req__docs_req_types
   :implemented: YES
   :satisfies: PROCESS_gd_req__req__structure
   :parent_has_problem: YES: std_req not mentioned 
   :parent_covered: YES: Together with tool_req__docs_linkage

   dosc-as-code shall support following requirement types:

   * Stakeholder requirement (stkh_req)
   * Feature requirement (feat_req)
   * Component requirement (comp_req)
   * Assumption of use requirement (aou_req)
   * Process requirement (gd_req)
   * Tool requirement (tool_req)


.. tool_req:: Document Types
   :id: tool_req__docs_doc_types
   :implemented: YES

   Docs-As-Code shall support following document types:

   * Generic Document (document)


.. tool_req:: Workflow Types
   :id: tool_req__docs_wf_types
   :implemented: YES

   dosc-as-code shall support following workflow types:

   * Workflow (wf)

.. tool_req:: Standard Requirement Types
   :id: tool_req__docs_std_req_types
   :implemented: YES
   :parent_has_problem: YES: Requirement not found

   dosc-as-code shall support following requirement types:

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

   docs-as-code shall support following architecture types ??

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

   .. warning::
      This is a temporary requirement, used to gain some oversight.

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

   Docs-As-Code shall ensure that Need IDs are globally unique.

   .. note::
      Implementation note (in some sort of DR in the future??).
      IDs are unique within one docs-instance, this is guaranteed by sphinx-needs.
      Several docs-instances are always independent. When they are linked, they always
      receive unique prefixes for their IDs.

.. tool_req:: Enforces need ID scheme
   :id: tool_req__docs_attr_id_scheme
   :implemented: YES
   :satisfies: PROCESS_gd_req__req__attr_uid, PROCESS_gd_req__arch__attribute_uid
   :parent_has_problem: YES: Parents are not aligned
   :parent_covered: YES: together with tool_req__docs_attr_id

   Docs-As-Code shall ensure that Need IDs adhere to the following:

   * Start with the need type (e.g. ``feature__``)
   * Include the feature name (for feature requirements)
      * Requirement Attribute UID: some part of the feature tree / component acronym
      * Architecture Attribute UID: last part of the feature tree
   * Have additional text

   This applies to all :need:`tool_req__docs_req_types`

----------------------
🧾 Title Requirements
----------------------

.. tool_req:: Enforces title wording rules
   :id: tool_req__docs_attr_title
   :implemented: YES
   :satisfies: PROCESS_gd_req__requirements_attr_title
   :parent_has_problem: NO
   :parent_covered: NO: Can not ensure summary


   Docs-As-Code shall ensure that requirement titles must not contain the words:

   * shall
   * must
   * will

   This applies to all :need:`tool_req__docs_req_types`


---------------------------
📝 Description Requirements
---------------------------

.. tool_req:: Enforces presence of description
   :id: tool_req__docs_attr_description
   :implemented: NO
   :parent_covered: NO: Can not cover 'ISO/IEC/IEEE/29148'

   Each requirement must contain a description (content).

   This applies to all :need:`tool_req__docs_req_types`


-------------------------
🧠 Rationale Requirements
-------------------------

.. tool_req:: Enforces rationale attribute
   :id: tool_req__docs_attr_rationale
   :implemented: YES
   :parent_covered: NO: Can not ensure correct reasoning
   :satisfies: PROCESS_gd_req__req__attr_rationale

   Each stakeholder requirement must contain a non-empty ``rationale`` attribute.

--------------------------
🏷️ Requirement Type Rules
--------------------------

.. tool_req:: Enforces requirement type classification
   :id: tool_req__docs_attr_type
   :implemented: YES
   :parent_has_problem: YES: tool_req shall not have 'reqtype' as discussed
   :satisfies: PROCESS_gd_req__req__attr_type

   Docs-As-Code shall enforce that each requirement has an ``reqtype`` attribute, which
   must be one of:

   * Functional
   * Interface
   * Process
   * Legal
   * Non-Functional

   This applies to all :need:`tool_req__docs_req_types`

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

   The ``security`` attribute must be one of:

   * YES
   * NO

   This applies to:

   * all :need:`tool_req__docs_req_types` except process requirements.
   * all architecture elements (TODO; see https://github.com/eclipse-score/process_description/issues/34)


.. tool_req:: Restrict linakge of security architecture elements
   :id: tool_req__docs_arch_security_linkage
   :implemented: NO
   :parent_covered: YES
   :satisfies: PROCESS_gd_req__arch__linkage_security_trace

   Docs-As-Code shall enforce that needs that are security relevant meaning ``security == YES`` can only be
   linked to other needs that are also security relevant.

   This shall be enforced when: 

   * both linked needs are architecture elements (TODO; see https://github.com/eclipse-score/process_description/issues/34)

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

   Docs-As-Code shall ensure that every need of type :need:`tool_req__docs_req_types` (except Process Requirements) shall have a automotive safety integrity
   level (``safety``) attribute, which must be one of:

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

   Docs-As-Code shall ensure that every need of type :need:`tool_req__docs_req_types` has a ``status`` attribute, 
   which must be one of:

   * valid
   * invalid


-------------------------
📄 Document Headers
-------------------------

.. NOTE: Header_service trigger/working execution is disabled
.. tool_req:: Mandatory Document attributes
   :id: tool_req__docs_doc_attr
   :implemented: NO
   :satisfies: PROCESS_gd_req__doc_author, PROCESS_gd_req__doc_approver, PROCESS_gd_req__doc_reviewer
   :parent_covered: NO
   :parent_has_problem: YES: Which need type to use for this?

   Docs-As-Code shall enforce that a 'document' need has the following attributes:

   * author
   * approver 
   * reviewer


.. NOTE: Header_service trigger/working execution is disabled
.. tool_req:: Document author is autofilled
   :id: tool_req__docs_doc_autofill_author
   :implemented: NO
   :satisfies: PROCESS_gd_req__doc_author
   :parent_covered: YES: Together with tool_req__docs_doc_attr
   :parent_has_problem: YES: Unclear how the contribution % is counted and how to accumulate %. Committer is a reserved role.

   Docs-As-Code shall implement an automatic way to determin the authors.
   Authors with more than 50% of content addition, shall be considerd as author.


.. tool_req:: Document approver is autofilled
   :id: tool_req__docs_doc_attr_approver
   :implemented: NO
   :satisfies: PROCESS_gd_req__doc_approver
   :parent_covered: YES: Together with tool_req__docs_doc_attr
   :parent_has_problem: YES: CODEOWNER is Github specific.

   Docs-As-Code shall implement an automatic way to determin the appropriate approver.
   This attribute shall be the *last CODEOWNER APPROVER* of the file that contains the document.
   The last PR touching the relevant file is the basis for this.



.. tool_req:: Document reviewer is autofilled
   :id: tool_req__docs_doc_attr_reviewer
   :implemented: NO
   :satisfies: PROCESS_gd_req__doc_reviewer
   :parent_covered: YES: Together with tool_req__docs_doc_attr
   :parent_has_problem: NO


   Docs-As-Code shall implement an automatic way to determin the appropriate reviewers.
   This attribute shall contain all reviewers that are not mentioned under the 'approver' attribute.
   The last PR touching the relevant file is the basis for this.


-------------------------
📌 Requirement Covered
-------------------------

.. tool_req:: Enables marking requirements as "covered"
   :id: tool_req__docs_covered
   :implemented: NO
   :satisfies: PROCESS_gd_req__req__attr_req_cov
   :parent_has_problem: YES: Not understandable what is required.
    
    

.. tool_req:: Support requirements test coverage
   :id: tool_req__docs_req_test_cov
   :implemented: PARTIAL
   :parent_covered: YES
   :satisfies: PROCESS_gd_req__req__attr_test_covered

   Docs-As-Code shall allow for every need of type :need:`tool_req__docs_req_types` to have a ``testcovered`` attribute, 
   which must be one of:

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

   Docs-As-Code shall allow and check for linking of need to specific levels. This is done via the ``satisfies`` attribute.
   In the table underneath you can see which need type can link to which other one

   .. table::
      :widths: auto

      ========================  ===========================
      Requirement Type          Allowed Link Target
      ========================  ===========================
      Feature Requirements      Stakeholder
      Component Requirements    Feature Requirements
      Process Requirements      Workflows
      Tooling Requirements      Process Requirements
      ========================  ===========================
   

.. tool_req:: Mandatory Architecture Attribute: fulfils
   :id: tool_req__docs_arch_attr_fulfils
   :implemented: YES
   :satisfies: PROCESS_gd_req__arch__linkage_requirement_type, PROCESS_gd_req__arch__attr_fulfils, PROCESS_gd_req__arch__traceability
   :parent_covered: YES
   :parent_has_problem: YES: Attribute is not mentioned. Link direction not clear. Fig. 22 does not contain 'fulfils'

   Docs-As-Code shall enforce and check for linking of need to specific levels. This is done via the ``fulfils`` attribute.
   In the table underneath you can see which need type can link to which other one

   .. table::
      :widths: auto


      ====================================  ==========================================
      Requirement Type                      Allowed Link Target
      ====================================  ==========================================
      Functional feature requirements       Static / dynamic feature architecture
      Interface feature requirements        Interface feature architecture
      Functional component requirements     Static / dynamic component architecture
      Interface component requirements      Interface component architecture
      ====================================  ==========================================



.. I don't think this is enforced for JUST architecture, but for all.
.. tool_req:: Mandate links for safety requirements
   :id: tool_req__docs_req_saftety_link
   :implemented: PARTIAL
   :satisfies: PROCESS_gd_req__arch__linkage_requirement
   :parent_covered: YES
   :parent_has_problem: NO

   Docs-As-Code shall enforce that architecture needs of type :need:`tool_req__docs_arch_types` that are safety relevant meaning ``safety != QM`` shall be
   linked to needs of type :need:`tool_req__docs_req_types` that are also safety relevant.


.. tool_req:: Restrict links for safety requirements
   :id: tool_req__docs_req_saftety_link_trace
   :implemented: PARTIAL
   :satisfies: PROCESS_gd_req__arch__linkage_safety_trace
   :parent_covered: NO
   :parent_has_problem: NO

   Docs-As-Code shall enforce that architecture needs of type :need:`tool_req__docs_arch_types` that are safety relevant meaning ``safety != QM`` can only be
   linked to architecture needs of type :need:`tool_req__docs_arch_types` if they are also safety relevant.


----------------------
📊 Diagramm Related
----------------------

.. This seems covered so far, but there might be edgecases that I have not seen/realised that aren't.
.. tool_req:: Support Diagramm drawing of architecture
   :id: tool_req__docs_arch_diag_draw
   :implemented: YES
   :satisfies: PROCESS_doc_concept__arch__process, PROCESS_gd_req__arch__viewpoints
   :parent_covered: YES
   :parent_has_problem: NO

   Docs-As-Code shall enable the rendering of diagramms for the following views:

   * Feature View & Component View:
      *  Static View
      *  Dynamic View
      *  Interface View
   * SW Module View
   * Platform View


----------------
🧬 Code Linkage
----------------

.. tool_req:: Supports linking to source code
   :id: tool_req__docs_attr_impl
   :implemented: PARTIAL
   :parent_covered: YES
   :satisfies: PROCESS_gd_req__req__attr_impl

   Docs-As-Code shall allow for Source code to link requirements.
   A backlink pointing to the code in Github shall be generate in the output as an attribute of said requirement.


.. tool_req:: Supports linking to test cases
   :id: tool_req__docs_test_case_linkage
   :implemented: NO
   :parent_has_problem: YES: Test vs Testcase unclear.
   :satisfies: PROCESS_gd_req__req__attr_testlink

   Docs-as-code shall allow for a testlink attribute in needs of type :need:`tool_req__docs_req_types`
   It shall be possible to link testcases to needs via this attribute. 


------------------------------
🏗 Tool Verification Reports
------------------------------

.. they are so different, that they need their own section

.. tool_req:: Tool Verification Report
   :id: tool_req__docs_tvr_uid
   :implemented: NO
   :parent_covered: NO
   :satisfies: PROCESS_gd_req__tool__attr_uid

   Docs-As-Code shall support the Tool Verification Report (tool_verification_report).

.. tool_req:: tool verification report: Enforce safety classification
   :id: tool_req__docs_tvr_safety
   :implemented: NO
   :parent_has_problem: YES: Safety affected vs Safety relevance
   :parent_covered: YES
   :satisfies: PROCESS_gd_req__tool__attr_safety_affected

   Docs-As-Code shall ensure that every Tool Verification Report has a ``safety_affected`` attribute, which must be one of:

   * YES
   * NO

.. tool_req:: tool verification report: enforce security classification
   :id: tool_req__docs_tvr_security
   :implemented: NO
   :parent_covered: YES
   :parent_has_problem: YES: Safety affected vs Safety relevance
   :satisfies: PROCESS_gd_req__tool_attr_security_affected

   Docs-As-Code shall ensure that every Tool Verification Report has a ``security_affected`` attribute, which must be one of:

   * YES
   * NO

.. tool_req:: tool verification report: enforce status classification (tool verification report)
   :id: tool_req__docs_tvr_status
   :implemented: NO
   :satisfies: PROCESS_gd_req__tool__attr_status
   :parent_has_problem: NO
   :parent_covered: YES

   Docs-As-Code shall ensure each Tool Verification Report has a ``status`` attribute, which must be one of:

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

