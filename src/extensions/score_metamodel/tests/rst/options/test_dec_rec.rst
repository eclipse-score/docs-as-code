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

.. test_metadata:: Test Decision Record Type
   :id: test_metadata__dec_rec
   :partially_verifies_list: tool_req__docs_dec_rec_type
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that the dec_rec need type supports its mandatory attributes and affects
   link, and that its tracking option accepts GitHub issue and pull request links.


.. dec_rec:: Test Decision Record 1
   :id: dec_rec__test__decision_record_1
   :status: accepted
   :context: A decision record is needed for the test.
   :decision: Use a dedicated decision record need type.
   :tracking: https://github.com/eclipse-score/docs-as-code/issues/1
   :expect_not: dec_rec__test__decision_record_1.tracking (https://github.com/eclipse-score/docs-as-code/issues/1): does not follow pattern
   :affects: dec_rec__test__decision_record_2


.. dec_rec:: Test Decision Record 2
   :id: dec_rec__test__decision_record_2
   :status: proposed
   :context: This decision record is affected by another decision.
   :decision: Keep the relationship explicit.
   :tracking: https://github.com/eclipse-score/score/pull/2
   :expect_not: dec_rec__test__decision_record_2.tracking (https://github.com/eclipse-score/score/pull/2): does not follow pattern
