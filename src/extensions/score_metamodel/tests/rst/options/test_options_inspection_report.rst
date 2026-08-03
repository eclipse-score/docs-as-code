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

.. mod:: Inspection Report Module
   :id: mod__inspection_report_module
   :security: YES
   :safety: ASIL_B
   :status: valid

.. comp_req:: Inspection Report Requirement
   :id: comp_req__inspection_report__sample
   :reqtype: Functional
   :security: YES
   :safety: ASIL_B
   :status: valid

.. mod_insp:: Inspection Report Record
   :id: mod_insp__inspection_report__requirements
   :safety: ASIL_B
   :security: YES
   :status: valid
   :inspection_type: requirements
   :inspection_state: approved
   :checklist_ref: gd_chklst__req_inspection
   :reviewers: reviewer_a
   :belongs_to: mod__inspection_report_module
   :inspects: comp_req__inspection_report__sample

#EXPECT-NOT[+2]: Inspection report is missing approved inspection(s)

.. mod_insp_report:: Inspection Report Valid
   :id: mod_ispr__inspection_report__valid
   :safety: ASIL_B
   :security: YES
   :status: valid
   :expected_inspections: requirements
   :belongs_to: mod__inspection_report_module
   :contains: mod_insp__inspection_report__requirements

# Invalid expected_inspections value
#EXPECT[+2]: mod_ispr__inspection_report__invalid.expected_inspections (requirements,security): does not follow pattern

.. mod_insp_report:: Inspection Report Invalid Expected Inspections
   :id: mod_ispr__inspection_report__invalid
   :safety: ASIL_B
   :security: YES
   :status: invalid
   :expected_inspections: requirements,security
   :belongs_to: mod__inspection_report_module
   :contains: mod_insp__inspection_report__requirements
