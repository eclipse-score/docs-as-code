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
   :id: test_metadata__arch_link_fulfils_aou
   :fully_verifies_list: tool_req__docs_arch_link_fulfils_aou[version==3]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that the ``fulfils`` link of the architectural static view
   (feat_arc_sta) and of the component itself (comp) may target an Assumption
   of Use (aou_req) and that their target is restricted accordingly:
   - feat_arc_sta may fulfil aou_req without a warning
   - comp may fulfil aou_req without a warning
   - a fulfils link to a disallowed target type is rejected with a warning


.. Setup: link targets reused by the tests below.

.. feat:: Parent feature
   :id: feat__fulfils_aou

.. logic_arc_int:: Interface target
   :id: logic_arc_int__fulfils_aou__int

.. aou_req:: Assumption of use target 1
   :id: aou_req__fulfils_aou__good_1

   An assumption of use target.


.. aou_req:: Assumption of use target 2
   :id: aou_req__fulfils_aou__good_2

   Another assumption of use target.


.. comp_req:: Component requirement target
   :id: comp_req__fulfils_aou__bad

   A component requirement, which is not an assumption of use.


.. feat_arc_sta:: Static view fulfils an AoU
   :id: feat_arc_sta__fulfils_aou__good
   :security: NO
   :safety: QM
   :status: valid
   :includes: logic_arc_int__fulfils_aou__int
   :belongs_to: feat__fulfils_aou
   :fulfils: aou_req__fulfils_aou__good_1
   :expect_not: must reference

   Static view fulfilling an assumption of use.


.. comp:: Component fulfils an AoU
   :id: comp__fulfils_aou__good
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: feat__fulfils_aou
   :fulfils: aou_req__fulfils_aou__good_2
   :expect_not: must reference

   Component fulfilling an assumption of use.


.. feat_arc_sta:: Static view fulfils a disallowed target
   :id: feat_arc_sta__fulfils_aou__bad
   :security: NO
   :safety: QM
   :status: valid
   :includes: logic_arc_int__fulfils_aou__int
   :belongs_to: feat__fulfils_aou
   :fulfils: comp_req__fulfils_aou__bad
   :expect: but it must reference Feature Requirement (feat_req) or Assumption of Use Requirement (aou_req)

   Static view fulfilling a component requirement instead of an AoU.


.. comp:: Component fulfils a disallowed target
   :id: comp__fulfils_aou__bad
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: feat__fulfils_aou
   :fulfils: comp_req__fulfils_aou__bad
   :expect: but it must reference Assumption of Use Requirement (aou_req)

   Component fulfilling a component requirement instead of an AoU.
