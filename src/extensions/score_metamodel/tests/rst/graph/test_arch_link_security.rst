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
   :id: test_metadata__arch_link_security
   :fully_verifies_list: tool_req__docs_arch_link_security[version==1]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that security relevant (Security == YES) architecture elements can
   only implement other security relevant architecture elements.  The check
   runs on the architecture types that own an implements link
   (real_arc_int_op implements logic_arc_int_op):
   - a security relevant source implementing a security relevant target builds
     without a warning
   - a security relevant source implementing a non-security relevant target
     triggers the graph check warning
   - a non-security relevant source is exempt from the check


.. logic_arc_int:: Security logic interface
   :id: logic_arc_int__arch_sec__logic_if
   :security: YES
   :safety: QM
   :status: valid


.. logic_arc_int:: Non-security logic interface
   :id: logic_arc_int__arch_sec__logic_if_nosec
   :security: NO
   :safety: QM
   :status: valid


.. logic_arc_int_op:: Security logic interface operation
   :id: logic_arc_int_op__arch_sec__logic_op_sec
   :security: YES
   :safety: QM
   :status: valid
   :included_by: logic_arc_int__arch_sec__logic_if


.. logic_arc_int_op:: Non-security logic interface operation
   :id: logic_arc_int_op__arch_sec__logic_op_nosec
   :security: NO
   :safety: QM
   :status: valid
   :included_by: logic_arc_int__arch_sec__logic_if_nosec


.. real_arc_int:: Security real interface
   :id: real_arc_int__arch_sec__real_if
   :security: YES
   :safety: QM
   :status: valid
   :language: cpp


.. real_arc_int:: Non-security real interface
   :id: real_arc_int__arch_sec__real_if_nosec
   :security: NO
   :safety: QM
   :status: valid
   :language: rust


.. Positive: security relevant source implements security relevant target.

.. real_arc_int_op:: Security source implements security target
   :id: real_arc_int_op__arch_sec__src_good
   :security: YES
   :safety: QM
   :status: valid
   :included_by: real_arc_int__arch_sec__real_if
   :implements: logic_arc_int_op__arch_sec__logic_op_sec
   :expect_not: does not fulfill condition


.. Negative: security relevant source implements non-security target.

.. real_arc_int_op:: Security source implements non-security target
   :id: real_arc_int_op__arch_sec__src_bad
   :security: YES
   :safety: QM
   :status: valid
   :included_by: real_arc_int__arch_sec__real_if
   :implements: logic_arc_int_op__arch_sec__logic_op_nosec
   :expect: does not fulfill condition `security == YES`


.. Exempt: non-security source is not selected by the check.

.. real_arc_int_op:: Non-security source implements non-security target
   :id: real_arc_int_op__arch_sec__src_exempt
   :security: NO
   :safety: QM
   :status: valid
   :included_by: real_arc_int__arch_sec__real_if_nosec
   :implements: logic_arc_int_op__arch_sec__logic_op_nosec
   :expect_not: does not fulfill condition


.. Negative: with `check_all` only the violating target is reported.

.. real_arc_int_op:: Security source implements security and non-security target
   :id: real_arc_int_op__arch_sec__src_mixed
   :security: YES
   :safety: QM
   :status: valid
   :included_by: real_arc_int__arch_sec__real_if
   :implements: logic_arc_int_op__arch_sec__logic_op_sec, logic_arc_int_op__arch_sec__logic_op_nosec
   :expect: Parent need `logic_arc_int_op__arch_sec__logic_op_nosec` does not fulfill condition `security == YES`
   :expect_not: Parent need `logic_arc_int_op__arch_sec__logic_op_sec`
