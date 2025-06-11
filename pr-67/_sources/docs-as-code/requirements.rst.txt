.. _requirements:

=================================
Requirements (Process Compliance)
=================================

Overview
--------

.. needtable::
   :filter: c.this_doc()
   :columns: id;title;satisfies;implemented;
   :style: datatables


.. needpie:: Implemented Tool Requirements
  :labels: Yes, Partial, No

  implemented == 'YES'
  implemented == 'PARTIAL'
  implemented == 'NO'

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
   :id: tool_req__req_types
   :implemented: YES
   :satisfies: PROCESS_gd_req__req__structure
   :parent_has_problem: NO
   :parent_covered: YES

   dosc-as-code shall support following requirement types:

   * Stakeholder requirement (stkh_req)
   * Feature requirement (feat_req)
   * Component requirement (comp_req)
   * Assumption of use requirement (aou_req)
   * Process requirement (gd_req)
   * Tool requirement (tool_req)


.. tool_req:: Architecture Types
   :id: tool_req__req_types_temp
   :satisfies: PROCESS_gd_req__req__structure
   :implemented: YES
   :parent_has_problem: YES
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

----------------------
📛 ID Rules
----------------------

.. tool_req:: Enforces need ID uniqueness
   :id: tool_req__attr_id
   :implemented: YES
   :satisfies:
      PROCESS_gd_req__req__attr_uid,
      PROCESS_gd_req__tool__attr_uid,
   :parent_has_problem: NO
   :parent_covered: YES

   .. (gd_req__req__attr_uid only covered together with tool_req__attr_id_scheme)

   Need IDs must be globally unique.

   .. note::
      Implementation note (in some sort of DR in the future??).
      IDs are unique within one docs-instance, this is guaranteed by sphinx-needs.
      Several docs-instances are always independent. When they are linked, they always
      receive unique prefixes for their IDs.

.. tool_req:: Enforces need ID scheme
   :id: tool_req__attr_id_scheme
   :implemented: YES
   :satisfies: PROCESS_gd_req__req__attr_uid
   :parent_has_problem: YES

   .. problem: how can requirements have a component name?

   :parent_covered: YES

   .. (together with tool_req__attr_id)

   Need IDs must:

   * Start with the need type (e.g. ``feature__``)
   * Include the feature name (for feature requirements)
   * Have additional text

   This applies to all :need:`tool_req__req_types`

----------------------
🧾 Title Requirements
----------------------

.. tool_req:: Enforces title wording rules
   :id: tool_req__attr_title
   :implemented: PARTIAL
   :satisfies: PROCESS_gd_req__requirements_attr_title
   :parent_has_problem: NO
   :parent_covered: NO

   .. "The title of the requirement shall provide a short summary of the description" is not toolable

   Titles must not contain the words:
   * ``shall``
   * ``must``
   * ``will``

   This applies to all :need:`tool_req__req_types`


---------------------------
📝 Description Requirements
---------------------------

.. tool_req:: Enforces presence of description
   :id: tool_req__attr_description
   :implemented: NO
   :satisfies: PROCESS_gd_req__requirements_attr_description

   Each requirement must contain a non-empty description.

   This applies to all :need:`tool_req__req_types`


-------------------------
🧠 Rationale Requirements
-------------------------

.. tool_req:: Enforces rationale attribute
   :id: tool_req__attr_rationale
   :implemented: YES
   :satisfies: PROCESS_gd_req__req__attr_rationale

   Each stakeholder requirement must contain a non-empty ``rationale`` attribute.

--------------------------
🏷️ Requirement Type Rules
--------------------------

.. tool_req:: Enforces requirement type classification
   :id: tool_req__attr_type
   :implemented: YES
   :satisfies: PROCESS_gd_req__req__attr_type

   docs-as-code shall enforce that each requirement has an ``reqtype`` attribute, which
   must be one of:

   * Functional
   * Interface
   * Process
   * Legal
   * Non-Functional

   This applies to all :need:`tool_req__req_types`

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

   * YES
   * NO

   This applies to:
   * all :need:`tool_req__req_types` except process requirements.
   * all architecture elements (TODO; see https://github.com/eclipse-score/process_description/issues/34)


.. TODO: Double check if this truly isn't implements
.. tool_req:: Restrict linakge of security architecture elements
   :id: tool_req__arch_security_linkage
   :implemented: NO
   :satisfies: PROCESS_gd_req__arch__linkage_security_trace

   The tool shall enforce that requirements that are security relevant e.g. `security == YES` can only be
   linked to other requirements that are also security relevant.

   This shall be enforced for the following requirement types:

   * Architecture

---------------------------
🛡️ Safety Classification
---------------------------

.. tool_req:: Enforces safety classification (requirements, architecture)
   :id: tool_req__attr_safety
   :implemented: YES
   :satisfies:
      PROCESS_gd_req__req__attr_safety,

   docs-as-code shall ensure that every element of type :need:`tool_req__req_types` shall have a automotive safety integrity
   level (``safety``) attribute, which must be one of:

   * QM
   * ASIL_B
   * ASIL_D



----------------------------
📈 Status Classification
----------------------------

.. tool_req:: Enforces status classification (requirements, architecture)
   :id: tool_req__attr_status
   :implemented: YES
   :satisfies:
     PROCESS_gd_req__req__attr_status,
     PROCESS_gd_req__arch__attr_status,

   Needs of type:

   * stakeholder requirements
   * feature requirements
   * component requirements
   * assumption of use requirements
   * process requirements

   shall have an ``status`` attribute, which must be one of:

   * valid
   * invalid

   .. warning::
      the architecture requirement does not talk about architecture elements, but about requirements.


-------------------------
📄 Document Headers
-------------------------

.. tool_req:: Document author is mandatory and autofilled
   :id: tool_req__doc_attr_author
   :implemented: PARTIAL
   :satisfies: PROCESS_gd_req__doc_author
   :parent_covered: NO
   :parent_has_problem: NO

   The tool shall ensure that a document header has an 'author' attribute.
   It furthermore shall implement an automatic way to deter Minn the authors.
   Commiters with more than 50% of content addition, shall be considerd as author.

   .. note::
      Header service treats the 'author' is the person who makes the PR. Not someone who has at least 50% of the content added

.. tool_req:: Document approver is mandatory and filled
   :id: tool_req__doc_attr_approver
   :implemented: PARTIAL
   :satisfies: PROCESS_gd_req__doc_approver
   :parent_covered: NO
   :parent_has_problem: NO

   The tool shall ensure that the document header contains the 'approver' attribute.
   This attribute shall be filled automatically and shall be the *last CODEOWNER APPROVER*
   of the file that contains the document.



.. tool_req:: Document reviewer is mandatory and filled
   :id: tool_req__doc_attr_reviewer
   :implemented: PARTIAL
   :satisfies: PROCESS_gd_req__doc_reviewer
   :parent_covered: NO
   :parent_has_problem: NO

   The tool shall ensure that the document header contains the 'reviewer' attribute.
   This attribute shall contain all reviewers that are not mentioned under the 'approver'
   attribute.

   .. note::
      The header service grabs 'all' reviewers not just the last one. Therefore this is not 100% fulfilled as written.

-------------------------
📌 "requirement covered"
-------------------------

.. tool_req:: Enables marking requirements as "covered"
   :id: tool_req__covered
   :implemented: NO
   :satisfies: PROCESS_gd_req__req__attr_req_cov
    
   The tool shall check requirement parents hashes versus the ones referenced in the requirement it self.  
   It then shall fill out the 'requirement covered' attribute accordingly. 

   The hashes referenced in the requirement and the parents hashes are the same => 'covered'. 
   Otherwise => 'not covered'
    

.. tool_req:: Support requirements test coverage
   :id: tool_req__req_test_cov
   :implemented: NO
   :satisfies: PROCESS_gd_req__req__attr_test_covered

   | Requirements shall allow for an attribute that shows if the requirement is covered by linked test cases.
   | Allowed values:

   * Yes
   * No

-------------------------
🔗 "requirement linkage"
-------------------------

.. tool_req:: Enables linking from/to requirements
   :id: tool_req__linkage
   :implemented: PARTIAL
   :satisfies: PROCESS_gd_req__req__linkage
   :parent_covered: NO
   :parent_has_problem: NO

   The tool shall allow and check for linking of requirements to specific levels.
   In the table underneath you can see which requirement type can link to which other one

   .. table::
      :widths: auto

      ========================  ===========================
      Requirement Type          Allowed Link Target
      ========================  ===========================
      Stakeholder               Feature Requirements
      Feature Requirements      Component Requirements
      Workflows                 Process Requirements
      ========================  ===========================
   
   .. note::
      It seems that 'stakeholder' has no allowed link, targets. 


.. tool_req:: Checking architectual requirement linking
   :id: tool_req__arch_linkage
   :implemented: NO
   :satisfies: PROCESS_gd_req__arch__linkage_requirement_type

   The tool shall allow and check for linking of requirements to specific elements.
   In the table underneath you can see which requirement type can link to which other one

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
   :id: tool_req__req_saftety_link
   :implemented: PARTIAL
   :satisfies: PROCESS_gd_req__arch__linkage_requirement

   The tool shall enforce that requirements who have an ASIL_* **have** to be linked
   against another requirements that have ASIL_* safety.

   This shall be enforced for the following requirement types:

   * Architecture


.. tool_req:: Restrict links for safety requirements
   :id: tool_req__req_saftety_link_trace
   :implemented: PARTIAL
   :satisfies: PROCESS_gd_req__arch__linkage_safety_trace
   :parent_covered: NO
   :parent_has_problem: NO

   The tool shall ensure that requirements with safety != QM can only
   be linked against safety elements.

   This shall be enforced for the following requirement types:

   * Architecture
   
   .. note::
      Currently only enforced for 'feat_req' and 'comp_req' not the other architecture needs.





.. tool_req:: Ensure Architecture -> Requirements Link
   :id: tool_req__arch_attr_fulfils
   :implemented: PARTIAL
   :satisfies: PROCESS_gd_req__arch__attr_fulfils
   :parent_covered: NO
   :parent_has_problem: NO

   The tool shall enforce that each architecture element is linked to a requirement via
   the 'fulfils' attribute/option.

   .. note:: 
      Requriements: feat_arc_sta, comp_arc_sta, comp_arc_dyn do not have it enforced. 
      !TODO: Are these all 'architecture reqs'? Should we enforce this on all then?

.. tool_req:: Ensure Architecture fulfillment links
   :id: tool_req__arch_traceability
   :implemented: PARTIAL
   :satisfies: PROCESS_gd_req__arch__traceability
   :parent_covered: NO
   :parent_has_problem: NO

   The tool shall enforce that requirements are fulfilled by the architecture at the correct level.
   This means:

   * Feature requirements can only be fulfilled by: feat_arch_*
   * Component requirements can only be fulfilled by: comp_arch_*

   .. note::
      The link is implemented the other way. We only allow 'feat_arch' to fulfill a feat_req.
      Feat_req's do not get checked what 'fullfilled_back' requirement types they are linked to.
      !TODO: Check if this is alright!



------------------------
🚀 Release related things
------------------------

.. tool_req:: Store releases
   :id: tool_req__req_release_storage
   :implemented: NO
   :satisfies: PROCESS_gd_req__workproducts_storage

   The tool shall allow for a permanently saved release of the documentation as text documents including OSS tooling


.. I'm unsure if we need to track his here, as this is 'done' by Github?
.. tool_req:: Enable visulisation of differences between versions
   :id: tool_req__vis_ver_diff
   :implemented: YES
   :satisfies: PROCESS_gd_req__baseline_diff

   The tool shall allow for two versions to be compared with each other and visualize the differences between those versions.


----------------------
📊 Diagramm Related
----------------------

.. This seems covered so far, but there might be edgecases that I have not seen/realised that aren't.
.. tool_req:: Support Diagramm drawing of architecture
   :id: tool_req__arch_diag_draw
   :implemented: YES
   :satisfies: PROCESS_doc_concept__arch__process, PROCESS_gd_req__arch__viewpoints
   :parent_covered: YES
   :parent_has_problem: NO

   The tool shall enable the creation of a diagramm the following views:

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
   :id: tool_req__attr_impl
   :implemented: PARTIAL
   :satisfies: PROCESS_gd_req__req__attr_impl

   Source code can link to requirements.


.. tool_req:: Supports linking to test cases
   :id: tool_req__test_case_linkage
   :implemented: NO
   :satisfies: PROCESS_gd_req__req__attr_testlink

   Docs-as-code shall provide a way to automatically link test cases to requirements


------------------------------
🏗 Tool Verification Reports
------------------------------

.. they are so different, that they need their own section

.. tool_req:: Tool Verification Report
   :id: tool_req__docs_tvr_uid
   :implemented: NO
   :satisfies: PROCESS_gd_req__tool__attr_uid

   .. not sure about that satisfies link

   docs-as-code shall support the Tool Verification Report (tool_verification_report).

.. tool_req:: tool verification report: Enforce safety classification
   :id: tool_req__docs_tvr_safety
   :implemented: YES
   :satisfies: PROCESS_gd_req__tool__attr_safety_affected

   docs-as-code shall ensure that every Tool Verification Report has a ``safety_affected`` attribute, which must be one of:

   * YES
   * NO

.. tool_req:: tool verification report: enforce security classification
   :id: tool_req__docs_tvr_security
   :implemented: YES
   :satisfies: PROCESS_gd_req__tool_attr_security_affected

   docs-as-code shall ensure that every Tool Verification Report has a ``security_affected`` attribute, which must be one of:

   * YES
   * NO

.. tool_req:: tool verification report: enforce status classification (tool verification report)
   :id: tool_req__docs_tvr_status
   :implemented: YES
   :satisfies: PROCESS_gd_req__tool__attr_status
   :parent_has_problem: NO
   :parent_covered: YES

   docs-as-code shall ensure each Tool Verification Report has an ``status`` attribute, which must be one of:

   * draft
   * evaluated
   * qualified
   * released
   * rejected

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



.. needextend:: c.this_doc() and type == 'tool_req'
   :safety: QM
   :security: NO
   :reqtype: Functional


.. needextend:: c.this_doc() and type == 'tool_req' and not status
   :status: valid
