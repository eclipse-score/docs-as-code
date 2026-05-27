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



.. stkh_req:: Test Req Extends 1
   :id: stkh_req__test__need_extends_1
   :status: invalid
   



.. Replacing of options that are already set is not allowed.
#EXPECT: Replacing of options that are already set is not allowed via needextends.

.. needextend:: c.this_doc() and id == 'stkh_req__test__need_extends_1'
  :status: valid


.. We explicitly allow the replacing of options on needs that are NOT set and 
.. where the need is in the current document
#EXPECT-NOT: Replacing of options

.. needextend:: c.this_doc() and id == 'stkh_req__test__need_extends_1'
  :safety: NO


# EXPECT: Potentially altering needs outside of the document is not allowed. Please add 'c.this_doc()' to the needextend to limit it to only needs in the same document
.. needextend:: id == 'stkh_req__test__need_extends_1'
   :security: QM
