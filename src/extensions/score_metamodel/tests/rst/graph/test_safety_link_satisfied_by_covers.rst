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
   :id: test_metadata__safety_link_satisfied_by_covers
   :partially_verifies_list:
      tool_req__docs_arch_link_qm_to_safety_req,
      tool_req__docs_common_attr_safety_link_check
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests the graph-based safety-derivation checks for ``fulfils``,
   ``satisfied_by`` and ``covers``.
   The implementing side of a link must be at least as safe as the specified side;
   a link to a less-safe target triggers a warning.


--- Setup: requirements used as link targets

.. feat_req:: QM feature requirement
   :id: feat_req__graph__qm
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :satisfied_by: feat__graph__feat_qm

.. feat_req:: ASIL_B feature requirement
   :id: feat_req__graph__asil
   :reqtype: Functional
   :security: NO
   :safety: ASIL_B
   :status: valid
   :satisfied_by: feat__graph__feat_asil

.. comp_req:: QM component requirement
   :id: comp_req__graph__qm
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :satisfied_by: comp__graph__comp_qm

.. comp_req:: ASIL_B component requirement
   :id: comp_req__graph__asil
   :reqtype: Functional
   :security: NO
   :safety: ASIL_B
   :status: valid
   :satisfied_by: comp__graph__comp_asil

.. aou_req:: QM assumption of use
   :id: aou_req__graph__qm
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid

.. aou_req:: ASIL_B assumption of use
   :id: aou_req__graph__asil
   :reqtype: Functional
   :security: NO
   :safety: ASIL_B
   :status: valid


--- Setup: architecture elements used as ``satisfied_by`` targets

.. feat:: QM feature
   :id: feat__graph__feat_qm
   :security: NO
   :safety: QM
   :status: valid

.. feat:: ASIL_B feature
   :id: feat__graph__feat_asil
   :security: NO
   :safety: ASIL_B
   :status: valid

.. comp:: QM component
   :id: comp__graph__comp_qm
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: feat__graph__feat_qm

.. comp:: ASIL_B component
   :id: comp__graph__comp_asil
   :security: NO
   :safety: ASIL_B
   :status: valid
   :belongs_to: feat__graph__feat_asil


--- Setup: architecture elements used as ``fulfils`` sources

.. feat_arc_sta:: QM static view
   :id: feat_arc_sta__graph__qm
   :security: NO
   :safety: QM
   :status: valid
   :includes: logic_arc_int__graph__int
   :belongs_to: feat__graph__feat_qm

.. feat_arc_sta:: ASIL_B static view
   :id: feat_arc_sta__graph__asil
   :security: NO
   :safety: ASIL_B
   :status: valid
   :includes: logic_arc_int__graph__int
   :belongs_to: feat__graph__feat_asil

.. logic_arc_int:: interface
   :id: logic_arc_int__graph__int
   :security: NO
   :safety: QM
   :status: valid


=== fulfils: a QM architecture element must not fulfil an ASIL requirement

.. Positive: QM architecture element fulfils a QM requirement — no warning.

.. feat_arc_sta:: QM arch fulfils QM req (ok)
   :id: feat_arc_sta__graph__qm_fulfils_qm
   :security: NO
   :safety: QM
   :status: valid
   :fulfils: feat_req__graph__qm
   :includes: logic_arc_int__graph__int
   :belongs_to: feat__graph__feat_qm
   :expect_not: cannot fulfil an ASIL

.. Negative: QM architecture element fulfils an ASIL requirement — warning.

.. feat_arc_sta:: QM arch fulfils ASIL req (forbidden)
   :id: feat_arc_sta__graph__qm_fulfils_asil
   :security: NO
   :safety: QM
   :status: valid
   :fulfils: feat_req__graph__asil
   :includes: logic_arc_int__graph__int
   :belongs_to: feat__graph__feat_qm
   :expect: cannot fulfil an ASIL requirement


=== satisfied_by: an ASIL requirement must not be satisfied by a QM element

.. Positive: ASIL requirement satisfied by an ASIL element — no warning.

.. feat_req:: ASIL req satisfied by ASIL feat (ok)
   :id: feat_req__graph__asil_by_asil
   :reqtype: Functional
   :security: NO
   :safety: ASIL_B
   :status: valid
   :satisfied_by: feat__graph__feat_asil
   :expect_not: cannot be satisfied by a QM

.. Positive: QM requirement satisfied by a QM element — no warning.

.. feat_req:: QM req satisfied by QM feat (ok)
   :id: feat_req__graph__qm_by_qm
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :satisfied_by: feat__graph__feat_qm
   :expect_not: cannot be satisfied by a QM

.. Negative: ASIL requirement satisfied by a QM element — warning (less-safe target).

.. comp_req:: ASIL req satisfied by QM comp (forbidden)
   :id: comp_req__graph__asil_by_qm
   :reqtype: Functional
   :security: NO
   :safety: ASIL_B
   :status: valid
   :satisfied_by: comp__graph__comp_qm
   :expect: cannot be satisfied by a QM element


=== covers: a QM requirement must not cover an ASIL assumption of use

.. Positive: QM requirement covers a QM AoU — no warning.

.. feat_req:: QM req covers QM aou (ok)
   :id: feat_req__graph__qm_covers_qm
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :satisfied_by: feat__graph__feat_qm
   :covers: aou_req__graph__qm
   :expect_not: cannot cover an ASIL

.. Positive: ASIL requirement covers an ASIL AoU — no warning.

.. comp_req:: ASIL req covers ASIL aou (ok)
   :id: comp_req__graph__asil_covers_asil
   :reqtype: Functional
   :security: NO
   :safety: ASIL_B
   :status: valid
   :satisfied_by: comp__graph__comp_asil
   :covers: aou_req__graph__asil
   :expect_not: cannot cover an ASIL

.. Negative: QM requirement covers an ASIL AoU — warning.

.. feat_req:: QM req covers ASIL aou (forbidden)
   :id: feat_req__graph__qm_covers_asil
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :satisfied_by: feat__graph__feat_qm
   :covers: aou_req__graph__asil
   :expect: cannot cover an ASIL assumption of use
