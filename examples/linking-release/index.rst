..
   # *******************************************************************************
   # Copyright (c) 2024 Contributors to the Eclipse Foundation
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

Hello World
=================
This is a simple example of a documentation page using the `docs` tool.

.. stkh_req:: TestTitle
   :id: stkh_req__docs__test_requirement
   :status: valid
   :safety: QM
   :rationale: A simple requirement we need to enable a documentation build
   :reqtype: Functional

   Some content to make sure we also can render this
   This is a link to an external need inside the 'score' documentation.
   :need:`PROCESS_gd_req__req__attr_uid`
   Note how it starts with the defined prefix but in UPPERCASE. This comes from sphinx-needs, `see here <https://github.com/useblocks/sphinx-needs/blob/master/sphinx_needs/external_needs.py#L119>`_
