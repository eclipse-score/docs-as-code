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


.. Base architecture and requirement objects used by verification report tests

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


.. Valid machine-readable verification report need
#EXPECT-NOT[+2]: does not follow pattern

.. mod_ver_report:: Verification Report Valid
   :id: mod_vrep__verification__valid
   :safety: ASIL_B
   :security: YES
   :status: valid
   :verification_method: test_and_inspection
   :requirements_tests_completely_passed_percent: 95
   :line_coverage_percent: 90
   :branch_coverage_percent: 85
   :applies_to_module_version: 1.0.0
   :belongs_to: mod__verification_module
   :covers: comp__verification_component, comp_req__verification__sample


.. Invalid coverage percentage value in module verification report
#EXPECT[+2]: mod_vrep__verification__bad_coverage.line_coverage_percent (150): does not follow pattern

.. mod_ver_report:: Verification Report Invalid Coverage
   :id: mod_vrep__verification__bad_coverage
   :safety: ASIL_B
   :security: YES
   :status: invalid
   :verification_method: inspection
   :line_coverage_percent: 150
   :belongs_to: mod__verification_module
   :covers: comp__verification_component
