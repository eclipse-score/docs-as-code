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

.. Tests that `covers` on feat_req and comp_req only allows aou_req as target.
.. req-Id: tool_req__docs_req_link_covers_aou

.. aou_req:: AoU target for covers tests
   :id: aou_req__covers__target
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid

   AoU content used for covers-link validation tests.


.. stkh_req:: Parent stakeholder requirement for covers tests
   :id: stkh_req__covers__parent
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :rationale: Stakeholder parent rationale for covers-link tests.


.. feat_req:: Parent feature requirement for covers tests
   :id: feat_req__covers__parent
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :satisfies: stkh_req__covers__parent

   Parent feature requirement used by covers-link tests.


.. Positive Test: feat_req pointing to an aou_req via covers is valid.
#EXPECT-NOT: feat_req__covers__good_1.covers (['aou_req__covers__target']): does not follow pattern `^aou_req__.*$`.

.. feat_req:: Feature requirement with valid covers link
   :id: feat_req__covers__good_1
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :satisfies: stkh_req__covers__parent
   :covers: aou_req__covers__target

   Valid feat_req that covers an AoU requirement.


.. Positive Test: comp_req pointing to an aou_req via covers is valid.
#EXPECT-NOT: comp_req__covers__good_1.covers (['aou_req__covers__target']): does not follow pattern `^aou_req__.*$`.

.. comp_req:: Component requirement with valid covers link
   :id: comp_req__covers__good_1
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :satisfies: feat_req__covers__parent
   :belongs_to: comp__covers__parent
   :covers: aou_req__covers__target

   Valid comp_req that covers an AoU requirement.


.. feat:: Feature for covers tests
   :id: feat__covers__parent
   :security: NO
   :safety: QM
   :status: valid
