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

   Tests that the common ``security`` attribute is enforced on every type
   that declares it in the metamodel.

   All directives that have ``security`` use the same regex
   ``^(YES|NO)$`` — a single equivalence class.
   One representative (stkh_req) covers all types for the valid-value case.

   For the other safety-critical types, we only verify a missing attribute is detected.


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


.. feat_req:: Missing security on a feature requirement
   :id: feat_req__security__missing
   :version: 1
   :reqtype: Functional
   :safety: QM
   :status: valid
   :rationale: missing security
   :valid_from: v1.0
   :satisfied_by: feat__security_support
   :expect: is missing required attribute: `security`


.. comp_req:: Missing security on a component requirement
   :id: comp_req__security__missing
   :reqtype: Interface
   :safety: QM
   :status: valid
   :satisfied_by: comp__security_support
   :expect: is missing required attribute: `security`

   Missing security test for comp_req.


.. aou_req:: Missing security on an assumption-of-use requirement
   :id: aou_req__security__missing
   :reqtype: Functional
   :safety: QM
   :status: valid
   :expect: is missing required attribute: `security`

   Missing security test for aou_req.


.. feat_arc_sta:: Missing security on a feature architecture static view
   :id: feat_arc_sta__security__missing
   :safety: QM
   :status: valid
   :includes: logic_arc_int__security_support, logic_arc_int_op__security_support
   :belongs_to: feat__security_support
   :expect: is missing required attribute: `security`


.. feat:: Missing security on a feature
   :id: feat__security__missing
   :safety: QM
   :status: valid
   :expect: is missing required attribute: `security`


.. logic_arc_int:: Missing security on a logical architecture interface
   :id: logic_arc_int__security__missing
   :safety: QM
   :status: valid
   :expect: is missing required attribute: `security`


.. logic_arc_int_op:: Missing security on a logical architecture interface operation
   :id: logic_arc_int_op__security__missing
   :safety: QM
   :status: valid
   :included_by: logic_arc_int__security_support
   :expect: is missing required attribute: `security`


.. comp_arc_sta:: Missing security on a component architecture static view
   :id: comp_arc_sta__security__missing
   :safety: QM
   :status: valid
   :belongs_to: comp__security_support
   :expect: is missing required attribute: `security`


.. comp:: Missing security on a component
   :id: comp__security__missing
   :safety: QM
   :status: valid
   :belongs_to: feat__security_support
   :expect: is missing required attribute: `security`


.. real_arc_int:: Missing security on a real architecture interface
   :id: real_arc_int__security__missing
   :safety: QM
   :status: valid
   :expect: is missing required attribute: `security`


.. real_arc_int_op:: Missing security on a real architecture interface operation
   :id: real_arc_int_op__security__missing
   :safety: QM
   :status: valid
   :included_by: real_arc_int__security_support
   :expect: is missing required attribute: `security`


..
   Support needs used as link targets by the negative fixtures above.
   All are valid so they do not interact with the security graph checks.


.. feat:: Support feature for security tests
   :id: feat__security_support
   :version: 1
   :security: NO
   :safety: QM
   :status: valid


.. comp:: Support component for security tests
   :id: comp__security_support
   :version: 1
   :security: NO
   :safety: QM
   :status: valid


.. logic_arc_int:: Support logical interface for security tests
   :id: logic_arc_int__security_support
   :security: NO
   :safety: QM
   :status: valid


.. logic_arc_int_op:: Support logical interface operation for security tests
   :id: logic_arc_int_op__security_support
   :security: NO
   :safety: QM
   :status: valid
   :included_by: logic_arc_int__security_support


.. real_arc_int:: Support real interface for security tests
   :id: real_arc_int__security_support
   :security: NO
   :safety: QM
   :status: valid


.. real_arc_int_op:: Support real interface operation for security tests
   :id: real_arc_int_op__security_support
   :security: NO
   :safety: QM
   :status: valid
   :included_by: real_arc_int__security_support
