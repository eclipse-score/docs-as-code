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

.. _example:


=======
Example
=======

This is a rendered example of the 'examples/linking-both' folder using the `docs` tool.

.. stkh_req:: TestTitle
   :id: stkh_req__index__test_requirement
   :status: valid
   :safety: QM
   :rationale: A simple requirement we need to enable a documentation build
   :reqtype: Functional

   Some content to make sure we also can render this
   This is a link to an external need inside the 'score' documentation.
   :need:`PROCESS_gd_req__req__attr_uid`.
   Note how it starts with the defined prefix but in UPPERCASE. This comes from sphinx-needs, `see here <https://github.com/useblocks/sphinx-needs/blob/master/sphinx_needs/external_needs.py#L119>`_



.. tool_req:: Some Title
   :id: tool_req__example__some_title
   :reqtype: Process
   :security: YES
   :safety: ASIL_B
   :satisfies: PROCESS_gd_req__req__attr_uid
   :status: invalid

   With this requirement we can check if the removal of the prefix is working correctly.
   It should remove id_prefix (PROCESS _) as it's defined inside the BUILD file and remove it before it checks the leftover value
   against the allowed defined regex in the metamodel
   Note: The ID is different here as the 'folder structure' is as well


.. toctree::
   :maxdepth: 1
   :titlesonly:

   Subfolder example <testing/index>
