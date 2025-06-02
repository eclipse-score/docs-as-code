.. _requirements:

=================================
Requirements (Process Compliance)
=================================

.. needtable::
   :filter: c.this_doc()
   :columns: id;title;implemented

Details
=======

.. Enforced via sphinx-needs
.. tool_req:: Enforces unique requirement ids
   :id: tool_req__ensure_unique_id
   :implemented: YES
   :satisfies: PROCESS_gd_req__req__attr_uid

   The tool shall enforce unique ids for requirements


.. Enforced via sphinx-needs
.. tool_req:: Enforce requirement type
   :id: tool_req__ensure_requirement_type
   :implemented: YES
   :satisfies: PROCESS_gd_req__req__attr_uid

   The tool shall enfore that each need has a requirement type

..
   Feature Tree?? whats that?
.. tool_req:: Help
   :id: tool_req__no_idea
   :implemented: ????
   :satisfies: PROCESS_gd_req__req__attr_uid



.. Enforced through custom checks
.. tool_req:: Check words in title
   :id: tool_req__check_title
   :implemented: YES
   :satisfies: PROCESS_gd_req__requirements_attr_title

   The tool shall enforce that 'shall' will not appear in the title of a need that
   is of type: Stakeholder, Feature or Component requirement


.. Not enforced but possible
.. tool_req:: Enforce descriptions
   :id: tool_req__enforce_descriptions
   :implemented: NO
   :satisfies: PROCESS_gd_req__requirements_attr_description

   The tool shall enforce that each requirement has a description


.. Enforced through the metamodel + custom checks
.. tool_req:: Enforce reuqirement attribute: Type
   :id: tool_req__enforce_attr_type
   :implemented: YES
   :satisfies: PROCESS_gd_req__req__attr_type

   The tool shall enforce that each requirement has one of the following types
   in the attribute 'reqtype':
   - Functional
   - Interface
   - Process
   - Legal
   - Non-Functional


.. Enforced through metamodel + custom checks
.. tool_req:: Enforce reuqirement attribute: Security
   :id: tool_req__enforce_attr_security
   :implemented: YES
   :satisfies: PROCESS_gd_req__requirements_attr_security

   The tool shall enforce that each requirement has one of the following strings in the
   attribute 'security':
   - YES
   - NO

.. Enforced through metamodel + custom checks
.. tool_req:: Enforce reuqirement attribute: Safety
   :id: tool_req__enforce_attr_safety
   :implemented: YES
   :satisfies: PROCESS_gd_req__req__attr_safety

   The tool shall enforce that each requirement has one of the following strings in the
   attribute 'safety':
   - QM
   - ASIL_B
   - ASIL_D

.. Enforced through metamodel + custom checks
.. tool_req:: Enforce reuqirement attribute: Status
   :id: tool_req__enforce_attr_status
   :implemented: YES
   :satisfies: PROCESS_gd_req__req__attr_status

   The tool shall enforce that each requirement has one of the following strings in the
   attribute 'status':
   - valid
   - invalid


.. Enforced partially. The 'sensible rationale' part can not be enforced automatically
.. Is 'PARITAL' correct then?
.. tool_req:: Enforce reuqirement attribute: Rationale
   :id: tool_req__enforce_attr_rationale
   :implemented: PARTIAL
   :satisfies: PROCESS_gd_req__req__attr_rationale

   The tool shall enforce that a attribute named rationale is present and filled.

.. This is a bit unclear imo. Is this a 'MUST' for all requirements or is this just, if they link
.. then they are only allowed to link to those?
.. tool_req:: Requirement linking
   :id: tool_req__enable_linking
   :implemented: ????
   :satisfies: PROCESS_gd_req__req__linkage

   Needs clarification

.. Also not sure what in the world this is refering to
.. tool_req:: Requirement attribute: Requirement covered
   :id: tool_req__requirement_covered
   :implemented: ????
   :satisfies: PROCESS_gd_req__req__attr_req_cov


.. Need to clarify if this is needed 'cross-repo' as well
.. tool_req:: Requirement attribute: code link
   :id: tool_req__
   :implemented: PARTIAL
   :satisfies: PROCESS_gd_req__req__attr_impl

   The tool shall enable a way to link requirements to a code location on github

..
   You can copy this here for an easier time

   .. tool_req:: Snippet
      :id: tool_req__
      :implemented:
      :satisfies:




.. needextend:: c.this_doc() and type == 'tool_req'
   :safety: QM
   :security: NO
   :status: valid
   :reqtype: Functional
