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

.. test_metadata::
   :id: test_metadata__common_attrs_status
   :fully_verifies_list: tool_req__docs_common_attr_status[version==2]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that the common ``status`` attribute is enforced on every directive
   that declares it in the metamodel.

   Every directive type has its own metamodel ``status`` regex.
   The regex patterns fall into two equivalence classes:

   * ``^(valid|invalid|valid_inspected)$`` — requirement types
     (stkh_req, feat_req, comp_req, aou_req) and architecture types
     (feat, comp, feat_arc_sta, feat_arc_dyn, comp_arc_sta, comp_arc_dyn,
     logic_arc_int, logic_arc_int_op, real_arc_int, real_arc_int_op).
   * ``^(valid|invalid)$`` — safety-analysis types
     (feat_saf_fmea, comp_saf_fmea, plat_saf_dfa, feat_saf_dfa,
     comp_saf_dfa).

   One representative from each class is tested for valid and invalid values.
   Missing-attribute is verified on all requirement types and one
   representative safety-analysis type.


.. stkh_req:: Valid status on a requirement type
   :id: stkh_req__status__good
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :rationale: valid status
   :valid_from: v1.0
   :expect_not: does not follow pattern, missing required attribute: `status`


.. stkh_req:: Invalid status on a requirement type
   :id: stkh_req__status__bad
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: draft
   :rationale: invalid status
   :valid_from: v1.0
   :expect: status (draft): does not follow pattern


.. stkh_req:: Missing status on a requirement type
   :id: stkh_req__status__missing
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :rationale: missing status
   :valid_from: v1.0
   :expect: is missing required attribute: `status`


.. stkh_req:: Valid: ``invalid`` and ``valid_inspected`` are also allowed
   :id: stkh_req__status__alternatives
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid_inspected
   :rationale: valid_inspected is a valid value
   :valid_from: v1.0
   :expect_not: does not follow pattern


.. feat_saf_fmea:: Invalid status on a safety-analysis type
   :id: feat_saf_fmea__status__bad
   :fault_id: FD_NEG
   :failure_effect: Negative `status` test for feat_saf_fmea.
   :sufficient: no
   :status: draft
   :violates: feat_arc_sta__status_support
   :expect: status (draft): does not follow pattern


.. feat_req:: Missing status on a feature requirement
   :id: feat_req__status__missing
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :rationale: missing status
   :valid_from: v1.0
   :satisfied_by: feat__status_support
   :expect: is missing required attribute: `status`


.. comp_req:: Missing status on a component requirement
   :id: comp_req__status__missing
   :reqtype: Interface
   :safety: QM
   :security: NO
   :satisfied_by: comp__status_support
   :expect: is missing required attribute: `status`

   Missing status test for comp_req.


.. aou_req:: Missing status on an assumption-of-use requirement
   :id: aou_req__status__missing
   :reqtype: Functional
   :safety: QM
   :security: NO
   :expect: is missing required attribute: `status`

   Missing status test for aou_req.


.. feat_saf_fmea:: Missing status on a safety-analysis type
   :id: feat_saf_fmea__status__missing
   :fault_id: FD_NEG
   :failure_effect: Negative `status` test for feat_saf_fmea.
   :sufficient: no
   :violates: feat_arc_sta__status_support
   :expect: is missing required attribute: `status`


..
   Support needs used as link targets by the negative fixtures above.
   All are valid so they do not interact with the safety graph checks.


.. feat:: Support feature for status tests
   :id: feat__status_support
   :version: 1
   :security: NO
   :safety: QM
   :status: valid


.. comp:: Support component for status tests
   :id: comp__status_support
   :version: 1
   :security: NO
   :safety: QM
   :status: valid


.. logic_arc_int:: Support logical interface for status tests
   :id: logic_arc_int__status_support
   :security: NO
   :safety: QM
   :status: valid


.. logic_arc_int_op:: Support logical interface operation for status tests
   :id: logic_arc_int_op__status_support
   :security: NO
   :safety: QM
   :status: valid
   :included_by: logic_arc_int__status_support


.. feat_arc_sta:: Support feature static view for status tests
   :id: feat_arc_sta__status_support
   :security: NO
   :safety: QM
   :status: valid
   :includes: logic_arc_int__status_support, logic_arc_int_op__status_support
   :belongs_to: feat__status_support
