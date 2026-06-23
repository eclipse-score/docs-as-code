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
   :id: test_metadata__metamodel_link_checks
   :partially_verifies_list: LACKS TOOL REQ
   :test_type: requirements_based
   :derivation_technique: requirements_based
   :check: check_options
   
   Tests if metamodel link options are correclty checked



.. std_req:: Standard requirement
   :id: std_req__iso26262__001

.. Expect to warning with "complies"

.. gd_req:: No Link is ok, since complies is optional
   :id: gd_req__001
   :expect_not: complies



.. FIXME: this will currently be printed as an INFO, and not as a warning.
      Re-enable EXCPECT once we can enable that as a warning.

.. .. gd_req:: Cannot refer to non std_req element
..    :id: gd_req__003
..    :complies: gd_req__001
..    :expect:  gd_req__003: references 'gd_req__001' as 'complies', but it must reference Standard Requirement (std_req).
