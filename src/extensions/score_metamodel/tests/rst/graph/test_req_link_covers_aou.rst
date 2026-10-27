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
   :id: test_metadata__req_link_covers_aou
   :fully_verifies_list: tool_req__docs_req_link_covers_aou[version==1]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests the allowed source and target combinations for the ``covers`` attribute.
   Feature requirements (feat_req) and component requirements (comp_req) may link
   to assumptions of use (aou_req) via ``covers``. All other targets are invalid.


.. Setup: link targets used by the tests below.

.. feat:: Feature
   :id: feat__test_covers
   :safety: QM
   :security: NO
   :status: valid

.. comp:: Component
   :id: comp__test_covers
   :safety: QM
   :security: NO
   :status: valid
   :belongs_to: feat__test_covers

.. aou_req:: Assumption of use
   :id: aou_req__test_covers
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid


.. feat_req:: Feature requirement covers assumption of use
   :id: feat_req__test_covers_aou
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :satisfied_by: feat__test_covers
   :covers: aou_req__test_covers
   :expect_not: must reference


.. comp_req:: Component requirement covers assumption of use
   :id: comp_req__test_covers_aou
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :satisfied_by: comp__test_covers
   :covers: aou_req__test_covers
   :expect_not: must reference


.. stkh_req:: Stakeholder requirement
   :id: stkh_req__test_covers
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :rationale: target for invalid covers test
   :valid_from: v1.0

.. feat_req:: Feature requirement covers stakeholder requirement
   :id: feat_req__test_covers_bad
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :satisfied_by: feat__test_covers
   :covers: stkh_req__test_covers
   :expect: feat_req__test_covers_bad: references 'stkh_req__test_covers' as 'covers', but it must reference Assumption of Use Requirement (aou_req).
