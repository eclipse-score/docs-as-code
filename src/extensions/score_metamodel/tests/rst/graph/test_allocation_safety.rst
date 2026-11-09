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

Safety requirement allocation
=============================

.. test_metadata::
   :id: test_metadata__allocation_safety
   :fully_verifies_list: tool_req__docs_arch_link_safety_to_req[version==3], tool_req__docs_arch_link_qm_to_safety_req[version==3]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Verifies safety compatibility and allocation completeness independently.
   QM requirements may be allocated to QM or ASIL_B features and components;
   ASIL_B requirements must not be allocated to QM elements. Safety elements
   need at least one safety requirement, while mixed allocations are accepted.
   Features and components use incoming satisfied_by allocations for completeness;
   views and interfaces use fulfils. Optional component AoU links do not replace
   requirement allocations. Compatibility violations are warnings; missing
   safety requirements are informational diagnostics.

Feature allocations via satisfied_by
------------------------------------

.. feat:: QM feat without requirements
   :id: feat__safety_alloc__feat_qm_none
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: must have at least one safety requirement allocated via satisfied_by., No linked need in `fulfils`
   :expect_not: must have at least one safety requirement allocated via satisfied_by.

.. feat:: QM feat with QM requirements
   :id: feat__safety_alloc__feat_qm_qm
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: must have at least one safety requirement allocated via satisfied_by., No linked need in `fulfils`
   :expect_not: must have at least one safety requirement allocated via satisfied_by.

.. feat_req:: QM requirement allocated to QM feat
   :id: feat_req__safety_alloc__feat_qm_qm_qm
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional
   :valid_from: v1.0
   :satisfied_by: feat__safety_alloc__feat_qm_qm
   :expect_info_not: A safety requirement cannot be allocated to a QM architecture element.

   Requirement description.

.. feat:: QM feat with safety requirements
   :id: feat__safety_alloc__feat_qm_asil
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: must have at least one safety requirement allocated via satisfied_by., No linked need in `fulfils`
   :expect_not: must have at least one safety requirement allocated via satisfied_by.

.. feat_req:: ASIL_B requirement allocated to QM feat
   :id: feat_req__safety_alloc__feat_qm_asil_asil_b
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional
   :valid_from: v1.0
   :satisfied_by: feat__safety_alloc__feat_qm_asil
   :expect_info: A safety requirement cannot be allocated to a QM architecture element.

   Requirement description.

.. feat:: QM feat with mixed requirements
   :id: feat__safety_alloc__feat_qm_mixed
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: must have at least one safety requirement allocated via satisfied_by., No linked need in `fulfils`
   :expect_not: must have at least one safety requirement allocated via satisfied_by.

.. feat_req:: QM requirement allocated to QM feat
   :id: feat_req__safety_alloc__feat_qm_mixed_qm
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional
   :valid_from: v1.0
   :satisfied_by: feat__safety_alloc__feat_qm_mixed
   :expect_info_not: A safety requirement cannot be allocated to a QM architecture element.

   Requirement description.

.. feat_req:: ASIL_B requirement allocated to QM feat
   :id: feat_req__safety_alloc__feat_qm_mixed_asil_b
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional
   :valid_from: v1.0
   :satisfied_by: feat__safety_alloc__feat_qm_mixed
   :expect_info: A safety requirement cannot be allocated to a QM architecture element.

   Requirement description.

.. feat:: ASIL_B feat without requirements
   :id: feat__safety_alloc__feat_asil_b_none
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :expect_info: must have at least one safety requirement allocated via satisfied_by.
   :expect_not: must have at least one safety requirement allocated via satisfied_by.
   :expect_info_not: No linked need in `fulfils`

.. feat:: ASIL_B feat with QM requirements
   :id: feat__safety_alloc__feat_asil_b_qm
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :expect_info: must have at least one safety requirement allocated via satisfied_by.
   :expect_not: must have at least one safety requirement allocated via satisfied_by.
   :expect_info_not: No linked need in `fulfils`

.. feat_req:: QM requirement allocated to ASIL_B feat
   :id: feat_req__safety_alloc__feat_asil_b_qm_qm
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional
   :valid_from: v1.0
   :satisfied_by: feat__safety_alloc__feat_asil_b_qm
   :expect_info_not: A safety requirement cannot be allocated to a QM architecture element.

   Requirement description.

.. feat:: ASIL_B feat with safety requirements
   :id: feat__safety_alloc__feat_asil_b_asil
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: must have at least one safety requirement allocated via satisfied_by., No linked need in `fulfils`
   :expect_not: must have at least one safety requirement allocated via satisfied_by.

.. feat_req:: ASIL_B requirement allocated to ASIL_B feat
   :id: feat_req__safety_alloc__feat_asil_b_asil_asil_b
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional
   :valid_from: v1.0
   :satisfied_by: feat__safety_alloc__feat_asil_b_asil
   :expect_info_not: A safety requirement cannot be allocated to a QM architecture element.

   Requirement description.

.. feat:: ASIL_B feat with mixed requirements
   :id: feat__safety_alloc__feat_asil_b_mixed
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: must have at least one safety requirement allocated via satisfied_by., No linked need in `fulfils`
   :expect_not: must have at least one safety requirement allocated via satisfied_by.

.. feat_req:: QM requirement allocated to ASIL_B feat
   :id: feat_req__safety_alloc__feat_asil_b_mixed_qm
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional
   :valid_from: v1.0
   :satisfied_by: feat__safety_alloc__feat_asil_b_mixed
   :expect_info_not: A safety requirement cannot be allocated to a QM architecture element.

   Requirement description.

.. feat_req:: ASIL_B requirement allocated to ASIL_B feat
   :id: feat_req__safety_alloc__feat_asil_b_mixed_asil_b
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional
   :valid_from: v1.0
   :satisfied_by: feat__safety_alloc__feat_asil_b_mixed
   :expect_info_not: A safety requirement cannot be allocated to a QM architecture element.

   Requirement description.

Component allocations via satisfied_by
--------------------------------------

.. comp:: QM comp without requirements
   :id: comp__safety_alloc__comp_qm_none
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: must have at least one safety requirement allocated via satisfied_by., No linked need in `fulfils`
   :expect_not: must have at least one safety requirement allocated via satisfied_by.

.. comp:: QM comp with QM requirements
   :id: comp__safety_alloc__comp_qm_qm
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: must have at least one safety requirement allocated via satisfied_by., No linked need in `fulfils`
   :expect_not: must have at least one safety requirement allocated via satisfied_by.

.. comp_req:: QM requirement allocated to QM comp
   :id: comp_req__safety_alloc__comp_qm_qm_qm
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional
   :satisfied_by: comp__safety_alloc__comp_qm_qm
   :expect_info_not: A safety requirement cannot be allocated to a QM architecture element.

   Requirement description.

.. comp:: QM comp with safety requirements
   :id: comp__safety_alloc__comp_qm_asil
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: must have at least one safety requirement allocated via satisfied_by., No linked need in `fulfils`
   :expect_not: must have at least one safety requirement allocated via satisfied_by.

.. comp_req:: ASIL_B requirement allocated to QM comp
   :id: comp_req__safety_alloc__comp_qm_asil_asil_b
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional
   :satisfied_by: comp__safety_alloc__comp_qm_asil
   :expect_info: A safety requirement cannot be allocated to a QM architecture element.

   Requirement description.

.. comp:: QM comp with mixed requirements
   :id: comp__safety_alloc__comp_qm_mixed
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: must have at least one safety requirement allocated via satisfied_by., No linked need in `fulfils`
   :expect_not: must have at least one safety requirement allocated via satisfied_by.

.. comp_req:: QM requirement allocated to QM comp
   :id: comp_req__safety_alloc__comp_qm_mixed_qm
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional
   :satisfied_by: comp__safety_alloc__comp_qm_mixed
   :expect_info_not: A safety requirement cannot be allocated to a QM architecture element.

   Requirement description.

.. comp_req:: ASIL_B requirement allocated to QM comp
   :id: comp_req__safety_alloc__comp_qm_mixed_asil_b
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional
   :satisfied_by: comp__safety_alloc__comp_qm_mixed
   :expect_info: A safety requirement cannot be allocated to a QM architecture element.

   Requirement description.

.. comp:: ASIL_B comp without requirements
   :id: comp__safety_alloc__comp_asil_b_none
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :expect_info: must have at least one safety requirement allocated via satisfied_by.
   :expect_not: must have at least one safety requirement allocated via satisfied_by.
   :expect_info_not: No linked need in `fulfils`

.. comp:: ASIL_B comp with QM requirements
   :id: comp__safety_alloc__comp_asil_b_qm
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :expect_info: must have at least one safety requirement allocated via satisfied_by.
   :expect_not: must have at least one safety requirement allocated via satisfied_by.
   :expect_info_not: No linked need in `fulfils`

.. comp_req:: QM requirement allocated to ASIL_B comp
   :id: comp_req__safety_alloc__comp_asil_b_qm_qm
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional
   :satisfied_by: comp__safety_alloc__comp_asil_b_qm
   :expect_info_not: A safety requirement cannot be allocated to a QM architecture element.

   Requirement description.

.. comp:: ASIL_B comp with safety requirements
   :id: comp__safety_alloc__comp_asil_b_asil
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: must have at least one safety requirement allocated via satisfied_by., No linked need in `fulfils`
   :expect_not: must have at least one safety requirement allocated via satisfied_by.

.. comp_req:: ASIL_B requirement allocated to ASIL_B comp
   :id: comp_req__safety_alloc__comp_asil_b_asil_asil_b
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional
   :satisfied_by: comp__safety_alloc__comp_asil_b_asil
   :expect_info_not: A safety requirement cannot be allocated to a QM architecture element.

   Requirement description.

.. comp:: ASIL_B comp with mixed requirements
   :id: comp__safety_alloc__comp_asil_b_mixed
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: must have at least one safety requirement allocated via satisfied_by., No linked need in `fulfils`
   :expect_not: must have at least one safety requirement allocated via satisfied_by.

.. comp_req:: QM requirement allocated to ASIL_B comp
   :id: comp_req__safety_alloc__comp_asil_b_mixed_qm
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional
   :satisfied_by: comp__safety_alloc__comp_asil_b_mixed
   :expect_info_not: A safety requirement cannot be allocated to a QM architecture element.

   Requirement description.

.. comp_req:: ASIL_B requirement allocated to ASIL_B comp
   :id: comp_req__safety_alloc__comp_asil_b_mixed_asil_b
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional
   :satisfied_by: comp__safety_alloc__comp_asil_b_mixed
   :expect_info_not: A safety requirement cannot be allocated to a QM architecture element.

   Requirement description.

Optional fulfils links
----------------------

.. feat_req:: QM fulfils target
   :id: feat_req__safety_alloc__fulfils_qm
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional
   :valid_from: v1.0

   Requirement description.

.. feat_req:: ASIL_B fulfils target
   :id: feat_req__safety_alloc__fulfils_asil_b
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional
   :valid_from: v1.0

   Requirement description.

.. comp_req:: QM fulfils target
   :id: comp_req__safety_alloc__fulfils_qm
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional

   Requirement description.

.. comp_req:: ASIL_B fulfils target
   :id: comp_req__safety_alloc__fulfils_asil_b
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional

   Requirement description.

.. aou_req:: QM fulfils target
   :id: aou_req__safety_alloc__fulfils_qm
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional

   Requirement description.

.. aou_req:: ASIL_B fulfils target
   :id: aou_req__safety_alloc__fulfils_asil_b
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional

   Requirement description.

.. feat_arc_sta:: QM feat_arc_sta without fulfils targets
   :id: feat_arc_sta__safety_alloc__fulfils_feat_arc_sta_qm_none
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: A QM architecture element cannot fulfil safety requirements., must be linked to at least one safety requirement via fulfils.

.. feat_arc_sta:: QM feat_arc_sta with QM fulfils targets
   :id: feat_arc_sta__safety_alloc__fulfils_feat_arc_sta_qm_qm
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: A QM architecture element cannot fulfil safety requirements., must be linked to at least one safety requirement via fulfils.
   :fulfils: feat_req__safety_alloc__fulfils_qm

.. feat_arc_sta:: QM feat_arc_sta with safety fulfils targets
   :id: feat_arc_sta__safety_alloc__fulfils_feat_arc_sta_qm_asil
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :expect_info: A QM architecture element cannot fulfil safety requirements.
   :expect_info_not: must be linked to at least one safety requirement via fulfils.
   :fulfils: feat_req__safety_alloc__fulfils_asil_b

.. feat_arc_sta:: QM feat_arc_sta with mixed fulfils targets
   :id: feat_arc_sta__safety_alloc__fulfils_feat_arc_sta_qm_mixed
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :expect_info: A QM architecture element cannot fulfil safety requirements.
   :expect_info_not: must be linked to at least one safety requirement via fulfils.
   :fulfils: feat_req__safety_alloc__fulfils_qm, feat_req__safety_alloc__fulfils_asil_b

.. feat_arc_sta:: ASIL_B feat_arc_sta without fulfils targets
   :id: feat_arc_sta__safety_alloc__fulfils_feat_arc_sta_asil_b_none
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: A QM architecture element cannot fulfil safety requirements.
   :expect_info: must be linked to at least one safety requirement via fulfils.

.. feat_arc_sta:: ASIL_B feat_arc_sta with QM fulfils targets
   :id: feat_arc_sta__safety_alloc__fulfils_feat_arc_sta_asil_b_qm
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: A QM architecture element cannot fulfil safety requirements.
   :expect_info: must be linked to at least one safety requirement via fulfils.
   :fulfils: feat_req__safety_alloc__fulfils_qm

.. feat_arc_sta:: ASIL_B feat_arc_sta with safety fulfils targets
   :id: feat_arc_sta__safety_alloc__fulfils_feat_arc_sta_asil_b_asil
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: A QM architecture element cannot fulfil safety requirements., must be linked to at least one safety requirement via fulfils.
   :fulfils: feat_req__safety_alloc__fulfils_asil_b

.. feat_arc_sta:: ASIL_B feat_arc_sta with mixed fulfils targets
   :id: feat_arc_sta__safety_alloc__fulfils_feat_arc_sta_asil_b_mixed
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: A QM architecture element cannot fulfil safety requirements., must be linked to at least one safety requirement via fulfils.
   :fulfils: feat_req__safety_alloc__fulfils_qm, feat_req__safety_alloc__fulfils_asil_b

.. comp:: QM comp without fulfils targets
   :id: comp__safety_alloc__fulfils_comp_qm_none
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: A QM architecture element cannot fulfil safety requirements., No linked need in `fulfils`

.. comp:: QM comp with QM fulfils targets
   :id: comp__safety_alloc__fulfils_comp_qm_qm
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: A QM architecture element cannot fulfil safety requirements., No linked need in `fulfils`
   :fulfils: aou_req__safety_alloc__fulfils_qm

.. comp:: QM comp with safety fulfils targets
   :id: comp__safety_alloc__fulfils_comp_qm_asil
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :expect_info: A QM architecture element cannot fulfil safety requirements.
   :expect_info_not: No linked need in `fulfils`
   :fulfils: aou_req__safety_alloc__fulfils_asil_b

.. comp:: QM comp with mixed fulfils targets
   :id: comp__safety_alloc__fulfils_comp_qm_mixed
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :expect_info: A QM architecture element cannot fulfil safety requirements.
   :expect_info_not: No linked need in `fulfils`
   :fulfils: aou_req__safety_alloc__fulfils_qm, aou_req__safety_alloc__fulfils_asil_b

.. comp:: ASIL_B comp without fulfils targets
   :id: comp__safety_alloc__fulfils_comp_asil_b_none
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: A QM architecture element cannot fulfil safety requirements., No linked need in `fulfils`
   :expect_info: must have at least one safety requirement allocated via satisfied_by.

.. comp:: ASIL_B comp with QM fulfils targets
   :id: comp__safety_alloc__fulfils_comp_asil_b_qm
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: A QM architecture element cannot fulfil safety requirements., No linked need in `fulfils`
   :expect_info: must have at least one safety requirement allocated via satisfied_by.
   :fulfils: aou_req__safety_alloc__fulfils_qm

.. comp:: ASIL_B comp with safety fulfils targets
   :id: comp__safety_alloc__fulfils_comp_asil_b_asil
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: A QM architecture element cannot fulfil safety requirements., No linked need in `fulfils`
   :expect_info: must have at least one safety requirement allocated via satisfied_by.
   :fulfils: aou_req__safety_alloc__fulfils_asil_b

.. comp:: ASIL_B comp with mixed fulfils targets
   :id: comp__safety_alloc__fulfils_comp_asil_b_mixed
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: A QM architecture element cannot fulfil safety requirements., No linked need in `fulfils`
   :expect_info: must have at least one safety requirement allocated via satisfied_by.
   :fulfils: aou_req__safety_alloc__fulfils_qm, aou_req__safety_alloc__fulfils_asil_b

.. feat_arc_dyn:: QM feat_arc_dyn cannot fulfil a safety requirement
   :id: feat_arc_dyn__safety_alloc__fulfils_feat_arc_dyn_unsafe
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :fulfils: feat_req__safety_alloc__fulfils_asil_b
   :expect_info: A QM architecture element cannot fulfil safety requirements.

.. logic_arc_int:: QM logic_arc_int cannot fulfil a safety requirement
   :id: logic_arc_int__safety_alloc__fulfils_logic_arc_int_unsafe
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :fulfils: feat_req__safety_alloc__fulfils_asil_b
   :expect_info: A QM architecture element cannot fulfil safety requirements.

.. comp_arc_sta:: QM comp_arc_sta cannot fulfil a safety requirement
   :id: comp_arc_sta__safety_alloc__fulfils_comp_arc_sta_unsafe
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :fulfils: comp_req__safety_alloc__fulfils_asil_b
   :expect_info: A QM architecture element cannot fulfil safety requirements.

.. comp_arc_dyn:: QM comp_arc_dyn cannot fulfil a safety requirement
   :id: comp_arc_dyn__safety_alloc__fulfils_comp_arc_dyn_unsafe
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :fulfils: comp_req__safety_alloc__fulfils_asil_b
   :expect_info: A QM architecture element cannot fulfil safety requirements.

.. real_arc_int:: QM real_arc_int cannot fulfil a safety requirement
   :id: real_arc_int__safety_alloc__fulfils_real_arc_int_unsafe
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :fulfils: comp_req__safety_alloc__fulfils_asil_b
   :expect_info: A QM architecture element cannot fulfil safety requirements.

Completeness of other views and interfaces
------------------------------------------

.. feat_arc_dyn:: QM feat_arc_dyn with qm requirements
   :id: feat_arc_dyn__safety_alloc__completeness_qm_qm
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :fulfils: feat_req__safety_alloc__fulfils_qm
   :expect_info_not: A QM architecture element cannot fulfil safety requirements., must be linked to at least one safety requirement via fulfils.

.. feat_arc_dyn:: ASIL_B feat_arc_dyn with none requirements
   :id: feat_arc_dyn__safety_alloc__completeness_asil_b_none
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: A QM architecture element cannot fulfil safety requirements.
   :expect_info: must be linked to at least one safety requirement via fulfils.

.. feat_arc_dyn:: ASIL_B feat_arc_dyn with qm requirements
   :id: feat_arc_dyn__safety_alloc__completeness_asil_b_qm
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :fulfils: feat_req__safety_alloc__fulfils_qm
   :expect_info_not: A QM architecture element cannot fulfil safety requirements.
   :expect_info: must be linked to at least one safety requirement via fulfils.

.. feat_arc_dyn:: ASIL_B feat_arc_dyn with mixed requirements
   :id: feat_arc_dyn__safety_alloc__completeness_asil_b_mixed
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :fulfils: feat_req__safety_alloc__fulfils_qm, feat_req__safety_alloc__fulfils_asil_b
   :expect_info_not: A QM architecture element cannot fulfil safety requirements., must be linked to at least one safety requirement via fulfils.

.. logic_arc_int:: QM logic_arc_int with qm requirements
   :id: logic_arc_int__safety_alloc__completeness_qm_qm
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :fulfils: feat_req__safety_alloc__fulfils_qm
   :expect_info_not: A QM architecture element cannot fulfil safety requirements., must be linked to at least one safety requirement via fulfils.

.. logic_arc_int:: ASIL_B logic_arc_int with none requirements
   :id: logic_arc_int__safety_alloc__completeness_asil_b_none
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: A QM architecture element cannot fulfil safety requirements.
   :expect_info: must be linked to at least one safety requirement via fulfils.

.. logic_arc_int:: ASIL_B logic_arc_int with qm requirements
   :id: logic_arc_int__safety_alloc__completeness_asil_b_qm
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :fulfils: feat_req__safety_alloc__fulfils_qm
   :expect_info_not: A QM architecture element cannot fulfil safety requirements.
   :expect_info: must be linked to at least one safety requirement via fulfils.

.. logic_arc_int:: ASIL_B logic_arc_int with mixed requirements
   :id: logic_arc_int__safety_alloc__completeness_asil_b_mixed
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :fulfils: feat_req__safety_alloc__fulfils_qm, feat_req__safety_alloc__fulfils_asil_b
   :expect_info_not: A QM architecture element cannot fulfil safety requirements., must be linked to at least one safety requirement via fulfils.

.. comp_arc_sta:: QM comp_arc_sta with qm requirements
   :id: comp_arc_sta__safety_alloc__completeness_qm_qm
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :fulfils: comp_req__safety_alloc__fulfils_qm
   :expect_info_not: A QM architecture element cannot fulfil safety requirements., must be linked to at least one safety requirement via fulfils.

.. comp_arc_sta:: ASIL_B comp_arc_sta with none requirements
   :id: comp_arc_sta__safety_alloc__completeness_asil_b_none
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: A QM architecture element cannot fulfil safety requirements.
   :expect_info: must be linked to at least one safety requirement via fulfils.

.. comp_arc_sta:: ASIL_B comp_arc_sta with qm requirements
   :id: comp_arc_sta__safety_alloc__completeness_asil_b_qm
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :fulfils: comp_req__safety_alloc__fulfils_qm
   :expect_info_not: A QM architecture element cannot fulfil safety requirements.
   :expect_info: must be linked to at least one safety requirement via fulfils.

.. comp_arc_sta:: ASIL_B comp_arc_sta with mixed requirements
   :id: comp_arc_sta__safety_alloc__completeness_asil_b_mixed
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :fulfils: comp_req__safety_alloc__fulfils_qm, comp_req__safety_alloc__fulfils_asil_b
   :expect_info_not: A QM architecture element cannot fulfil safety requirements., must be linked to at least one safety requirement via fulfils.

.. comp_arc_dyn:: QM comp_arc_dyn with qm requirements
   :id: comp_arc_dyn__safety_alloc__completeness_qm_qm
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :fulfils: comp_req__safety_alloc__fulfils_qm
   :expect_info_not: A QM architecture element cannot fulfil safety requirements., must be linked to at least one safety requirement via fulfils.

.. comp_arc_dyn:: ASIL_B comp_arc_dyn with none requirements
   :id: comp_arc_dyn__safety_alloc__completeness_asil_b_none
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :expect_info_not: A QM architecture element cannot fulfil safety requirements.
   :expect_info: must be linked to at least one safety requirement via fulfils.

.. comp_arc_dyn:: ASIL_B comp_arc_dyn with qm requirements
   :id: comp_arc_dyn__safety_alloc__completeness_asil_b_qm
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :fulfils: comp_req__safety_alloc__fulfils_qm
   :expect_info_not: A QM architecture element cannot fulfil safety requirements.
   :expect_info: must be linked to at least one safety requirement via fulfils.

.. comp_arc_dyn:: ASIL_B comp_arc_dyn with mixed requirements
   :id: comp_arc_dyn__safety_alloc__completeness_asil_b_mixed
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :fulfils: comp_req__safety_alloc__fulfils_qm, comp_req__safety_alloc__fulfils_asil_b
   :expect_info_not: A QM architecture element cannot fulfil safety requirements., must be linked to at least one safety requirement via fulfils.

.. real_arc_int:: QM real_arc_int with qm requirements
   :id: real_arc_int__safety_alloc__completeness_qm_qm
   :safety: QM
   :security: NO
   :status: valid
   :version: 1
   :language: cpp
   :fulfils: comp_req__safety_alloc__fulfils_qm
   :expect_info_not: A QM architecture element cannot fulfil safety requirements., must be linked to at least one safety requirement via fulfils.

.. real_arc_int:: ASIL_B real_arc_int with none requirements
   :id: real_arc_int__safety_alloc__completeness_asil_b_none
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :language: cpp
   :expect_info_not: A QM architecture element cannot fulfil safety requirements.
   :expect_info: must be linked to at least one safety requirement via fulfils.

.. real_arc_int:: ASIL_B real_arc_int with qm requirements
   :id: real_arc_int__safety_alloc__completeness_asil_b_qm
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :language: cpp
   :fulfils: comp_req__safety_alloc__fulfils_qm
   :expect_info_not: A QM architecture element cannot fulfil safety requirements.
   :expect_info: must be linked to at least one safety requirement via fulfils.

.. real_arc_int:: ASIL_B real_arc_int with mixed requirements
   :id: real_arc_int__safety_alloc__completeness_asil_b_mixed
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :language: cpp
   :fulfils: comp_req__safety_alloc__fulfils_qm, comp_req__safety_alloc__fulfils_asil_b
   :expect_info_not: A QM architecture element cannot fulfil safety requirements., must be linked to at least one safety requirement via fulfils.

Safety requirements allocated to multiple elements
--------------------------------------------------

An ASIL_B requirement must reject every QM allocation target, even when another
allocation target is ASIL_B.

.. feat_req:: Safety requirement allocated to both QM and ASIL_B feat
   :id: feat_req__safety_alloc__multiple_feat_targets
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional
   :valid_from: v1.0
   :satisfied_by: feat__safety_alloc__feat_asil_b_asil, feat__safety_alloc__feat_qm_asil
   :expect_not: A safety requirement cannot be allocated to a QM architecture element.
   :expect_info: Parent need `feat__safety_alloc__feat_qm_asil` does not fulfill condition `safety != QM`.

   Every allocated element must support the requirement's safety classification.

.. comp_req:: Safety requirement allocated to both QM and ASIL_B comp
   :id: comp_req__safety_alloc__multiple_comp_targets
   :safety: ASIL_B
   :security: NO
   :status: valid
   :version: 1
   :reqtype: Functional
   :satisfied_by: comp__safety_alloc__comp_asil_b_asil, comp__safety_alloc__comp_qm_asil
   :expect_not: A safety requirement cannot be allocated to a QM architecture element.
   :expect_info: Parent need `comp__safety_alloc__comp_qm_asil` does not fulfill condition `safety != QM`.

   Every allocated element must support the requirement's safety classification.
