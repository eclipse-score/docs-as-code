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


.. test_metadata:: Document and TVR Attribute Validation
   :id: test_metadata__doc_tool_attrs
   :fully_verifies_list: tool_req__docs_doc_generic_mandatory,tool_req__docs_tvr_safety,tool_req__docs_tvr_security,tool_req__docs_tvr_status,tool_req__docs_tvr_confidence_level
   :partially_verifies_list: tool_req__docs_tvr_version
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests the mandatory attributes of Generic Documents (document) and Tool
   Verification Reports (doc_tool), plus validation of TVR summary attribute
   values, as defined in the metamodel. Every mandatory attribute is
   exercised with an accepted value, an unaccepted value, and an omitted value.

   The tool_version attribute is not enforced yet for migration purposes.


.. Generic workproduct used as the realizes target of the documents below

.. workproduct:: Generic Workproduct
   :id: wp__doc_attrs
   :version: 1
   :status: valid

.. document:: Generic Document With All Mandatory Attributes
   :id: doc__attr_ok
   :version: 1
   :status: valid
   :safety: ASIL_B
   :security: YES
   :realizes: wp__doc_attrs
   :expect_not: is missing required attribute, is missing required link, does not follow pattern

.. document:: Generic Document With Invalid Status
   :id: doc__attr_bad_status
   :version: 1
   :status: active
   :safety: QM
   :security: NO
   :realizes: wp__doc_attrs
   :expect: status (active): does not follow pattern

.. document:: Generic Document With Invalid Safety Classification
   :id: doc__attr_bad_safety
   :version: 1
   :status: valid
   :safety: SIL3
   :security: NO
   :realizes: wp__doc_attrs
   :expect: safety (SIL3): does not follow pattern

.. document:: Generic Document With Invalid Security Classification
   :id: doc__attr_bad_security
   :version: 1
   :status: valid
   :safety: QM
   :security: MAYBE
   :realizes: wp__doc_attrs
   :expect: security (MAYBE): does not follow pattern

.. document:: Generic Document With Missing Status
   :id: doc__attr_missing_status
   :version: 1
   :safety: QM
   :security: NO
   :realizes: wp__doc_attrs
   :expect: doc__attr_missing_status: is missing required attribute: `status`.

.. document:: Generic Document With Missing Safety
   :id: doc__attr_missing_safety
   :version: 1
   :status: valid
   :security: NO
   :realizes: wp__doc_attrs
   :expect: doc__attr_missing_safety: is missing required attribute: `safety`.

.. document:: Generic Document With Missing Attributes
   :id: doc__attr_missing
   :version: 1
   :status: draft
   :safety: QM
   :expect: doc__attr_missing: is missing required attribute: `security`., doc__attr_missing: is missing required link: `realizes`.

.. document:: Generic Document With Invalid Realizes Target
   :id: doc__attr_bad_realizes
   :version: 1
   :status: valid
   :safety: QM
   :security: NO
   :realizes: comp_req__attr_bad_realizes
   :expect: references 'comp_req__attr_bad_realizes' as 'realizes', but it must reference Workproduct (workproduct).

.. doc_tool:: TVR With All Mandatory Attributes
   :id: doc_tool__attr_ok
   :version: 1
   :status: released
   :safety_affected: YES
   :security_affected: NO
   :tcl: HIGH
   :realizes: wp__doc_attrs
   :expect_not: is missing required attribute, is missing required link, does not follow pattern

.. doc_tool:: TVR With Valid Tool Version
   :id: doc_tool__attr_version
   :version: 1
   :status: qualified
   :safety_affected: NO
   :security_affected: NO
   :tcl: HIGH
   :tool_version: v1.2.3
   :expect_not: does not follow pattern

.. doc_tool:: TVR With Invalid Safety Classification
   :id: doc_tool__attr_bad_safety
   :version: 1
   :status: evaluated
   :safety_affected: MAYBE
   :security_affected: NO
   :tcl: LOW
   :expect: doc_tool__attr_bad_safety.safety_affected (MAYBE): does not follow pattern

.. doc_tool:: TVR With Invalid Security Classification
   :id: doc_tool__attr_bad_security
   :version: 1
   :status: evaluated
   :safety_affected: NO
   :security_affected: UNKNOWN
   :tcl: LOW
   :expect: doc_tool__attr_bad_security.security_affected (UNKNOWN): does not follow pattern

.. doc_tool:: TVR With Invalid Status Classification
   :id: doc_tool__attr_bad_status
   :version: 1
   :status: approved
   :safety_affected: NO
   :security_affected: NO
   :tcl: LOW
   :expect: doc_tool__attr_bad_status.status (approved): does not follow pattern

.. doc_tool:: TVR With Invalid Confidence Level
   :id: doc_tool__attr_bad_tcl
   :version: 1
   :status: qualified
   :safety_affected: NO
   :security_affected: NO
   :tcl: MEDIUM
   :expect: doc_tool__attr_bad_tcl.tcl (MEDIUM): does not follow pattern

.. doc_tool:: TVR Without Tool Version During Migration
   :id: doc_tool__attr_missing_tool_version
   :version: 1
   :status: evaluated
   :security_affected: NO
   :expect_not: is missing required attribute: `tool_version`

.. doc_tool:: TVR With Missing Mandatory Attributes
   :id: doc_tool__attr_missing
   :version: 1
   :expect: doc_tool__attr_missing: is missing required attribute: `status`., doc_tool__attr_missing: is missing required attribute: `security_affected`.
