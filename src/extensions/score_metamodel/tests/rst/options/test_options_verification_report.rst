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
   :id: test_metadata__verification_report_need
   :fully_verifies_list: tool_req__docs_verification_report_need
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests the machine-readable module verification report need type, one case per
   statement of the requirement:

   - the ``mod_ver_report`` directive exists
   - ``safety``, ``security``, ``status`` and ``verification_method`` classify
     the report, are mandatory and are value-checked
   - ``belongs_to`` is mandatory and restricted to the verified module
   - ``contains``, ``covers``, ``evidence`` and ``realizes`` are accepted, with
     ``realizes`` restricted to work products


.. Base architecture, requirement and work product objects used by the report tests

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

   Requirement text for verification report tests.

.. workproduct:: Verification Report Workproduct
   :id: wp__verification_report
   :status: valid

.. document:: Verification Evidence Document
   :id: doc__verification_evidence
   :status: valid
   :safety: ASIL_B
   :security: YES
   :realizes: wp__verification_report


.. The directive exists and accepts the classifying attributes, the optional
   metrics and every optional link.

.. mod_ver_report:: Verification Report Valid
   :id: mod_vrep__verification__valid
   :safety: ASIL_B
   :security: YES
   :status: valid
   :version: 1
   :verification_method: test_and_inspection
   :requirements_tests_completely_passed_percent: 95
   :line_coverage_percent: 90
   :branch_coverage_percent: 85
   :applies_to_module_version: 1.0.0
   :belongs_to: mod__verification_module
   :contains: doc__verification_evidence
   :covers: comp_req__verification__sample
   :evidence: doc__verification_evidence
   :realizes: wp__verification_report
   :expect_not: does not follow pattern, is missing required


.. Each classifying attribute is mandatory.

.. mod_ver_report:: Verification Report Without Safety
   :id: mod_vrep__verification__no_safety
   :security: YES
   :status: valid
   :verification_method: test
   :belongs_to: mod__verification_module
   :expect: mod_vrep__verification__no_safety: is missing required attribute: `safety`.

.. mod_ver_report:: Verification Report Without Security
   :id: mod_vrep__verification__no_security
   :safety: ASIL_B
   :status: valid
   :verification_method: test
   :belongs_to: mod__verification_module
   :expect: mod_vrep__verification__no_security: is missing required attribute: `security`.

.. mod_ver_report:: Verification Report Without Status
   :id: mod_vrep__verification__no_status
   :safety: ASIL_B
   :security: YES
   :verification_method: test
   :belongs_to: mod__verification_module
   :expect: mod_vrep__verification__no_status: is missing required attribute: `status`.

.. mod_ver_report:: Verification Report Without Method
   :id: mod_vrep__verification__no_method
   :safety: ASIL_B
   :security: YES
   :status: valid
   :belongs_to: mod__verification_module
   :expect: mod_vrep__verification__no_method: is missing required attribute: `verification_method`.


.. Each classifying attribute is restricted to its allowed values.

.. mod_ver_report:: Verification Report Invalid Safety
   :id: mod_vrep__verification__bad_safety
   :safety: ASIL_D
   :security: YES
   :status: valid
   :verification_method: test
   :belongs_to: mod__verification_module
   :expect: mod_vrep__verification__bad_safety.safety (ASIL_D): does not follow pattern

.. mod_ver_report:: Verification Report Invalid Security
   :id: mod_vrep__verification__bad_security
   :safety: ASIL_B
   :security: MAYBE
   :status: valid
   :verification_method: test
   :belongs_to: mod__verification_module
   :expect: mod_vrep__verification__bad_security.security (MAYBE): does not follow pattern

.. mod_ver_report:: Verification Report Invalid Status
   :id: mod_vrep__verification__bad_status
   :safety: ASIL_B
   :security: YES
   :status: draft
   :verification_method: test
   :belongs_to: mod__verification_module
   :expect: mod_vrep__verification__bad_status.status (draft): does not follow pattern


.. Invalid coverage percentage value in module verification report

.. mod_ver_report:: Verification Report Invalid Coverage
   :id: mod_vrep__verification__bad_coverage
   :safety: ASIL_B
   :security: YES
   :status: valid
   :verification_method: inspection
   :line_coverage_percent: 150
   :belongs_to: mod__verification_module
   :expect: mod_vrep__verification__bad_coverage.line_coverage_percent (150): does not follow pattern


.. The verified module link is mandatory and must name a module.

.. mod_ver_report:: Verification Report Without Module
   :id: mod_vrep__verification__no_module
   :safety: ASIL_B
   :security: YES
   :status: valid
   :verification_method: test
   :expect: mod_vrep__verification__no_module: is missing required link: `belongs_to`.

.. mod_ver_report:: Verification Report Wrong Module
   :id: mod_vrep__verification__bad_module
   :safety: ASIL_B
   :security: YES
   :status: valid
   :verification_method: test
   :belongs_to: comp__verification_component
   :expect: references 'comp__verification_component' as 'belongs_to', but it must reference Module (mod).


.. The work product link must name a work product.

.. mod_ver_report:: Verification Report Wrong Realizes
   :id: mod_vrep__verification__bad_realizes
   :safety: ASIL_B
   :security: YES
   :status: valid
   :verification_method: test
   :belongs_to: mod__verification_module
   :realizes: doc__verification_evidence
   :expect: references 'doc__verification_evidence' as 'realizes', but it must reference Workproduct (workproduct).
