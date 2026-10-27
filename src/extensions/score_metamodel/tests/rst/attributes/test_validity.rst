..
   # *******************************************************************************
   # Copyright (c) 2025 Contributors to the Eclipse Foundation
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


.. test_metadata:: Validity attribute checks
   :id: test_metadata__validity_checks
   :fully_verifies_list: tool_req__docs_req_attr_validity_correctness, tool_req__docs_req_attr_validity_consistency
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Checks milestone formatting for validity attributes and the ordering of
   valid_from before valid_until.


.. stkh_req:: Valid major and minor milestones
   :id: stkh_req__validity__aaaa
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :rationale: valid milestone values
   :valid_from: v1.0
   :valid_until: v2.0
   :expect_not: does not follow pattern, inconsistent validity


.. stkh_req:: Valid patch milestone ordering
   :id: stkh_req__validity__aaab
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :rationale: valid patch values
   :valid_from: v1.2.3
   :valid_until: v1.2.4
   :expect_not: does not follow pattern, inconsistent validity


.. stkh_req:: Invalid valid_from format
   :id: stkh_req__validity__aaac
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :rationale: invalid milestone format
   :valid_from: v1
   :valid_until: v0.5
   :expect: valid_from (v1): does not follow pattern
   :expect_not: inconsistent validity


.. stkh_req:: Invalid valid_until format
   :id: stkh_req__validity__aaad
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :rationale: invalid milestone format
   :valid_from: v1.0
   :valid_until: v1.0.0-beta
   :expect: valid_until (v1.0.0-beta): does not follow pattern
   :expect_not: inconsistent validity


.. stkh_req:: valid_from is after valid_until
   :id: stkh_req__validity__aaae
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :rationale: inconsistent validity
   :valid_from: v1.1
   :valid_until: v1.0
   :expect: inconsistent validity: valid_from (v1.1) >= valid_until (v1.0)


.. stkh_req:: valid_from equals valid_until
   :id: stkh_req__validity__aaaf
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :rationale: equal validity bounds are inconsistent
   :valid_from: v1.0.0
   :valid_until: v1.0
   :expect: inconsistent validity: valid_from (v1.0.0) >= valid_until (v1.0)


.. stkh_req:: Missing valid_until is allowed
   :id: stkh_req__validity__aaag
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :rationale: no end of validity period
   :valid_from: v1.0
   :expect_not: inconsistent validity


.. feat:: Validity target feature
   :id: feat__validity_target
   :version: 1
   :status: valid
   :safety: QM
   :security: NO


.. comp:: Validity target component
   :id: comp__validity_target
   :version: 1
   :status: valid
   :safety: QM
   :security: NO
   :belongs_to: feat__validity_target


.. feat_req:: Valid feature requirement milestones
   :id: feat_req__validity__aaaa
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :satisfied_by: feat__validity_target
   :valid_from: v1.0
   :valid_until: v2.0
   :expect_not: does not follow pattern, inconsistent validity

   This feature requirement is used to check the validity attributes.


.. feat_req:: Feature requirement valid_from is after valid_until
   :id: feat_req__validity__aaab
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :satisfied_by: feat__validity_target
   :valid_from: v1.1
   :valid_until: v1.0
   :expect: inconsistent validity: valid_from (v1.1) >= valid_until (v1.0)

   This feature requirement is used to check the validity attributes.


.. feat_req:: Feature requirement with malformed valid_from
   :id: feat_req__validity__aaac
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :satisfied_by: feat__validity_target
   :valid_from: v01.0
   :valid_until: v1.0
   :expect: valid_from (v01.0): does not follow pattern
   :expect_not: inconsistent validity

   This feature requirement is used to check the validity attributes.


.. feat_req:: Feature requirement with malformed valid_until
   :id: feat_req__validity__aaad
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :satisfied_by: feat__validity_target
   :valid_from: v1.0
   :valid_until: v01.0
   :expect: valid_until (v01.0): does not follow pattern
   :expect_not: inconsistent validity

   This feature requirement is used to check the validity attributes.


.. feat_req:: Feature requirement without valid_until
   :id: feat_req__validity__aaae
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :satisfied_by: feat__validity_target
   :valid_from: v1.0
   :expect_not: inconsistent validity

   This feature requirement is used to check the validity attributes.


.. comp_req:: Valid component requirement milestones
   :id: comp_req__attributes__validity_aaaa
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :satisfied_by: comp__validity_target
   :valid_from: v1.0
   :valid_until: v2.0
   :expect_not: does not follow pattern, inconsistent validity

   This component requirement is used to check the validity attributes.


.. comp_req:: Component requirement without validity bounds
   :id: comp_req__attributes__validity_aaae
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :satisfied_by: comp__validity_target
   :expect_not: is missing required attribute: `valid_from`, is missing required attribute: `valid_until`, inconsistent validity

   Component requirements may omit validity bounds.


.. comp_req:: Component requirement with malformed valid_from
   :id: comp_req__attributes__validity_aaab
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :satisfied_by: comp__validity_target
   :valid_from: v01.0
   :valid_until: v2.0
   :expect: valid_from (v01.0): does not follow pattern
   :expect_not: inconsistent validity

   This component requirement checks the valid_from pattern.


.. comp_req:: Component requirement with malformed valid_until
   :id: comp_req__attributes__validity_aaac
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :satisfied_by: comp__validity_target
   :valid_from: v1.0
   :valid_until: v01.0
   :expect: valid_until (v01.0): does not follow pattern
   :expect_not: inconsistent validity

   This component requirement checks the valid_until pattern.


.. comp_req:: Component requirement with inconsistent validity
   :id: comp_req__attributes__validity_aaad
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :satisfied_by: comp__validity_target
   :valid_from: v1.1
   :valid_until: v1.0
   :expect: inconsistent validity: valid_from (v1.1) >= valid_until (v1.0)

   This component requirement checks the validity ordering.
