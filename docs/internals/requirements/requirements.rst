.. _tool_requirements:

=================================
Tool Requirements
=================================


📈 Status
##########

This section provides an overview of current process requirements and their clarification & implementation status.

.. note::
  All open issues and pull requests in the process repository are considered as if they
  are already part of the process requirements. They address a lot of the
  requirements that are referenced in this document, so we would be blocked if we would
  not consider them as part of the process requirements.

.. needbar:: Docs-As-Code Requirements Status
  :stacked:
  :show_sum:
  :xlabels: FROM_DATA
  :ylabels: FROM_DATA
  :colors: green,orange,red
  :legend:
  :transpose:
  :xlabels_rotation: 45
  :horizontal:

                   , implemented                                    , partially implemented                                          , not implemented, process not clear
  Common,  'tool_req__docs' in id and implemented == "YES" and "Common Attributes"         in tags and status == "valid", 'tool_req__docs' in id and implemented == "PARTIAL" and "Common Attributes"         in tags and status == "valid", 'tool_req__docs' in id and implemented == "NO" and         "Common Attributes" in tags and status == "valid", 'tool_req__docs' in id and         "Common Attributes" in tags and status != "valid"
  Doc,     'tool_req__docs' in id and implemented == "YES" and "Documents"                 in tags and status == "valid", 'tool_req__docs' in id and implemented == "PARTIAL" and "Documents"                 in tags and status == "valid", 'tool_req__docs' in id and implemented == "NO" and                 "Documents" in tags and status == "valid", 'tool_req__docs' in id and                 "Documents" in tags and status != "valid"
  Req,     'tool_req__docs' in id and implemented == "YES" and "Requirements"              in tags and status == "valid", 'tool_req__docs' in id and implemented == "PARTIAL" and "Requirements"              in tags and status == "valid", 'tool_req__docs' in id and implemented == "NO" and              "Requirements" in tags and status == "valid", 'tool_req__docs' in id and              "Requirements" in tags and status != "valid"
  Arch,    'tool_req__docs' in id and implemented == "YES" and "Architecture"              in tags and status == "valid", 'tool_req__docs' in id and implemented == "PARTIAL" and "Architecture"              in tags and status == "valid", 'tool_req__docs' in id and implemented == "NO" and              "Architecture" in tags and status == "valid", 'tool_req__docs' in id and              "Architecture" in tags and status != "valid"
  DDesign, 'tool_req__docs' in id and implemented == "YES" and "Detailed Design & Code"    in tags and status == "valid", 'tool_req__docs' in id and implemented == "PARTIAL" and "Detailed Design & Code"    in tags and status == "valid", 'tool_req__docs' in id and implemented == "NO" and    "Detailed Design & Code" in tags and status == "valid", 'tool_req__docs' in id and    "Detailed Design & Code" in tags and status != "valid"
  TVR,     'tool_req__docs' in id and implemented == "YES" and "Tool Verification Reports" in tags and status == "valid", 'tool_req__docs' in id and implemented == "PARTIAL" and "Tool Verification Reports" in tags and status == "valid", 'tool_req__docs' in id and implemented == "NO" and "Tool Verification Reports" in tags and status == "valid", 'tool_req__docs' in id and "Tool Verification Reports" in tags and status != "valid"
  Other,   'tool_req__docs' in id and implemented == "YES" and "Process / Other"           in tags and status == "valid", 'tool_req__docs' in id and implemented == "PARTIAL" and "Process / Other"           in tags and status == "valid", 'tool_req__docs' in id and implemented == "NO" and           "Process / Other" in tags and status == "valid", 'tool_req__docs' in id and           "Process / Other" in tags and status != "valid"
  SftyAn,  'tool_req__docs' in id and implemented == "YES" and "Safety Analysis"           in tags and status == "valid", 'tool_req__docs' in id and implemented == "PARTIAL" and "Safety Analysis"           in tags and status == "valid", 'tool_req__docs' in id and implemented == "NO" and           "Safety Analysis" in tags and status == "valid", 'tool_req__docs' in id and           "Safety Analysis" in tags and status != "valid"


🗂️ Common Attributes
#####################

.. note::
  To stay consistent with sphinx-needs (the tool behind docs-as-code), we'll use `need`
  for any kind of model element like a requirement, an architecture element or a
  feature description.


----------------------
🔢 ID
----------------------

.. tool_req:: Enforces need ID uniqueness
  :id: tool_req__docs_common_attr_id
  :implemented: YES
  :tags: Common Attributes
  :satisfies:
     gd_req__req_attr_uid,
     gd_req__tool_attr_uid,
     gd_req__arch_attribute_uid,
     gd_req__saf_attr_uid,
  :parent_covered: NO

  Docs-as-Code shall enforce that all Need IDs are globally unique across all included
  documentation instances.

  .. note::
     Within each docs-instance (as managed by sphinx-needs), IDs are guaranteed to be unique.
     When linking across instances, unique prefixes are automatically applied to maintain global uniqueness.

.. tool_req:: Enforces need ID scheme
  :id: tool_req__docs_common_attr_id_scheme
  :implemented: PARTIAL
  :tags: Common Attributes
  :satisfies:
    gd_req__req_attr_uid,
    gd_req__arch_attribute_uid,
    gd_req__saf_attr_uid,
    gd_req__req_check_mandatory,
  :parent_covered: NO: cannot check non-existent "doc__naming_conventions" in gd_req__req_attr_uid

  Docs-as-Code shall enforce that Need IDs follow the following naming scheme:

  * A prefix indicating the need type (e.g. `feature__`)
  * A middle part matching the hierarchical structure of the need:
     * For requirements: a portion of the feature tree or a component acronym
     * For architecture elements: the structural element (e.g. a part of the feature tree, component acronym)
     * For safety analysis (FMEA, DFA): name of analyzed structural element (e.g. Persistency, FEO, etc.)
  * Additional descriptive text to ensure human readability


----------------------
🏷️ Title
----------------------

.. tool_req:: Enforces title wording rules
  :id: tool_req__docs_common_attr_title
  :implemented: YES
  :tags: Common Attributes
  :satisfies:
    gd_req__req_attr_title,
    gd_req__saf_attr_title,
  :parent_covered: NO: Can not ensure summary

  Docs-as-Code shall enforce that all needs have titles and titles do not contain the following words:

  * shall
  * must
  * will


---------------------------
📝 Description
---------------------------

.. tool_req:: Enforces presence of description
  :id: tool_req__docs_common_attr_description
  :tags: Common Attributes
  :parent_covered: NO: Can not cover 'ISO/IEC/IEEE/29148'
  :implemented: YES
  :satisfies: gd_req__req_attr_description, gd_req__req_check_mandatory

  Docs-as-Code shall enforce that each need of type :need:`tool_req__docs_req_types` has a description (content)


.. tool_req:: Enforces description wording rules
  :id: tool_req__docs_common_attr_desc_wording
  :tags: Common Attributes
  :implemented: YES
  :satisfies:
    gd_req__req_desc_weak,
  :parent_covered: YES

  Docs-as-Code shall enforce that requirement descriptions do not contain the following weak words:
  ju-st, ab-out, rea-lly, so-me, th-ing, absol-utely

  This rule applies to:

  * all requirement types defined in :need:`tool_req__docs_req_types`, except process requirements.

  .. note::
    Artificial "-" added to avoid triggering violation of this requirment in this document.

----------------------------
🔒 Security Classification
----------------------------

.. tool_req:: Security: enforce classification
  :id: tool_req__docs_common_attr_security
  :implemented: YES
  :tags: Common Attributes
  :satisfies:
     gd_req__req_attr_security,
     gd_req__arch_attr_security,
     gd_req__req_check_mandatory,

  Docs-as-Code shall enforce that the ``security`` attribute has one of the following values:

  * YES
  * NO

  This rule applies to:

  * all requirement types defined in :need:`tool_req__docs_req_types`, except process and tool requirements.
  * all architecture elements defined in :need:`tool_req__docs_arch_types`.




---------------------------
🛡️ Safety Classification
---------------------------

.. tool_req:: Safety: enforce classification
  :id: tool_req__docs_common_attr_safety
  :tags: Common Attributes
  :implemented: YES
  :parent_covered: YES
  :satisfies:
     gd_req__req_check_mandatory,
     gd_req__req_attr_safety,
     gd_req__arch_attr_safety

  Docs-as-Code shall enforce that the ``safety`` attribute has one of the following values:

  * QM
  * ASIL_B


  This rule applies to:

  * all requirement types defined in :need:`tool_req__docs_req_types`, except process and tool requirements.
  * all architecture elements defined in :need:`tool_req__docs_arch_types`.



----------
🚦 Status
----------

.. tool_req:: Status: enforce attribute
  :id: tool_req__docs_common_attr_status
  :tags: Common Attributes
  :implemented: YES
  :parent_covered: NO: gd_req__saf_attr_status has additional constraints
  :satisfies:
    gd_req__req_attr_status,
    gd_req__arch_attr_status,
    gd_req__saf_attr_status,
    gd_req__req_check_mandatory,

  Docs-as-Code shall enforce that the ``status`` attribute has one of the following values:

  * valid
  * invalid

  This rule applies to:

  * all requirement types defined in :need:`tool_req__docs_req_types`, except process and tool requirements.
  * all architecture elements defined in :need:`tool_req__docs_arch_types`.
  * all safety analysis elements defined in :need:`tool_req__docs_saf_types`.



----------
Versioning
----------

.. tool_req:: Versioning: enforce attribute
   :id: tool_req__docs_common_attr_version
   :tags: Common Attributes
   :implemented: NO
   :parent_covered: NO: to be checked after demo
   :satisfies: gd_req__req_attr_version

   Docs-As-Code shall enable and enforce a versioning attribute for all needs.

   .. note::
     Exact nature to be decided, it could e.g. be a number, a string, a semantic version, a date or a hash.



.. tool_req:: Suspicious: Enforce attribute
   :id: tool_req__docs_common_attr_suspicious
   :tags: Common Attributes
   :implemented: NO
   :parent_covered: NO: parent talks about setting covered to false, but we want to issue a build error.
   :satisfies: gd_req__req_suspicious
   :status: invalid

   Docs-as-Code shall check if linked parent needs have different versions, compared to
   the version the need was originally linked to.




📚 Documents
#############

.. tool_req:: Document Types
  :id: tool_req__docs_doc_types
  :tags: Documents
  :implemented: YES
  :parent_covered: YES
  :satisfies: gd_req__doc_types

  Docs-as-Code shall support the following document types:

  * Generic Document (document)
  * Tool Verification Report (doc_tool)
  * Change Request is also a generic document

.. tool_req:: Mandatory attributes of Generic Documents
  :id: tool_req__docs_doc_generic_mandatory
  :tags: Documents
  :implemented: PARTIAL
  :satisfies:
   gd_req__doc_attributes_manual,
   gd_req__change_attr_impact_safety
  :parent_covered: YES

  Docs-as-Code shall enforce that each Generic Document ``doc__*`` has the following attributes:

  * status
  * security
  * safety
  * realizes

.. tool_req:: Mandatory Document attributes
  :id: tool_req__docs_doc_attr
  :tags: Documents
  :implemented: NO
  :satisfies:
   gd_req__doc_author,
   gd_req__doc_approver,
   gd_req__doc_reviewer,
   gd_req__change_attr_title,
  :parent_covered: NO, process requirement has changed and we do not understand the new wording.
  :status: invalid

  Docs-as-Code shall enforce that each :need:`tool_req__docs_doc_types` has the
  following attributes:

  * title (implicitly enforced by sphinx-needs)
  * author
  * approver
  * reviewer


.. tool_req:: Document author is autofilled
  :id: tool_req__docs_doc_attr_author_autofill
  :tags: Documents
  :implemented: NO
  :satisfies: gd_req__doc_author
  :parent_covered: NO, process requirement has changed and we do not understand the new wording.
  :status: invalid

  Docs-as-Code shall provide an automatic mechanism to determine document authors.

  Contributors responsible for more than 50% of the content shall be considered the
  document author. Contributors are accumulated over all commits to the file containing
  the document.

  .. note::
    The requirement is currently invalid as it's currently unclear how the contribution
    % are counted and how to accumulate %.

.. tool_req:: Document approver is autofilled
  :id: tool_req__docs_doc_attr_approver_autofill
  :tags: Documents
  :implemented: NO
  :satisfies: gd_req__doc_approver
  :parent_covered: NO, process requirement has changed and we do not understand the new wording.
  :status: invalid

  Docs-as-Code shall provide an automatic mechanism to determine the document approver.

  The approver shall be the approvers listed in *CODEOWNERS* of the last pull request of
  the file containing the document.


.. tool_req:: Document reviewer is autofilled
  :id: tool_req__docs_doc_attr_reviewer_autofill
  :tags: Documents
  :implemented: NO
  :satisfies: gd_req__doc_reviewer
  :parent_covered: NO, process requirement has changed and we do not understand the new wording.
  :status: invalid

  Docs-as-Code shall provide an automatic mechanism to determine the document reviewers.

  The reviewer shall be the approvers NOT listed in *CODEOWNERS* of the last pull
  request of the file containing the document.


--------
 Mapping
--------

.. needtable::
   :style: table
   :types: gd_req
   :columns: id;satisfies_back as "tool_req"
   :filter: "gd_req__doc" in id


📋 Requirements
################

-------------------------
🔢 Requirement Types
-------------------------

.. tool_req:: Requirements Types
  :id: tool_req__docs_req_types
  :tags: Requirements
  :implemented: YES
  :satisfies: gd_req__req_structure
  :parent_covered: YES: Together with tool_req__docs_linkage

  Docs-as-Code shall support the following requirement types:

  * Stakeholder requirement (stkh_req)
  * Feature requirement (feat_req)
  * Component requirement (comp_req)
  * Assumption of use requirement (aou_req)
  * Process requirement (gd_req)
  * Tool requirement (tool_req)

-------------------------
🏷️ Attributes
-------------------------

.. tool_req:: Enforces rationale attribute
  :id: tool_req__docs_req_attr_rationale
  :tags: Requirements
  :implemented: YES
  :parent_covered: NO: Can not ensure correct reasoning
  :satisfies: gd_req__req_attr_rationale, gd_req__req_check_mandatory

  Docs-as-Code shall enforce that each stakeholder requirement (stkh_req) contains a ``rationale`` attribute.

.. tool_req:: Enforces requirement type classification
  :id: tool_req__docs_req_attr_reqtype
  :tags: Requirements
  :implemented: YES
  :satisfies: gd_req__req_attr_type

  Docs-as-Code shall enforce that each need of type :need:`tool_req__docs_req_types`
  except process and tool requirements has a ``reqtype`` attribute with one of the
  following values:

  * Functional
  * Interface
  * Process
  * Non-Functional

.. tool_req:: Enables marking requirements as "covered"
  :id: tool_req__docs_req_attr_reqcov
  :tags: Requirements
  :implemented: PARTIAL
  :satisfies: gd_req__req_attr_req_cov

  Docs as code shall shall enable marking requirements as covered by their linked children.

  Attribute ``reqcov`` must be one of the following values:
      * Yes
      * No

  .. note::
     No concept yet, as parents are generally not aware of their children.

.. tool_req:: Support requirements test coverage
  :id: tool_req__docs_req_attr_testcov
  :tags: Requirements
  :implemented: PARTIAL
  :parent_covered: YES
  :satisfies: gd_req__req_attr_test_covered
  :status: invalid

  Docs-As-Code shall allow for every need of type :need:`tool_req__docs_req_types` to
  have a ``testcovered`` attribute, which must be one of:

  * Yes
  * No

  .. note::
     No concept yet


.. tool_req:: Enforce validity attribute correctness
  :id: tool_req__docs_req_attr_validity_correctness
  :tags: Requirements
  :implemented: PARTIAL
  :parent_covered: YES
  :satisfies: gd_req__req_validity
  :status: valid

  Docs-as-Code shall enforce that the ``valid_from`` and ``valid_until`` attributes of stakeholder and feature requirements are correct.

  The format of a milestone is something like "v0.5" or "v1.0.1".
  No suffixes like "-SNAPSHOT" or "-beta" are allowed.

.. tool_req:: Enforce validity start is before end
  :id: tool_req__docs_req_attr_validity_consistency
  :tags: Requirements
  :implemented: PARTIAL
  :parent_covered: YES
  :satisfies: gd_req__req_validity
  :status: valid

  Docs-as-Code shall enforce that ``valid_from`` is before ``valid_until`` attribute in stakeholder and feature requirements.
  We consider "from" is inclusive but "until" is exclusive, so from v0.5 until v1.0 means valid for v0.5 but not for v1.0.
  If either attribute is missing, no check is performed.


-------------------------
🔗 Links
-------------------------

.. tool_req:: Enables needs linking via satisfies attribute
  :id: tool_req__docs_req_link_satisfies_allowed
  :tags: Requirements
  :implemented: PARTIAL
  :satisfies: gd_req__req_linkage, gd_req__req_traceability
  :parent_covered: YES
  :status: invalid

  Docs-as-Code shall enforce that linking between model elements via the ``satisfies``
  attribute follows defined rules. Having at least one link is mandatory.

  Allowed source and target combinations are defined in the following table:

  .. table::
     :widths: auto

     ================================ ===================================================
     Source Type                      Allowed Link Target
     ================================ ===================================================
     Feature Requirements             Stakeholder Requirements
     Component Requirements           Feature Requirements
     Process Requirements             Workflows
     Tooling Requirements             Process Requirements, Stakeholder Requirements
     ================================ ===================================================

  .. note::
      Certain tool requirements do not have a matching process requirement.

.. tool_req:: Safety: enforce safe linking
   :id: tool_req__docs_common_attr_safety_link_check
   :tags: Common Attributes
   :implemented: YES
   :parent_covered: YES
   :satisfies: gd_req__req_linkage_safety

   QM requirements (safety == QM) shall not be linked to safety requirements (safety != QM) via the ``satisfies`` attribute.

🏛️ Architecture
################

----------------------
🔢 Architecture Types
----------------------

.. tool_req:: Architecture Types
  :id: tool_req__docs_arch_types
  :tags: Architecture
  :satisfies:
     gd_req__arch_hierarchical_structure,
     gd_req__arch_build_blocks,
  :implemented: YES
  :parent_covered: NO
  :status: invalid

  Docs-as-Code shall support the following architecture element types:

  * Feature Static View (feat_arc_sta)
  * Feature (feat)
  * Logical Interface (logic_arc_int)
  * Logical Interface Operation (logic_arc_int_op)
  * Component Static View (comp_arc_sta)
  * Component (comp)
  * Interface (real_arc_int)
  * Interface Operation (real_arc_int_op)

--------------------------
Architecture Attributes
--------------------------

.. tool_req:: Architecture Mandatory Attributes
   :id: tool_req__docs_arch_attr_mandatory
   :tags: Architecture
   :satisfies:
      gd_req__arch_attr_mandatory,
      gd_req__arch_attr_fulfils,
   :implemented: PARTIAL
   :parent_covered: YES
   :parent_has_problem: YES: Metamodel & Process aren't the same. Some definitions are not consistent in Process

   Docs-as-Code shall enforce that the following attributes are present in all needs of type :need:`tool_req__docs_arch_types`

   * Fulfils
   * Safety
   * Security
   * Status
   * UID



------------------------
🔗 Linkage
------------------------

.. tool_req:: Mandatory Architecture Attribute: fulfils
  :id: tool_req__docs_arch_link_fulfils
  :tags: Architecture
  :implemented: PARTIAL
  :satisfies:
   gd_req__arch_linkage_requirement_type,
   gd_req__arch_attr_fulfils,
   gd_req__arch_traceability,
   gd_req__req_linkage_fulfill
  :parent_covered: YES

  Docs-as-Code shall enforce that linking via the ``fulfils`` attribute follows defined rules.

  Allowed source and target combinations are defined in the following table:

  .. table::
     :widths: auto

     ====================================  ==========================================
     Link Source                           Allowed Link Target
     ====================================  ==========================================
     feat_arc_sta                          feat_req
     feat_arc_dyn                          feat_req
     logic_arc_int                         feat_req
     comp_arc_sta                          comp_req
     comp_arc_dyn                          comp_req
     real_arc_int                          comp_req
     ====================================  ==========================================


.. tool_req:: Ensure safety architecture elements link a safety requirement
  :id: tool_req__docs_arch_link_safety_to_req
  :tags: Architecture
  :implemented: PARTIAL
  :satisfies: gd_req__arch_linkage_requirement
  :parent_covered: YES

  Docs-as-Code shall enforce that architecture elements of type
  :need:`tool_req__docs_arch_types` with ``safety != QM`` are linked to at least one
  requirements of type :need:`tool_req__docs_req_types` with the exact same ``safety``
  value.

.. tool_req:: Ensure qm architecture elements do not fulfill safety requirements
  :id: tool_req__docs_arch_link_qm_to_safety_req
  :tags: Architecture
  :implemented: PARTIAL
  :satisfies: gd_req__arch_linkage_requirement
  :parent_covered: YES

  Docs-as-Code shall enforce that architecture elements of type
  :need:`tool_req__docs_arch_types` with ``safety == QM`` are not linked to requirements
  of type :need:`tool_req__docs_req_types` with ``safety != QM``.


.. tool_req:: Restrict links for safety requirements
  :id: tool_req__docs_req_arch_link_safety_to_arch
  :tags: Architecture
  :implemented: PARTIAL
  :satisfies:
    gd_req__arch_linkage_safety_trace,
    gd_req__req_linkage_safety,
  :parent_covered: NO

  Docs-as-Code shall enforce that valid safety architectural elements (Safety != QM) can
  only be linked against valid safety architectural elements.

.. tool_req:: Security: Restrict linkage
  :id: tool_req__docs_arch_link_security
  :tags: Architecture
  :implemented: YES
  :parent_covered: YES
  :satisfies: gd_req__arch_linkage_security_trace

  Docs-as-Code shall enforce that security relevant :need:`tool_req__docs_arch_types` (Security ==
  YES) can only be linked against security relevant :need:`tool_req__docs_arch_types`.

----------------------
🖼️ Diagram Related
----------------------

.. tool_req:: Support Diagram drawing of architecture
  :id: tool_req__docs_arch_views
  :tags: Architecture
  :implemented: YES
  :satisfies:
    gd_req__arch_viewpoints,
  :parent_covered: YES

  Docs-as-Code shall enable the rendering of diagrams for the following architecture views:

  * Feature Package Diagram (feat_arc_sta)
  * Feature Sequence Diagram (feat_arc_dyn)
  * Feature Interface View (logic_arc_int)
  * Component Package Diagram (comp_arc_sta)
  * Component Sequence Diagram (comp_arc_dyn)
  * Component Interface (real_arc_int)
  * Module View (mod_view_sta)

  .. note::
    feat_arc_sta, comp_arc_sta, logic_arc_int, real_arc_int are architecture views,
    but are still defined as architectural elements, which means they have the properties of
    architectural elements.

💻 Detailed Design & Code
##########################

----------------
🔗 Code Linkage
----------------

.. tool_req:: Supports linking to source code
  :tags: Detailed Design & Code
  :id: tool_req__docs_dd_link_source_code_link
  :implemented: YES
  :parent_covered: NO: we only enable linking, we do not link
  :satisfies:
    gd_req__req_attr_impl,

  Docs-as-Code shall allow source code to link to requirement sphinx-needs objects.

  A link to the corresponding source code location in GitHub shall be generated in the
  generated documentation within the linked requirement.



.. tool_req:: Feature Flags
   :id: tool_req__docs_dd_feature_flag
   :tags: Detailed Design & Code
   :implemented: NO
   :parent_covered: YES
   :satisfies: gd_req__req_linkage_architecture_switch

   Docs-as-Code shall allow for a to-be-defined list of checks to be non-fatal for non
   release builds. These are typically better suited for metrics than for checks.

   e.g. gd_req__req_linkage_architecture


.. tool_req:: Static Diagram for Unit Interactions
   :id: tool_req__docs_dd_sta
   :tags: Detailed Design & Code
   :implemented: YES
   :parent_covered: YES
   :satisfies: gd_req__impl_static_diagram

   Provide needs type ``dd_sta`` for static diagrams showing unit interactions as UML.

.. .. tool_req:: Dynamic Diagram for Unit Interactions
..    :id: tool_req__docs_dd_dyn
..    :tags: Detailed Design & Code
..    :implemented: YES
..    :parent_covered: YES
..    :satisfies: gd_req__impl_dynamic_diagram

..    Provide needs type ``dd_dyn`` for dynamic diagrams showing unit interactions as UML.


Testing
#######


.. tool_req:: Supports linking to test cases
  :id: tool_req__docs_test_link_testcase
  :tags: Testing
  :implemented: PARTIAL
  :parent_covered: YES
  :satisfies: gd_req__req_attr_testlink

  Docs-as-Code shall allow requirements of type :need:`tool_req__docs_req_types` to
  include a ``testlink`` attribute.

  This attribute shall support linking test cases to requirements.


.. tool_req:: Extract Metadata from Tests
   :id: tool_req__docs_test_metadata_mandatory_1
   :tags: Testing
   :implemented: NO
   :parent_covered: NO
   :satisfies: gd_req__verification_checks

   Docs-as-Code shall ensure that each test case has TestType and DerivationTechnique set.

.. tool_req:: Extract Metadata from Tests
   :id: tool_req__docs_test_metadata_mandatory_2
   :tags: Testing
   :implemented: NO
   :parent_covered: NO
   :satisfies: gd_req__verification_checks
   :status: invalid

   Docs-as-Code shall ensure that each test case has a non empty description.

   .. note:: this will probably be implemented outside of docs-as-code.

.. tool_req:: Extract Metadata from Tests
   :id: tool_req__docs_test_metadata_link_levels
   :tags: Testing
   :implemented: NO
   :parent_covered: NO
   :satisfies: gd_req__verification_checks
   :status: invalid

   Docs-as-Code shall ensure that test cases link to requirements on the correct level:

    - If Partially/FullyVerifies are set in Feature Integration Test these shall link to Feature Requirements
    - If Partially/FullyVerifies are set in Component Integration Test these shall link to Component Requirements
    - If Partially/FullyVerifies are set in Unit Test these shall link to Component Requirements


🧪 Tool Verification Reports
############################

.. they are so different, that they need their own section

.. tool_req:: Enforce safety classification
  :id: tool_req__docs_tvr_safety
  :tags: Tool Verification Reports
  :implemented: YES
  :parent_covered: YES
  :satisfies: gd_req__tool_attr_safety_affected, gd_req__tool_check_mandatory

  Docs-as-Code shall enforce that every Tool Verification Report (`doc_tool`) includes a
  ``safety_affected`` attribute with one of the following values:

  * YES
  * NO

.. tool_req:: Enforce security classification
  :id: tool_req__docs_tvr_security
  :tags: Tool Verification Reports
  :implemented: YES
  :parent_covered: YES
  :satisfies: gd_req__tool_attr_security_affected, gd_req__tool_check_mandatory

  Docs-as-Code shall enforce that every Tool Verification Report (`doc_tool`) includes a
  `security_affected` attribute with one of the following values:

  * YES
  * NO


.. tool_req:: Enforce status classification
  :id: tool_req__docs_tvr_status
  :tags: Tool Verification Reports
  :implemented: YES
  :satisfies: gd_req__tool_attr_status, gd_req__tool_check_mandatory
  :parent_covered: YES

  Docs-as-Code shall enforce that every Tool Verification Report (`doc_tool`) includes a
  `status` attribute with one of the following values:

  * draft
  * evaluated
  * qualified
  * released
  * rejected

.. tool_req:: Enforce version attribute
  :id: tool_req__docs_tvr_version
  :tags: Tool Verification Reports
  :implemented: YES
  :satisfies: gd_req__tool_attr_version
  :parent_covered: YES

  Docs-as-Code shall enforce that every Tool Verification Report (`doc_tool`) includes a
  `version` attribute.

.. tool_req:: Enforce confidence level classification
  :id: tool_req__docs_tvr_confidence_level
  :tags: Tool Verification Reports
  :implemented: YES
  :satisfies: gd_req__tool_attr_tcl
  :parent_covered: YES

  Docs-as-Code shall enforce that every Tool Verification Report (`doc_tool`) includes a
  `tcl` attribute with one of the following values:

  * LOW
  * HIGH

⚙️ Process / Other
###################

.. tool_req:: Workflow Types
  :id: tool_req__docs_wf_types
  :tags: Process / Other
  :implemented: YES
  :satisfies: gd_req__process_management_build_blocks_attr, gd_req__process_management_build_blocks_link

  Docs-as-Code shall support the following workflow types:

  * Workflow (wf)

.. tool_req:: Standard Requirement Types
  :id: tool_req__docs_stdreq_types
  :tags: Process / Other
  :implemented: YES

  Docs-as-Code shall support the following requirement types:

  * Standard requirement (std_req)


🛡️ Safety Analysis (DFA + FMEA)
###############################


.. tool_req:: Safety Analysis Need Types
  :id: tool_req__docs_saf_types
  :implemented: YES
  :tags: Safety Analysis
  :satisfies:
    gd_req__saf_structure,
    gd_req__saf_attr_uid,
  :parent_covered: YES

   Docs-As-Code shall support the following need types:

  * Feature FMEA (Failure Modes and Effect Analysis) -> ``feat_saf_fmea``
  * Component FMEA (Failure Modes and Effect Analysis) -> ``comp_saf_fmea``
  * Feature DFA (Dependend Failure Analysis) -> ``feat_saf_dfa``
  * Component DFA (Dependent Failure Analysis) -> ``comp_saf_dfa``

.. tool_req:: Safety Analysis Mandatory Attributes
  :id: tool_req__docs_saf_attrs_mandatory
  :implemented: YES
  :tags: Safety Analysis
  :satisfies:
    gd_req__saf_attr_mandatory,
  :parent_covered: YES

  All safety analysis elements in :need:`tool_req__docs_saf_types`
  shall have the following mandatory attributes:

  * DFA-only attribute: ``failure_id``
  * FMEA-only attribute: ``fault_id``
  * attribute: ``failure_effect``
  * attribute: ``status``
  * attribute: ``sufficient``
  * attribute: ``title`` (all Needs elements have a title)
  * attribute: ``id`` (all Needs elements have an id)


.. tool_req:: Safety Analysis Mitigation Attribute
  :id: tool_req__docs_saf_attrs_mitigated_by
  :implemented: NO
  :tags: Safety Analysis
  :satisfies:
    gd_req__saf_attr_mitigated_by,
    gd_req__saf_attr_requirements,
    gd_req__saf_attr_requirements_check,
    gd_req__saf_attr_aou,
    gd_req__saf_linkage_safety,
  :parent_covered: YES

  Docs-As-Code shall enforce valid needs (`status` == `valid`) of type
  :need:`tool_req__docs_saf_types` to have at least one `mitigated_by` link to a
  requirement on the corresponding level.

  At least one of the linked requirements must have
  the same ASIL level or a higher one.

  It can be ``comp_req`` or ``aou_req``.


.. tool_req:: Safety Analysis Mitigation Issue Attribute
  :id: tool_req__docs_saf_attrs_mitigation_issue
  :implemented: YES
  :tags: Safety Analysis
  :satisfies: gd_req__saf_attr_mitigation_issue
  :parent_covered: NO

  Docs-As-Code shall allow needs of type :need:`tool_req__docs_saf_types` to have a
  `mitigation_issue` attribute which links to a GitHub issue.


.. tool_req:: Safety Analysis Sufficient Attribute
  :id: tool_req__docs_saf_attrs_sufficient
  :implemented: YES
  :tags: Safety Analysis
  :satisfies: gd_req__saf_attr_sufficient
  :parent_covered: YES

  Docs-As-Code shall enforce needs of type :need:`tool_req__docs_saf_types` to
  have a `sufficient` attribute , which can have one of the following values:

  * yes
  * no

.. tool_req:: Safety Analysis Sufficient Check
  :id: tool_req__docs_saf_attrs_sufficient_check
  :implemented: NO
  :tags: Safety Analysis
  :satisfies: gd_req__saf_attr_sufficient
  :parent_covered: YES

  Docs-As-Code shall ensure needs of type :need:`tool_req__docs_saf_types` with
  `sufficient` == `yes` have a `mitigated_by` entry.


.. tool_req:: Safety Analysis Mandatory Content
   :id: tool_req__docs_saf_attrs_content
   :implemented: NO
   :tags: Safety Analysis
   :satisfies: gd_req__saf_argument
   :parent_covered: NO

   Docs-As-Code shall enforce needs of type :need:`tool_req__docs_saf_types` to have a
   non empty content.



.. tool_req:: Safety Analysis Linkage Violates
  :id: tool_req__docs_saf_attrs_violates
  :implemented: NO
  :tags: Safety Analysis
  :satisfies:
    gd_req__saf_linkage_check,
    gd_req__saf_linkage,
  :parent_covered: YES

  Docs-As-Code shall enforce that needs of type :need:`tool_req__docs_saf_types` have a
  `violates` links to at least one dynamic / static diagram according to the table.


  .. table::
     :widths: auto

     =============  ===================
     Link Source    Allowed Link Target
     =============  ===================
     feat_saf_dfa   feat_arc_sta
     comp_saf_dfa   comp_arc_sta
     feat_saf_fmea  feat_arc_dyn
     comp_saf_fmea  comp_arc_dyn
     =============  ===================



.. tool_req:: FMEA: fault id attribute
   :id: tool_req__docs_saf_attr_fmea_fault_id
   :implemented: NO
   :tags: Safety Analysis
   :satisfies: gd_req__saf_attr_fault_id
   :parent_covered: NO

   Docs-As-Code shall enforce that needs of type DFA (see
   :need:`tool_req__docs_saf_types`) have a `fault_id` attribute.

   Allowed values are listed as ID in tables at :need:`gd_guidl__dfa_failure_initiators`.


.. tool_req:: DFA: failure id attribute
   :id: tool_req__docs_saf_attr_dfa_failure_id
   :implemented: NO
   :tags: Safety Analysis
   :satisfies: gd_req__saf_attr_failure_id
   :parent_covered: NO

   Docs-As-Code shall enforce that needs of type DFA (see
   :need:`tool_req__docs_saf_types`) have a `fault_id` attribute.

   Allowed values are listed as ID in tables at :need:`gd_guidl__dfa_failure_initiators`.


.. tool_req:: Failure Effect
   :id: tool_req__docs_saf_attr_fmea_failure_effect
   :implemented: NO
   :tags: Safety Analysis
   :satisfies: gd_req__saf_attr_feffect
   :parent_covered: NO
   :status: invalid

   Docs-As-Code shall enforce that every Safety Analysis has a short description of the failure effect (e.g. failure lead to an unintended actuation of the analysed element)

----------------------------------------------------------------
Safety Analysis (DFA + FMEA) Process to Tool Requirement Mapping
----------------------------------------------------------------

.. needtable::
   :style: table
   :types: gd_req
   :columns: id;satisfies_back as "tool_req"
   :filter: "gd_req__saf" in id


🗺️ Full Mapping
################

Process to tools:

.. needtable::
   :style: table
   :types: gd_req
   :columns: id;satisfies_back as "tool_req"

Overview of Tool to Process Requirements
########################################

.. needtable::
   :types: tool_req
   :filter: any(s.startswith("gd_req") for s in satisfies)
   :columns: satisfies as "Process Requirement" ;id as "Tool Requirement";implemented;source_code_link
   :style: table


..
.. ------------------------------------------------------------------------
..

Grouped Requirements
####################

.. tool_req:: Metamodel
  :id: tool_req__docs_metamodel
  :tags: metamodel
  :implemented: YES

  Docs-as-Code shall provide a metamodel for definining config in a  `metamodel.yaml` in the source code repository.

  .. note:: "satisfied by" is something like "used by" or "required by".


.. needextend:: c.this_doc() and type == 'tool_req'
  :safety: ASIL_B
  :security: NO

.. needextend:: c.this_doc() and type == 'tool_req' and not status
  :status: valid

.. needextend:: "metamodel.yaml" in source_code_link
  :+satisfies: tool_req__docs_metamodel
  :+tags: config
