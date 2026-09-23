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


.. test_metadata::
   :id: test_metadata__req_link_satisfies_allowed
   :partially_verifies_list: tool_req__docs_req_link_satisfies_allowed[version==1]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests the allowed source and target combinations for the ``satisfies`` attribute.
   The table rows Feature Requirement -> Stakeholder Requirement and
   Component Requirement -> Feature Requirement are implemented via
   ``derived_from`` because ``satisfies`` is hard-deprecated for those types.
   Having at least one link is enforced for ``tool_req``.
   It is not yet enforced for ``gd_req`` (TODO in metamodel.yaml).


.. Setup: link targets used by the tests below.

.. stkh_req:: Stakeholder requirement
   :id: stkh_req__test_satisfies

.. feat_req:: Feature requirement
   :id: feat_req__test_satisfies

.. comp_req:: Component requirement
   :id: comp_req__test_satisfies

.. gd_req:: Process requirement
   :id: gd_req__test_satisfies

.. workproduct:: Workproduct
   :id: wp__test_satisfies
   :status: valid

.. role:: Role
   :id: rl__test_satisfies

.. workflow:: Workflow
   :id: wf__test_satisfies
   :status: valid
   :input: wp__test_satisfies
   :output: wp__test_satisfies
   :approved_by: rl__test_satisfies
   :responsible: rl__test_satisfies


.. gd_req:: Process requirement satisfies workflow
   :id: gd_req__test_satisfies_ok
   :satisfies: wf__test_satisfies
   :expect_not: must reference

   Some content.


.. gd_req:: Process requirement satisfies stakeholder requirement
   :id: gd_req__test_satisfies_bad
   :satisfies: stkh_req__test_satisfies
   :expect: gd_req__test_satisfies_bad: references 'stkh_req__test_satisfies' as 'satisfies', but it must reference Workflow (workflow).

   Some content.


.. tool_req:: Tool requirement satisfies process requirement
   :id: tool_req__test_satisfies_gd
   :satisfies: gd_req__test_satisfies
   :expect_not: must reference

   Some content.

.. tool_req:: Tool requirement satisfies stakeholder requirement
   :id: tool_req__test_satisfies_stkh
   :satisfies: stkh_req__test_satisfies
   :expect_not: must reference

   Some content.

.. tool_req:: Tool requirement satisfies feature requirement
   :id: tool_req__test_satisfies_feat
   :satisfies: feat_req__test_satisfies
   :expect_not: must reference

   Some content.

.. tool_req:: Tool requirement satisfies component requirement
   :id: tool_req__test_satisfies_comp
   :satisfies: comp_req__test_satisfies
   :expect_not: must reference

   Some content.

.. tool_req:: Tool requirement satisfies workflow
   :id: tool_req__test_satisfies_bad
   :satisfies: wf__test_satisfies
   :expect: tool_req__test_satisfies_bad: references 'wf__test_satisfies' as 'satisfies', but it must reference Process Requirements (gd_req) or Stakeholder Requirement (stkh_req) or Feature Requirement (feat_req) or Component Requirement (comp_req).

   Some content.


.. feat_req:: Feature requirement derived from stakeholder requirement
   :id: feat_req__test_derived_from_stkh
   :derived_from: stkh_req__test_satisfies
   :expect_not: feat_req__test_derived_from_stkh: references

   Some content.


.. comp_req:: Component requirement derived from feature requirement
   :id: comp_req__test_derived_from_feat
   :derived_from: feat_req__test_satisfies
   :expect_not: comp_req__test_derived_from_feat: references

   Some content.


.. comp_req:: Component requirement derived from stakeholder requirement
   :id: comp_req__test_derived_from_bad
   :derived_from: stkh_req__test_satisfies
   :expect: comp_req__test_derived_from_bad: references 'stkh_req__test_satisfies' as 'derived_from', but it must reference Feature Requirement (feat_req).

   Some content.


.. tool_req:: Tool requirement without any satisfies link
   :id: tool_req__test_missing_satisfies
   :expect: tool_req__test_missing_satisfies: is missing required link: `satisfies`.

   Some content.
