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


.. test_metadata:: Test Common Attribute Version
   :id: test_metadata__common_attr_version
   :partially_verifies_list: tool_req__docs_common_attr_version
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that a versioning attribute is mandatory for all needs and that it
   accepts whole numbers.

   Partial because "rejects non-whole numbers" cannot be tested with this rst-file approach.

.. Valid whole-number version.

.. stkh_req:: Version 1
   :id: stkh_req__common_attr_version__aaaa
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :rationale: valid version
   :valid_from: v1.0
   :expect_not: is missing required attribute: `version`

.. Valid larger whole-number version.

.. stkh_req:: Version 34
   :id: stkh_req__common_attr_version__bbbb
   :version: 34
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :rationale: valid version
   :valid_from: v1.0
   :expect_not: is missing required attribute: `version`

.. Missing version is rejected because the version attribute is mandatory.

.. stkh_req:: No version
   :id: stkh_req__common_attr_version__cccc
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :rationale: missing version
   :valid_from: v1.0
   :expect: is missing required attribute: `version`
