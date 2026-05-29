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

.. stkh_req:: Test Req Extends 1
   :id: stkh_req__test__need_extends_1
   :status: invalid


.. stkh_req:: Test Req Extends 2
   :id: stkh_req__test__need_extends_abc
   :status: valid


.. feat_req:: Test Linkage Override
   :id: feat_req__test__linkage_override
   :satisfies: stkh_req__test__need_extends_1


.. Replacing of options that are already set is not allowed.

#EXPECT[+2]: Error when extending need: stkh_req__test__need_extends_1. Replacing of options that are already set is not allowed via needextends.

.. needextend:: c.this_doc() and id == 'stkh_req__test__need_extends_1'
   :status: valid


.. We explicitly allow the replacing of options on needs that are NOT set and
.. where the need is in the current document

#EXPECT-NOT[+2]: Replacing of options

.. needextend:: c.this_doc() and id == 'stkh_req__test__need_extends_1'
   :safety: NO


#EXPECT-NOT[+2]: Replacing of options

.. needextend:: c.this_doc() and id == 'stkh_req__test__need_extends_1'
   :safety: NO


#EXPECT[+2]: Error when extending need: feat_req__test__linkage_override. Replace or Delete action is not allowed via needextends.

.. needextend:: feat_req__test__linkage_override
   :satisfies: stkh_req__test__need_extends_abc


#EXPECT[+2]: Error when extending need: stkh_req__test__need_extends_1. Delete action is not allowed via needextends.

.. needextend:: id == 'stkh_req__test__need_extends_1'
   :-safety:


#EXPECT[+2]: Error when extending need: stkh_req__test__need_extends_1. Append action is not allowed via needextends on 'string type options'

.. needextend:: id == 'stkh_req__test__need_extends_1'
   :+safety: YES


.. This will be activated once we have activated the c.this_doc() check aswell
.. #EXPECT[+2]: Potentially altering needs outside of the document is not allowed. Please add 'c.this_doc()' to the needextend to limit it to only needs in the same document

.. .. needextend:: id == 'stkh_req__test__need_extends_1'
.. :security: QM
