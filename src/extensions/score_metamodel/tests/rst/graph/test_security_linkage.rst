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
   :id: test_metadata__security_linkage
   :partially_verifies_list: tool_req__docs_arch_link_security, tool_req__docs_req_link_security_to_arch, tool_req__docs_arch_link_nonsec_to_sec_req, tool_req__docs_req_link_security_child
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests the security linkage checks between requirements and architecture.
   The checks tool_req__docs_req_link_security_to_arch,
   tool_req__docs_arch_link_nonsec_to_sec_req and
   tool_req__docs_req_link_security_child are new checks, so their findings
   are reported as infos instead of warnings.


.. Setup: link targets used by the tests below.

.. logic_arc_int:: Security interface
   :id: logic_arc_int__test_sec__yes
   :security: YES
   :safety: QM
   :status: valid

.. logic_arc_int:: Non-security interface
   :id: logic_arc_int__test_sec__no
   :security: NO
   :safety: QM
   :status: valid

.. comp:: Security component
   :id: comp__test_sec_yes
   :security: YES
   :safety: QM
   :status: valid

.. comp:: Non-security component
   :id: comp__test_sec_no
   :security: NO
   :safety: QM
   :status: valid


.. tool_req__docs_arch_link_security: a security component may only implement security interfaces.

.. Positive Test: security component implements a security interface.

.. comp:: Security component implements security interface
   :id: comp__test_sec_impl_ok
   :security: YES
   :safety: QM
   :status: valid
   :implements: logic_arc_int__test_sec__yes
   :expect_not: does not fulfill condition `security == YES`

.. Negative Test: security component implements a non-security interface.

.. comp:: Security component implements non-security interface
   :id: comp__test_sec_impl_bad
   :security: YES
   :safety: QM
   :status: valid
   :implements: logic_arc_int__test_sec__no
   :expect: Parent need `logic_arc_int__test_sec__no` does not fulfill condition `security == YES`.


.. tool_req__docs_req_link_security_to_arch: new check, reported as info only.

.. Positive Test: security requirement satisfied by a security component.

.. comp_req:: Security requirement
   :id: comp_req__test_sec_yes
   :security: YES
   :safety: QM
   :status: valid
   :satisfied_by: comp__test_sec_yes
   :expect_not: does not fulfill condition `security == YES`

.. Negative Test: security requirement satisfied by a non-security component.

.. comp_req:: Security requirement satisfied by non-security component
   :id: comp_req__test_sec_satisfied_by_nonsec
   :security: YES
   :safety: QM
   :status: valid
   :satisfied_by: comp__test_sec_no
   :expect: Parent need `comp__test_sec_no` does not fulfill condition `security == YES`


.. tool_req__docs_arch_link_nonsec_to_sec_req: new check, reported as info only.

.. comp_req:: Non-security requirement
   :id: comp_req__test_sec_no
   :security: NO
   :safety: QM
   :status: valid
   :satisfied_by: comp__test_sec_no

.. Positive Test: non-security interface fulfils a non-security requirement.

.. real_arc_int:: Non-security interface fulfils non-security requirement
   :id: real_arc_int__test_sec__fulfils_ok
   :security: NO
   :safety: ASIL_B
   :status: valid
   :fulfils: comp_req__test_sec_no
   :expect_not: does not fulfill condition `security == NO`

.. Negative Test: non-security interface fulfils a security requirement.

.. real_arc_int:: Non-security interface fulfils security requirement
   :id: real_arc_int__test_sec__fulfils_bad
   :security: NO
   :safety: ASIL_B
   :status: valid
   :fulfils: comp_req__test_sec_yes
   :expect: Parent need `comp_req__test_sec_yes` does not fulfill condition `security == NO`


.. tool_req__docs_req_link_security_child: new check, reported as info only.

.. Positive Test: one security child is enough, non-security children are allowed.

.. feat_req:: Security parent with a security child
   :id: feat_req__test_sec_parent_ok
   :security: YES
   :safety: QM
   :status: valid
   :expect_not: none of its child requirements

.. comp_req:: Security child
   :id: comp_req__test_sec_child_ok_yes
   :security: YES
   :safety: QM
   :status: valid
   :derived_from: feat_req__test_sec_parent_ok
   :satisfied_by: comp__test_sec_yes

.. comp_req:: Non-security child next to a security child
   :id: comp_req__test_sec_child_ok_no
   :security: NO
   :safety: QM
   :status: valid
   :derived_from: feat_req__test_sec_parent_ok
   :satisfied_by: comp__test_sec_no

.. Negative Test: security parent with only non-security children.

.. feat_req:: Security parent with only non-security children
   :id: feat_req__test_sec_parent
   :security: YES
   :safety: QM
   :status: valid
   :expect: is security relevant, but none of its child requirements is: comp_req__test_sec_child_no

.. comp_req:: Non-security child
   :id: comp_req__test_sec_child_no
   :security: NO
   :safety: QM
   :status: valid
   :derived_from: feat_req__test_sec_parent
   :satisfied_by: comp__test_sec_no
