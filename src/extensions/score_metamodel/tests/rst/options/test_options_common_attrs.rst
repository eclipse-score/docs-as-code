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
   :id: test_metadata__common_attrs
   :fully_verifies_list: tool_req__docs_common_attr_status[version==2], tool_req__docs_common_attr_security[version==1]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that the common ``status`` and ``security`` attributes are enforced on
   every directive that declares them in the metamodel:
   the four requirement types (stkh_req, feat_req, comp_req, aou_req),
   the eight architecture element/view types, and - for ``status`` only -
   the five safety-analysis types.

   Every directive has its own metamodel regex,
   so each one gets at least one invalid-value (negative) case;
   the missing-value cases cover the mandatory-attribute mechanism
   for all four requirement types.


.. stkh_req:: Valid common status and security values
   :id: stkh_req__common_attrs__good
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: YES
   :status: valid
   :rationale: valid common attributes
   :valid_from: v1.0
   :expect_not: does not follow pattern, missing required attribute: `status`, missing required attribute: `security`


.. stkh_req:: Invalid common status
   :id: stkh_req__common_attrs__bad_status
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: draft
   :rationale: invalid status
   :valid_from: v1.0
   :expect: status (draft): does not follow pattern
   :expect_not: security (NO): does not follow pattern


.. stkh_req:: Missing common status
   :id: stkh_req__common_attrs__missing_status
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :rationale: missing status
   :valid_from: v1.0
   :expect: is missing required attribute: `status`


.. stkh_req:: Invalid common security
   :id: stkh_req__common_attrs__bad_security
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: MAYBE
   :status: valid
   :rationale: invalid security
   :valid_from: v1.0
   :expect: security (MAYBE): does not follow pattern
   :expect_not: status (valid): does not follow pattern


.. stkh_req:: Missing common security
   :id: stkh_req__common_attrs__missing_security
   :version: 1
   :reqtype: Functional
   :safety: QM
   :status: valid
   :rationale: missing security
   :valid_from: v1.0
   :expect: is missing required attribute: `security`


.. stkh_req:: Valid invalid status and NO security values
   :id: stkh_req__common_attrs__invalid_no
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: invalid
   :rationale: both values are allowed
   :valid_from: v1.0
   :expect_not: does not follow pattern


..
   Support needs used as link targets by the negative fixtures below.
   All are valid (`status: valid`, `safety: QM`, `security: NO`),
   so they do not interact with the safety/security graph checks.


.. feat:: Support feature
   :id: feat__attrs_support
   :version: 1
   :security: NO
   :safety: QM
   :status: valid


.. logic_arc_int:: Support logical interface
   :id: logic_arc_int__attrs_support
   :security: NO
   :safety: QM
   :status: valid


.. logic_arc_int_op:: Support logical interface operation
   :id: logic_arc_int_op__attrs_support
   :security: NO
   :safety: QM
   :status: valid
   :included_by: logic_arc_int__attrs_support


.. comp:: Support component
   :id: comp__attrs_support
   :version: 1
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: feat__attrs_support


.. comp_arc_sta:: Support component package view
   :id: comp_arc_sta__attrs_support
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: comp__attrs_support


.. comp_arc_dyn:: Support component sequence view
   :id: comp_arc_dyn__attrs_support
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: comp__attrs_support


.. real_arc_int:: Support interface
   :id: real_arc_int__attrs_support
   :security: NO
   :safety: QM
   :status: valid
   :language: cpp


.. real_arc_int_op:: Support interface operation
   :id: real_arc_int_op__attrs_support
   :security: NO
   :safety: QM
   :status: valid
   :included_by: real_arc_int__attrs_support


.. feat_arc_sta:: Support feature static view
   :id: feat_arc_sta__attrs_support
   :security: NO
   :safety: QM
   :status: valid
   :includes: logic_arc_int__attrs_support, logic_arc_int_op__attrs_support
   :belongs_to: feat__attrs_support


.. feat_arc_dyn:: Support feature dynamic view
   :id: feat_arc_dyn__attrs_support
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: feat__attrs_support


..
   Invalid ``status`` value for every directive that declares it,
   i.e. all requirement types, all architecture types and all safety-analysis types.


.. feat_req:: Invalid status
   :id: feat_req__attrs__bad_status
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: draft
   :valid_from: v1.0
   :satisfied_by: feat__attrs_support
   :expect: status (draft): does not follow pattern
   :expect_not: security (NO): does not follow pattern

   Negative `status` test for feat_req.


.. comp_req:: Invalid status
   :id: comp_req__attrs__bad_status
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: draft
   :satisfied_by: comp__attrs_support
   :expect: status (draft): does not follow pattern
   :expect_not: security (NO): does not follow pattern

   Negative `status` test for comp_req.


.. aou_req:: Invalid status
   :id: aou_req__attrs__bad_status
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: draft
   :expect: status (draft): does not follow pattern
   :expect_not: security (NO): does not follow pattern

   Negative `status` test for aou_req.


.. feat:: Invalid status
   :id: feat__attrs_bad_status
   :version: 1
   :security: NO
   :safety: QM
   :status: draft
   :expect: status (draft): does not follow pattern
   :expect_not: security (NO): does not follow pattern


.. feat_arc_sta:: Invalid status
   :id: feat_arc_sta__attrs__bad_status
   :security: NO
   :safety: QM
   :status: draft
   :includes: logic_arc_int__attrs_support, logic_arc_int_op__attrs_support
   :belongs_to: feat__attrs_support
   :expect: status (draft): does not follow pattern
   :expect_not: security (NO): does not follow pattern


.. feat_arc_dyn:: Invalid status
   :id: feat_arc_dyn__attrs__bad_status
   :security: NO
   :safety: QM
   :status: draft
   :belongs_to: feat__attrs_support
   :expect: status (draft): does not follow pattern
   :expect_not: security (NO): does not follow pattern


.. logic_arc_int:: Invalid status
   :id: logic_arc_int__attrs__bad_status
   :security: NO
   :safety: QM
   :status: draft
   :expect: status (draft): does not follow pattern
   :expect_not: security (NO): does not follow pattern


.. logic_arc_int_op:: Invalid status
   :id: logic_arc_int_op__attrs__bad_status
   :security: NO
   :safety: QM
   :status: draft
   :included_by: logic_arc_int__attrs_support
   :expect: status (draft): does not follow pattern
   :expect_not: security (NO): does not follow pattern


.. comp:: Invalid status
   :id: comp__attrs_bad_status
   :version: 1
   :security: NO
   :safety: QM
   :status: draft
   :belongs_to: feat__attrs_support
   :expect: status (draft): does not follow pattern
   :expect_not: security (NO): does not follow pattern


.. comp_arc_sta:: Invalid status
   :id: comp_arc_sta__attrs__bad_status
   :security: NO
   :safety: QM
   :status: draft
   :belongs_to: comp__attrs_support
   :expect: status (draft): does not follow pattern
   :expect_not: security (NO): does not follow pattern


.. comp_arc_dyn:: Invalid status
   :id: comp_arc_dyn__attrs__bad_status
   :security: NO
   :safety: QM
   :status: draft
   :belongs_to: comp__attrs_support
   :expect: status (draft): does not follow pattern
   :expect_not: security (NO): does not follow pattern


.. real_arc_int:: Invalid status
   :id: real_arc_int__attrs__bad_status
   :security: NO
   :safety: QM
   :status: draft
   :language: cpp
   :expect: status (draft): does not follow pattern
   :expect_not: security (NO): does not follow pattern


.. real_arc_int_op:: Invalid status
   :id: real_arc_int_op__attrs__bad_status
   :security: NO
   :safety: QM
   :status: draft
   :included_by: real_arc_int__attrs_support
   :expect: status (draft): does not follow pattern
   :expect_not: security (NO): does not follow pattern


.. feat_saf_fmea:: Invalid status
   :id: feat_saf_fmea__attrs__bad_status
   :fault_id: FD_NEG
   :failure_effect: Negative `status` test for feat_saf_fmea.
   :sufficient: no
   :status: draft
   :violates: feat_arc_dyn__attrs_support
   :expect: status (draft): does not follow pattern


.. comp_saf_fmea:: Invalid status
   :id: comp_saf_fmea__attrs__bad_status
   :fault_id: FD_NEG
   :failure_effect: Negative `status` test for comp_saf_fmea.
   :sufficient: no
   :status: draft
   :violates: comp_arc_dyn__attrs_support
   :expect: status (draft): does not follow pattern


.. plat_saf_dfa:: Invalid status
   :id: plat_saf_dfa__attrs__bad_status
   :failure_id: FI_NEG
   :failure_effect: Negative `status` test for plat_saf_dfa.
   :sufficient: no
   :status: draft
   :violates: feat_arc_sta__attrs_support
   :expect: status (draft): does not follow pattern


.. feat_saf_dfa:: Invalid status
   :id: feat_saf_dfa__attrs__bad_status
   :failure_id: FI_NEG
   :failure_effect: Negative `status` test for feat_saf_dfa.
   :sufficient: no
   :status: draft
   :violates: feat_arc_sta__attrs_support
   :expect: status (draft): does not follow pattern


.. comp_saf_dfa:: Invalid status
   :id: comp_saf_dfa__attrs__bad_status
   :failure_id: FI_NEG
   :failure_effect: Negative `status` test for comp_saf_dfa.
   :sufficient: no
   :status: draft
   :violates: comp_arc_sta__attrs_support
   :expect: status (draft): does not follow pattern


..
   Missing ``status`` value for all requirement types.


.. feat_req:: Missing status
   :id: feat_req__attrs__missing_status
   :reqtype: Functional
   :security: NO
   :safety: QM
   :valid_from: v1.0
   :satisfied_by: feat__attrs_support
   :expect: is missing required attribute: `status`

   Missing `status` test for feat_req.


.. comp_req:: Missing status
   :id: comp_req__attrs__missing_status
   :reqtype: Functional
   :security: NO
   :safety: QM
   :satisfied_by: comp__attrs_support
   :expect: is missing required attribute: `status`

   Missing `status` test for comp_req.


.. aou_req:: Missing status
   :id: aou_req__attrs__missing_status
   :reqtype: Functional
   :security: NO
   :safety: QM
   :expect: is missing required attribute: `status`

   Missing `status` test for aou_req.


..
   Invalid ``security`` value for every directive that declares it,
   i.e. all requirement types and all architecture types.


.. feat_req:: Invalid security
   :id: feat_req__attrs__bad_security
   :reqtype: Functional
   :security: MAYBE
   :safety: QM
   :status: valid
   :valid_from: v1.0
   :satisfied_by: feat__attrs_support
   :expect: security (MAYBE): does not follow pattern
   :expect_not: status (valid): does not follow pattern

   Negative `security` test for feat_req.


.. comp_req:: Invalid security
   :id: comp_req__attrs__bad_security
   :reqtype: Functional
   :security: MAYBE
   :safety: QM
   :status: valid
   :satisfied_by: comp__attrs_support
   :expect: security (MAYBE): does not follow pattern
   :expect_not: status (valid): does not follow pattern

   Negative `security` test for comp_req.


.. aou_req:: Invalid security
   :id: aou_req__attrs__bad_security
   :reqtype: Functional
   :security: MAYBE
   :safety: QM
   :status: valid
   :expect: security (MAYBE): does not follow pattern
   :expect_not: status (valid): does not follow pattern

   Negative `security` test for aou_req.


.. feat:: Invalid security
   :id: feat__attrs_bad_security
   :version: 1
   :security: MAYBE
   :safety: QM
   :status: valid
   :expect: security (MAYBE): does not follow pattern
   :expect_not: status (valid): does not follow pattern


.. feat_arc_sta:: Invalid security
   :id: feat_arc_sta__attrs__bad_security
   :security: MAYBE
   :safety: QM
   :status: valid
   :includes: logic_arc_int__attrs_support, logic_arc_int_op__attrs_support
   :belongs_to: feat__attrs_support
   :expect: security (MAYBE): does not follow pattern
   :expect_not: status (valid): does not follow pattern


.. feat_arc_dyn:: Invalid security
   :id: feat_arc_dyn__attrs__bad_security
   :security: MAYBE
   :safety: QM
   :status: valid
   :belongs_to: feat__attrs_support
   :expect: security (MAYBE): does not follow pattern
   :expect_not: status (valid): does not follow pattern


.. logic_arc_int:: Invalid security
   :id: logic_arc_int__attrs__bad_security
   :security: MAYBE
   :safety: QM
   :status: valid
   :expect: security (MAYBE): does not follow pattern
   :expect_not: status (valid): does not follow pattern


.. logic_arc_int_op:: Invalid security
   :id: logic_arc_int_op__attrs__bad_security
   :security: MAYBE
   :safety: QM
   :status: valid
   :included_by: logic_arc_int__attrs_support
   :expect: security (MAYBE): does not follow pattern
   :expect_not: status (valid): does not follow pattern


.. comp:: Invalid security
   :id: comp__attrs_bad_security
   :version: 1
   :security: MAYBE
   :safety: QM
   :status: valid
   :belongs_to: feat__attrs_support
   :expect: security (MAYBE): does not follow pattern
   :expect_not: status (valid): does not follow pattern


.. comp_arc_sta:: Invalid security
   :id: comp_arc_sta__attrs__bad_security
   :security: MAYBE
   :safety: QM
   :status: valid
   :belongs_to: comp__attrs_support
   :expect: security (MAYBE): does not follow pattern
   :expect_not: status (valid): does not follow pattern


.. comp_arc_dyn:: Invalid security
   :id: comp_arc_dyn__attrs__bad_security
   :security: MAYBE
   :safety: QM
   :status: valid
   :belongs_to: comp__attrs_support
   :expect: security (MAYBE): does not follow pattern
   :expect_not: status (valid): does not follow pattern


.. real_arc_int:: Invalid security
   :id: real_arc_int__attrs__bad_security
   :security: MAYBE
   :safety: QM
   :status: valid
   :language: cpp
   :expect: security (MAYBE): does not follow pattern
   :expect_not: status (valid): does not follow pattern


.. real_arc_int_op:: Invalid security
   :id: real_arc_int_op__attrs__bad_security
   :security: MAYBE
   :safety: QM
   :status: valid
   :included_by: real_arc_int__attrs_support
   :expect: security (MAYBE): does not follow pattern
   :expect_not: status (valid): does not follow pattern


..
   Missing ``security`` value for all requirement types.


.. feat_req:: Missing security
   :id: feat_req__attrs__missing_security
   :reqtype: Functional
   :safety: QM
   :status: valid
   :valid_from: v1.0
   :satisfied_by: feat__attrs_support
   :expect: is missing required attribute: `security`

   Missing `security` test for feat_req.


.. comp_req:: Missing security
   :id: comp_req__attrs__missing_security
   :reqtype: Functional
   :safety: QM
   :status: valid
   :satisfied_by: comp__attrs_support
   :expect: is missing required attribute: `security`

   Missing `security` test for comp_req.


.. aou_req:: Missing security
   :id: aou_req__attrs__missing_security
   :reqtype: Functional
   :safety: QM
   :status: valid
   :expect: is missing required attribute: `security`

   Missing `security` test for aou_req.
