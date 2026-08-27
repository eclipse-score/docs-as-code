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
   :id: test_metadata__metamodel_graph_mod_ver_report
   :partially_verifies_list: tool_req__docs_verification_report_need
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that a module verification report covers exactly the components of its
   module — drift in either direction is detected, never silently corrected.

--- Setup

.. feat:: Report Scope Feature
   :id: feat__report_scope
   :security: NO
   :safety: QM
   :status: valid

.. comp:: Report Scope Component A
   :id: comp__report_scope_a
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: feat__report_scope

.. comp:: Report Scope Component B
   :id: comp__report_scope_b
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: feat__report_scope

.. comp:: Report Scope Component Outside The Module
   :id: comp__report_scope_outside
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: feat__report_scope

.. mod:: Report Scope Module
   :id: mod__report_scope
   :security: NO
   :safety: QM
   :status: valid
   :includes: comp__report_scope_a, comp__report_scope_b

---

.. Positive test: covers exactly the included components — no warning expected.

.. mod_ver_report:: Complete Report
   :id: mod_vrep__report_scope__complete
   :safety: QM
   :security: NO
   :status: valid
   :verification_method: test
   :belongs_to: mod__report_scope
   :covers: comp__report_scope_a, comp__report_scope_b
   :expect_not: does not cover, which is not included by

.. Negative test: an included component is missing from ':covers:'.

.. mod_ver_report:: Report Missing A Component
   :id: mod_vrep__report_scope__missing
   :safety: QM
   :security: NO
   :status: valid
   :verification_method: test
   :belongs_to: mod__report_scope
   :covers: comp__report_scope_a
   :expect: does not cover 'comp__report_scope_b', which is included by 'mod__report_scope'
   :expect_not: which is not included by

.. Negative test: a covered component is not part of the module.

.. mod_ver_report:: Report Covering Too Much
   :id: mod_vrep__report_scope__extra
   :safety: QM
   :security: NO
   :status: valid
   :verification_method: test
   :belongs_to: mod__report_scope
   :covers: comp__report_scope_a, comp__report_scope_b, comp__report_scope_outside
   :expect: covers 'comp__report_scope_outside', which is not included by 'mod__report_scope'
   :expect_not: does not cover
