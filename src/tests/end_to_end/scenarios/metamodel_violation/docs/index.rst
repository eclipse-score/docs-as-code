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

Metamodel Check
===============

.. test_req:: A requirement missing its status
   :id: test_req__demo_missing

Needextend checks
-----------------

needextend may only add values to unset options of Needs in its own document.

.. test_req:: Needextend replaces a set option
   :id: test_req__needextend_replace_set
   :status: valid

.. test_req:: Needextend sets an unset option
   :id: test_req__needextend_replace_unset
   :status: valid

.. test_req:: Needextend replaces a link
   :id: test_req__needextend_replace_link
   :status: valid
   :links: test_req__needextend_replace_set

.. test_req:: Needextend deletes an option
   :id: test_req__needextend_delete
   :status: valid

.. test_req:: Needextend appends to a string option
   :id: test_req__needextend_append
   :status: valid

.. needextend:: c.this_doc() and id == 'test_req__needextend_replace_set'
   :status: draft

.. needextend:: c.this_doc() and id == 'test_req__needextend_replace_unset' and not safety
   :safety: QM

.. needextend:: c.this_doc() and id == 'test_req__needextend_replace_unset' and not tags
   :tags: extended

.. needextend:: test_req__needextend_replace_link
   :links: test_req__needextend_delete

.. needextend:: c.this_doc() and id == 'test_req__needextend_delete'
   :-status:

.. needextend:: c.this_doc() and id == 'test_req__needextend_append'
   :+status: draft

.. needextend:: id == 'test_req__needextend_replace_set'
   :tags: unscoped

.. needextend:: test_req__unknown
