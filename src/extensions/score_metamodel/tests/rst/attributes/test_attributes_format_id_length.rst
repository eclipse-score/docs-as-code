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
#CHECK: check_id_length

.. Id contains too many characters
#EXPECT: std_wp__testabcdefghijklmnopqrstuvwxyz123__abcd.id (std_wp__testabcdefghijklmnopqrstuvwxyz123__abcd): exceeds the maximum allowed length of 45 characters (current length: 47).

.. std_wp:: This is a test
   :id: std_wp__testabcdefghijklmnopqrstuvwxyz123__abcd

.. Id has correct length
#EXPECT-NOT: exceeds the maximum allowed length of 45 characters

.. std_wp:: This is a test
   :id: std_wp__test__abce
