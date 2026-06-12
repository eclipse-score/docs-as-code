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

#CHECK: check_metamodel_graph

--- Setup

.. an ASPICE 40 IIC standard requirement (valid link target).

.. std_req:: ASPICE 40 IIC requirement
   :id: std_req__aspice_40__iic_1

.. an ASPICE non-IIC standard requirement (invalid link target).

.. std_req:: ASPICE non-IIC requirement
   :id: std_req__aspice_40__bp_1

.. an standard work product (complies link is allowed, not checked by workproduct_aspice_40).

.. std_wp:: standard work product
   :id: std_wp__1

---

.. Positive test: workproduct links to an ASPICE 40 IIC requirement — no warning expected.

#EXPECT-NOT[+2]: aspice_40__iic

.. workproduct:: workproduct
   :id: wp__valid
   :complies: std_req__aspice_40__iic_1

.. Positive test: workproduct with no complies link — check condition not met, no warning.

#EXPECT-NOT[+2]: aspice_40__iic

.. workproduct:: Workproduct without complies
   :id: wp__no_impl

.. Positive test: workproduct complies with a std_wp — allowed, no warning.

#EXPECT-NOT[+2]: aspice_40__iic

.. workproduct:: workproduct complying with std_wp
   :id: wp__std_wp
   :complies: std_wp__1

.. Negative test: workproduct links to a non-IIC requirement — warning expected.

#EXPECT[+2]: Workproducts may only link to ASPICE 40 IIC

.. workproduct:: Invalid workproduct
   :id: wp__invalid
   :complies: std_req__aspice_40__bp_1
