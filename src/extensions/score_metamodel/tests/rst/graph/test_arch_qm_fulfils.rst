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
   :id: test_metadata__arch_qm_fulfils
   :partially_verifies_list: tool_req__docs_arch_link_qm_to_safety_req[version==2]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Checks QM logical interfaces against the architecture-to-requirement safety
   rule. Single and multiple QM targets are accepted, while every ASIL_B target
   is rejected, including in mixed lists. ASIL_B sources are exempt, and empty
   fulfils lists remain accepted.


.. feat:: QM fulfilment validation feature
   :id: feat__qm_fulfils
   :security: NO
   :safety: QM
   :status: valid
   :version: 1

   Feature containing the logical interfaces and their requirement targets.


.. feat_req:: First QM requirement
   :id: feat_req__qm_fulfils__qm_one
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :version: 1
   :valid_from: v1.0
   :satisfied_by: feat__qm_fulfils

   A QM requirement target for single and mixed fulfilment lists.


.. feat_req:: Second QM requirement
   :id: feat_req__qm_fulfils__qm_two
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :version: 1
   :valid_from: v1.0
   :satisfied_by: feat__qm_fulfils

   A second QM requirement target for multiple-target fulfilment.


.. feat_req:: First ASIL_B requirement
   :id: feat_req__qm_fulfils__asil_one
   :reqtype: Functional
   :security: NO
   :safety: ASIL_B
   :status: valid
   :version: 1
   :valid_from: v1.0
   :satisfied_by: feat__qm_fulfils

   An ASIL_B requirement target for single and mixed fulfilment lists.


.. feat_req:: Second ASIL_B requirement
   :id: feat_req__qm_fulfils__asil_two
   :reqtype: Functional
   :security: NO
   :safety: ASIL_B
   :status: valid
   :version: 1
   :valid_from: v1.0
   :satisfied_by: feat__qm_fulfils

   A distinct ASIL_B requirement target for mixed fulfilment.


.. logic_arc_int:: QM interface fulfils one QM requirement
   :id: logic_arc_int__qm_fulfils__one_qm
   :security: NO
   :safety: QM
   :status: valid
   :version: 1
   :included_by: feat__qm_fulfils
   :fulfils: feat_req__qm_fulfils__qm_one
   :expect_not: An QM architecture element cannot implement ASIL requirements.

   A QM source may fulfil a QM requirement.


.. logic_arc_int:: QM interface fulfils multiple QM requirements
   :id: logic_arc_int__qm_fulfils__many_qm
   :security: NO
   :safety: QM
   :status: valid
   :version: 1
   :included_by: feat__qm_fulfils
   :fulfils: feat_req__qm_fulfils__qm_one, feat_req__qm_fulfils__qm_two
   :expect_not: An QM architecture element cannot implement ASIL requirements.

   Every target in this fulfilment list is QM.


.. logic_arc_int:: QM interface rejects an ASIL_B requirement
   :id: logic_arc_int__qm_fulfils__one_asil
   :security: NO
   :safety: QM
   :status: valid
   :version: 1
   :included_by: feat__qm_fulfils
   :fulfils: feat_req__qm_fulfils__asil_one
   :expect: Parent need `feat_req__qm_fulfils__asil_one` does not fulfill condition `safety == QM`. Explanation: An QM architecture element cannot implement ASIL requirements.

   A QM source cannot fulfil an ASIL_B requirement.


.. logic_arc_int:: QM interface rejects every ASIL_B target in a mixed list
   :id: logic_arc_int__qm_fulfils__mixed
   :security: NO
   :safety: QM
   :status: valid
   :version: 1
   :included_by: feat__qm_fulfils
   :fulfils: feat_req__qm_fulfils__qm_one, feat_req__qm_fulfils__asil_one, feat_req__qm_fulfils__asil_two
   :expect:
      Parent need `feat_req__qm_fulfils__asil_one` does not fulfill condition `safety == QM`. Explanation: An QM architecture element cannot implement ASIL requirements.,
      Parent need `feat_req__qm_fulfils__asil_two` does not fulfill condition `safety == QM`. Explanation: An QM architecture element cannot implement ASIL requirements.
   :expect_not: Parent need `feat_req__qm_fulfils__qm_one`

   Both ASIL_B targets are rejected without rejecting the QM target.


.. logic_arc_int:: ASIL_B interface is exempt from the QM source rule
   :id: logic_arc_int__qm_fulfils__asil_source
   :security: NO
   :safety: ASIL_B
   :status: valid
   :version: 1
   :included_by: feat__qm_fulfils
   :fulfils: feat_req__qm_fulfils__qm_one, feat_req__qm_fulfils__asil_one
   :expect_not: An QM architecture element cannot implement ASIL requirements.

   An ASIL_B source with QM and ASIL_B targets is not selected by this rule.


.. logic_arc_int:: QM interface without fulfilment targets
   :id: logic_arc_int__qm_fulfils__empty
   :security: NO
   :safety: QM
   :status: valid
   :version: 1
   :included_by: feat__qm_fulfils
   :expect_not: An QM architecture element cannot implement ASIL requirements.

   An empty fulfilment list preserves the existing check_all behavior.
