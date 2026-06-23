..
   # *******************************************************************************
   # Copyright (c) 2025 Contributors to the Eclipse Foundation
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
   :id: test_metadata__wp_comp
   :partially_verifies_list: LACKS TOOL REQ
   :test_type: requirements_based
   :derivation_technique: requirements_based
   :check: check_options
   
   Tests if we correctly enforce mandatory options & links for workproducts


.. std_wp:: Standard work product
   :id: std_wp__iso26262__001

.. std_req:: Standard requirement
   :id: std_req__iso26262__001

.. std_req:: Standard IIC requirement
   :id: std_req__aspice_40__iic_001

----

.. Expect no warning with "complies"

.. workproduct:: No Link is ok, since complies is optional
   :id: wp__001
   :expect_not: complies

---

.. Expect no warning with "complies"

.. workproduct:: Linking to std_wp is allowed
   :id: wp__002
   :complies: std_wp__iso26262__001
   :expect_not: complies

---

.. FIXME: this will currently be printed as an INFO, and not as a warning.
   Re-enable EXCPECT once we can enable that as a warning.

.. workproduct:: Cannot refer to std_req element
   :id: wp__003
   :complies: std_req__iso26262__001
   :expect: std_req__iso26262__001` does not fulfill condition `{'or': ['id contains aspice_40__iic', 'id contains std_wp']}`. Explanation: Workproducts may only link to ASPICE 40 IIC stakeholder requirements. Please ensure that the linked requirement is an ASPICE 40 IIC stakeholder requirement.

---



.. workproduct:: But it can refer to std_req if it is an IIC requirement
   :id: wp__003_two
   :complies: std_req__aspice_40__iic_001
   :expect_not: complies

