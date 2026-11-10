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

.. test_metadata:: Architectural link correlations
   :id: test_metadata__arch_linkage_safety
   :fully_verifies_list: tool_req__arch_linkage_safety[version==3]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Verifies that the mandatory architectural correlations are enforced.
   ``logic_arc_int`` without ``included_by`` link to a ``feat`` must be
   rejected as missing a mandatory link.

.. feat:: Feature required for the test
   :id: feat__linkage_safety
   :version: 1
   :security: NO
   :safety: QM
   :status: valid

.. logic_arc_int:: Logical interface with mandatory included_by link
   :id: logic_arc_int__linkage_safety__good
   :version: 1
   :security: NO
   :safety: QM
   :status: valid
   :included_by: feat__linkage_safety
   :expect_not: is missing required link

   A ``logic_arc_int`` must have ``included_by`` set to a ``feat``.

.. logic_arc_int:: Logical interface missing mandatory included_by link
   :id: logic_arc_int__linkage_safety__missing
   :version: 1
   :security: NO
   :safety: QM
   :status: valid
   :expect: is missing required link: `included_by`

   A ``logic_arc_int`` without ``included_by`` is rejected.