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


.. Base architecture and requirement objects used by verification evidence tests

.. feat:: Verification Feature
   :id: feat__verification_feature
   :security: YES
   :safety: ASIL_B
   :status: valid

.. comp:: Verification Component
   :id: comp__verification_component
   :security: YES
   :safety: ASIL_B
   :status: valid
   :belongs_to: feat__verification_feature

.. mod:: Verification Module
   :id: mod__verification_module
   :security: YES
   :safety: ASIL_B
   :status: valid
   :includes: comp__verification_component

.. comp_req:: Verification Requirement
   :id: comp_req__verification__sample
   :reqtype: Functional
   :security: YES
   :safety: ASIL_B
   :status: valid
   :content: Requirement text for verification evidence tests.


.. Valid machine-readable verification report need
#EXPECT-NOT[+2]: does not follow pattern

.. mod_ver_report:: Verification Report Valid
   :id: mod_vrep__verification__valid
   :safety: ASIL_B
   :security: YES
   :status: valid
   :verification_method: test_and_inspection
   :requirements_coverage_percent: 95
   :structural_coverage_percent: 90
   :branch_coverage_percent: 85
   :verdict: pass
   :report_version: 1.0.0
   :release_baseline: main
   :belongs_to: mod__verification_module
   :covers: comp_req__verification__sample


.. Invalid verdict value in module verification report
#EXPECT[+2]: mod_vrep__verification__bad_verdict.verdict (pending): does not follow pattern

.. mod_ver_report:: Verification Report Invalid Verdict
   :id: mod_vrep__verification__bad_verdict
   :safety: ASIL_B
   :security: YES
   :status: invalid
   :verification_method: inspection
   :verdict: pending
   :belongs_to: mod__verification_module


.. Valid machine-readable inspection record need
#EXPECT-NOT[+2]: does not follow pattern

.. mod_insp:: Inspection Record Valid
   :id: mod_insp__verification__valid
   :safety: ASIL_B
   :security: YES
   :status: valid
   :inspection_type: requirements
   :inspection_state: approved
   :checklist_template: gd_chklst__req_inspection
   :reviewers: reviewer_a,reviewer_b
   :checklist_type: req
   :findings_total: 1
   :findings_open: 0
   :inspection_date: 2026-06-24
   :belongs_to: mod__verification_module
   :inspects: comp_req__verification__sample
   :checklist: doc__verification__filled_checklist


.. Invalid inspection_state value in module inspection record
#EXPECT[+2]: mod_insp__verification__bad_state.inspection_state (approved_late): does not follow pattern

.. mod_insp:: Inspection Record Invalid State
   :id: mod_insp__verification__bad_state
   :safety: ASIL_B
   :security: YES
   :status: invalid
   :inspection_type: architecture
   :inspection_state: approved_late
   :checklist_template: gd_chklst__arch_inspection_checklist
   :reviewers: reviewer_a
   :belongs_to: mod__verification_module
   :inspects: comp_req__verification__sample
   :checklist: doc__verification__filled_checklist
