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
   :fully_verifies_list: tool_req__docs_dec_rec_type[version==2]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that the dec_rec need type supports its mandatory attributes and affects
   link, and that its tracking option accepts GitHub issue and pull request links.


.. dec_rec:: Test Decision Record 1
   :id: dec_rec__platform__feature_delivery
   :status: accepted
   :context: A decision record is needed for the test.
   :decision: Use a dedicated decision record need type.
   :tracking: https://github.com/eclipse-score/docs-as-code/issues/1
   :version: 1
   :consequences: Provides traceability for decisions.
   :affects: dec_rec__feature__follow_up


.. dec_rec:: Test Decision Record 2
   :id: dec_rec__feature__follow_up
   :status: proposed
   :context: This decision record is affected by another decision.
   :decision: Keep the relationship explicit.
   :tracking: https://github.com/eclipse-score/score/pull/2#discussion_r3
   :expect_not: dec_rec__feature__follow_up.tracking (https://github.com/eclipse-score/score/pull/2#discussion_r3): does not follow pattern
   :version: 1
   :consequences: Allows linking between related decisions.


.. dec_rec:: Decision Record with missing tracking
   :id: dec_rec__logging__no_tracking
   :status: accepted
   :context: The tracking link is missing.
   :decision: Require tracking for every decision record.
   :version: 1
   :consequences: Decisions must refer to an issue or pull request.
   :expect: dec_rec__logging__no_tracking: is missing required attribute: `tracking`.


.. dec_rec:: Decision Record with missing consequences
   :id: dec_rec__logging__no_consequences
   :status: accepted
   :context: The consequences are missing.
   :decision: Require consequences for every decision record.
   :tracking: https://github.com/eclipse-score/score/pull/2
   :version: 1
   :expect: dec_rec__logging__no_consequences: is missing required attribute: `consequences`.


.. dec_rec:: Decision Record with invalid tracking organization
   :id: dec_rec__dac__invalid_tracking_org
   :status: accepted
   :context: Tracking links must belong to the eclipse-score organization.
   :decision: Reject links owned by other organizations.
   :tracking: https://github.com/other-org/score/pull/3
   :version: 1
   :consequences: Tracking is restricted to the eclipse-score organization.
   :expect: dec_rec__dac__invalid_tracking_org.tracking (https://github.com/other-org/score/pull/3): does not follow pattern


.. dec_rec:: Decision Record with missing status
   :id: dec_rec__proc__missing_status
   :context: The status is missing.
   :decision: Required fields remain enforced.
   :tracking: https://github.com/eclipse-score/score/issues/1
   :version: 1
   :consequences: Every decision record must declare its status.
   :expect: dec_rec__proc__missing_status: is missing required attribute: `status`.
