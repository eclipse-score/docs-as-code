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

.. mod:: Inspection Report Graph Module
   :id: mod__inspection_report_graph_module
   :security: YES
   :safety: ASIL_B
   :status: valid

.. comp_req:: Inspection Report Graph Requirement
   :id: comp_req__inspection_report_graph__sample
   :reqtype: Functional
   :security: YES
   :safety: ASIL_B
   :status: valid

.. mod_insp:: Approved Requirements Inspection
   :id: mod_insp__inspection_report_graph__requirements
   :safety: ASIL_B
   :security: YES
   :status: valid
   :inspection_type: requirements
   :inspection_state: approved
   :checklist_ref: gd_chklst__req_inspection
   :reviewers: reviewer_a
   :belongs_to: mod__inspection_report_graph_module
   :inspects: comp_req__inspection_report_graph__sample

#EXPECT[+2]: Inspection report is missing approved inspection(s) for: architecture

.. mod_insp_report:: Incomplete Inspection Report
   :id: mod_ispr__inspection_report_graph__incomplete
   :safety: ASIL_B
   :security: YES
   :status: valid
   :expected_inspections: requirements,architecture
   :belongs_to: mod__inspection_report_graph_module
   :contains: mod_insp__inspection_report_graph__requirements

#EXPECT-NOT[+2]: Inspection report is missing approved inspection(s)

.. mod_insp_report:: Complete Inspection Report
   :id: mod_ispr__inspection_report_graph__complete
   :safety: ASIL_B
   :security: YES
   :status: valid
   :expected_inspections: requirements
   :belongs_to: mod__inspection_report_graph_module
   :contains: mod_insp__inspection_report_graph__requirements
