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

#CHECK: check_options

.. std_wp:: Standard work product
   :id: std_wp__iso26262__001

.. std_req:: Standard requirement
   :id: std_req__iso26262__001

.. std_req:: Standard IIC requirement
   :id: std_req__aspice_40__iic_001

----

# Expect no warning with "complies"
#EXPECT-NOT: complies

.. workproduct:: No Link is ok, since complies is optional
   :id: wp__001

---

# Expect no warning with "complies"
#EXPECT-NOT: complies

.. workproduct:: Linking to std_wp is allowed
   :id: wp__002
   :complies: std_wp__iso26262__001

---

#FIXME: this will currently be printed as an INFO, and not as a warning.
#       Re-enable EXCPECT once we can enable that as a warning.
#EXP-ECT: wp__003: references 'std_req__iso26262__001' as 'complies', but it must reference Standard Work Product (std_wp) or ^std_req__aspice_40__iic.*$.

.. workproduct:: Cannot refer to std_req element
   :id: wp__003
   :complies: std_req__iso26262__001

---


# Expect no warning with "complies"
#EXPECT-NOT: complies

.. workproduct:: But it can refer to std_req if it is an IIC requirement
   :id: wp__003
   :complies: std_req__aspice_40__iic_001

---
