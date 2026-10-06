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
   :id: test_metadata__common_attrs_security
   :fully_verifies_list: tool_req__docs_common_attr_security[version==1]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that the common ``security`` attribute is enforced on every directive
   that declares it in the metamodel.

   All directives that have ``security`` use the same regex
   ``^(YES|NO)$`` — a single equivalence class.
   One representative (stkh_req) covers all types for the invalid-value case.
   Since ``security`` is mandatory only for requirement types,
   the missing-value case is covered only for that class.

   Pseudo-code for generating the test cases::

       CLASSES = [
           ("req/arch", types=[stkh_req, feat_req, feat, comp, ...],
                        regex="^(YES|NO)$"),
       ]
       for class in CLASSES:
           representative = class.types[0]
           emit_valid_case(representative, value="YES")
           emit_invalid_value_case(representative, bad_value="MAYBE")
           if class.is_mandatory:
               emit_missing_case(representative)


.. stkh_req:: Valid security on a requirement type
   :id: stkh_req__security__good
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: YES
   :status: valid
   :rationale: valid security
   :valid_from: v1.0
   :expect_not: does not follow pattern, missing required attribute: `security`


.. stkh_req:: Invalid security on a requirement type
   :id: stkh_req__security__bad
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: MAYBE
   :status: valid
   :rationale: invalid security
   :valid_from: v1.0
   :expect: security (MAYBE): does not follow pattern


.. stkh_req:: Missing security on a requirement type
   :id: stkh_req__security__missing
   :version: 1
   :reqtype: Functional
   :safety: QM
   :status: valid
   :rationale: missing security
   :valid_from: v1.0
   :expect: is missing required attribute: `security`


.. stkh_req:: Valid NO security value
   :id: stkh_req__security__no
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :rationale: NO is a valid security value
   :valid_from: v1.0
   :expect_not: does not follow pattern