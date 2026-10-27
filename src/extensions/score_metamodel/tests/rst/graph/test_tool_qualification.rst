..
   # *******************************************************************************
   # Copyright (c) 2026 Contributors to the Eclipse Foundation
   #
   # See the NOTICE file(s) distributed with this work for additional
   # information regarding copyright ownership.
   #
   # This program and the accompanying materials are made available under the
   # terms of the Apache License 2.0 which is available at
   # https://www.apache.org/licenses/LICENSE-2.0
   #
   # SPDX-License-Identifier: Apache-2.0
   # *******************************************************************************

.. test_metadata::
   :id: test_metadata__tool_qualification
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Exercises the conditional local validation of tool malfunctions.

.. doc_tool:: Draft tool verification report
   :id: doc_tool__tool_qualification_checks
   :status: draft
   :security_affected: NO
   :version: 1

.. tool_req:: Tool qualification check requirement
   :id: tool_req__tool_qualification_checks
   :version: 1

.. tool_usecase:: Tool qualification check use case
   :id: tool_usecase__tool_qualification_checks
   :belongs_to: doc_tool__tool_qualification_checks
   :version: 1

.. tool_usecase:: Tool usage context without a pre-existing requirement
   :id: tool_usecase__tool_qualification_unmapped
   :belongs_to: doc_tool__tool_qualification_checks
   :version: 1

.. potential_tool_malfunction:: Missing detection value
   :id: potential_tool_malfunction__tool_qualification_missing_detection
   :parent_needs: tool_usecase__tool_qualification_checks
   :violates: tool_req__tool_qualification_checks
   :safety_affected: YES
   :version: 1
   :expect: safety-relevant malfunctions must define

.. potential_tool_malfunction:: Positive detection without measure
   :id: potential_tool_malfunction__tool_qualification_missing_measure
   :parent_needs: tool_usecase__tool_qualification_checks
   :violates: tool_req__tool_qualification_checks
   :safety_affected: YES
   :detection_sufficient: YES
   :version: 1
   :expect: non-empty `safety_measures`

.. potential_tool_malfunction:: Insufficient detection
   :id: potential_tool_malfunction__tool_qualification_insufficient_detection
   :parent_needs: tool_usecase__tool_qualification_checks
   :violates: tool_req__tool_qualification_checks
   :safety_affected: YES
   :detection_sufficient: NO
   :version: 1
   :expect_not: safety-relevant malfunctions must define

.. potential_tool_malfunction:: Non-safety malfunction
   :id: potential_tool_malfunction__tool_qualification_non_safety
   :parent_needs: tool_usecase__tool_qualification_checks
   :violates: tool_req__tool_qualification_checks
   :safety_affected: NO
   :version: 1
   :expect_not: non-safety malfunctions must not define

.. potential_tool_malfunction:: Meaningless detection value
   :id: potential_tool_malfunction__tool_qualification_meaningless_detection
   :parent_needs: tool_usecase__tool_qualification_checks
   :violates: tool_req__tool_qualification_checks
   :safety_affected: NO
   :detection_sufficient: YES
   :version: 1
   :expect: non-safety malfunctions must not define
