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

.. std_req:: Standard requirement
   :id: std_req__iso26262__001

# Expect to warning with "complies"
#EXPECT-NOT: complies

.. gd_req:: No Link is ok, since complies is optional
   :id: gd_req__001

# Expect to warning with "complies"
#EXPECT-NOT: complies

.. gd_req:: Correct link to std_req
   :id: gd_req__002
   :complies: std_req__iso26262__001

#FIXME: this will currently be printed as an INFO, and not as a warning.
#       Re-enable EXCPECT once we can enable that as a warning.
#EXP-ECT: gd_req__003: references 'gd_req__001' as 'complies', but it must reference Standard Requirement (std_req).

.. gd_req:: Cannot refer to non std_req element
   :id: gd_req__003
   :complies: gd_req__001
