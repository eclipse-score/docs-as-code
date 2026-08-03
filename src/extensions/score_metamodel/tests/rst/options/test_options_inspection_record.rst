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
#CHECK: check_options


.. Base architecture and requirement objects used by inspection record tests

.. feat:: Inspection Feature
   :id: feat__inspection_feature
   :security: YES
   :safety: ASIL_B
   :status: valid

.. comp:: Inspection Component
   :id: comp__inspection_component
   :security: YES
   :safety: ASIL_B
   :status: valid
   :belongs_to: feat__inspection_feature

.. mod:: Inspection Module
   :id: mod__inspection_module
   :security: YES
   :safety: ASIL_B
   :status: valid
   :includes: comp__inspection_component

.. comp_req:: Inspection Requirement
   :id: comp_req__inspection__sample
   :reqtype: Functional
   :security: YES
   :safety: ASIL_B
   :status: valid

   Requirement text for inspection record tests.


.. Valid machine-readable inspection record need
#EXPECT-NOT[+2]: does not follow pattern

.. mod_insp:: Inspection Record Valid
   :id: mod_insp__inspection__valid
   :safety: ASIL_B
   :security: YES
   :status: valid
   :inspection_type: requirements
   :inspection_state: approved
   :checklist_ref: gd_chklst__req_inspection
   :reviewers: reviewer_a,reviewer_b
   :moderator: moderator_a
   :approver: approver_a
   :belongs_to: mod__inspection_module
   :inspects: comp_req__inspection__sample


.. Invalid inspection_state value in module inspection record
#EXPECT[+2]: mod_insp__inspection__bad_state.inspection_state (approved_late): does not follow pattern

.. mod_insp:: Inspection Record Invalid State
   :id: mod_insp__inspection__bad_state
   :safety: ASIL_B
   :security: YES
   :status: invalid
   :inspection_type: architecture
   :inspection_state: approved_late
   :checklist_ref: gd_chklst__arch_inspection_checklist
   :reviewers: reviewer_a
   :belongs_to: mod__inspection_module
   :inspects: comp_req__inspection__sample
