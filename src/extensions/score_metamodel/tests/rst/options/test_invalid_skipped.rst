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


.. test_metadata:: Invalid Needs are skipped and not tested
   :id: test_metadata__invalid_needs_skipped
   :fully_verifies_list: tool_req__docs_common_attr_status_invalid[version==1]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Test that invalid needs are skipped and are not checked


..
   Every case below pairs a `valid` need with an `invalid` twin.
   The `valid` need proves the check fires, the `invalid` twin proves it is skipped.



.. Fixtures for the link and graph checks below

.. feat:: Parent feature of the component
   :id: feat__options_inv_parent
   :safety: ASIL_B
   :status: valid
   :security: NO

   Parent feature fixture.

.. comp:: Component satisfying the requirements below
   :id: comp__options_inv_target
   :safety: ASIL_B
   :status: valid
   :security: NO
   :belongs_to: feat__options_inv_parent

   Component fixture.

.. feat_req:: ASIL_B parent requirement
   :id: feat_req__options__asil_parent
   :reqtype: Functional
   :safety: ASIL_B
   :status: valid
   :security: NO
   :valid_from: v1.0

   Valid ASIL_B parent requirement.

.. feat_req:: Invalid ASIL_B parent requirement
   :id: feat_req__options__asil_parent_inv
   :reqtype: Functional
   :safety: ASIL_B
   :status: invalid
   :security: NO
   :valid_from: v1.0

   Invalid ASIL_B parent requirement.



--- Local check: missing mandatory attribute begin ---

.. comp_req:: Missing safety attribute
   :id: comp_req__options__missing_attr_valid
   :reqtype: Functional
   :status: valid
   :security: NO
   :satisfied_by: comp__options_inv_target
   :expect: comp_req__options__missing_attr_valid: is missing required attribute: `safety`.

   The safety attribute is missing.

.. comp_req:: Missing safety attribute
   :id: comp_req__options__missing_attr_invalid
   :reqtype: Functional
   :status: invalid
   :security: NO
   :satisfied_by: comp__options_inv_target
   :expect_not: is missing required attribute

   The safety attribute is missing.

--- Local check: missing mandatory attribute end ---



--- Local check: attribute does not follow pattern begin ---

.. comp_req:: Security attribute with wrong value
   :id: comp_req__options__bad_pattern_valid
   :reqtype: Functional
   :safety: QM
   :status: valid
   :security: MAYBE
   :satisfied_by: comp__options_inv_target
   :expect: comp_req__options__bad_pattern_valid.security (MAYBE): does not follow pattern `^(YES|NO)$`.

   The security attribute has a value outside the pattern.

.. comp_req:: Security attribute with wrong value
   :id: comp_req__options__bad_pattern_invalid
   :reqtype: Functional
   :safety: QM
   :status: invalid
   :security: MAYBE
   :satisfied_by: comp__options_inv_target
   :expect_not: does not follow pattern

   The security attribute has a value outside the pattern.

--- Local check: attribute does not follow pattern end ---



--- Local check: link references wrong need type begin ---

.. comp_req:: Derived from a component instead of a feature requirement
   :id: comp_req__options__bad_link_valid
   :reqtype: Functional
   :safety: ASIL_B
   :status: valid
   :security: NO
   :satisfied_by: comp__options_inv_target
   :derived_from: comp__options_inv_target
   :expect: comp_req__options__bad_link_valid: references 'comp__options_inv_target' as 'derived_from', but it must reference Feature Requirement (feat_req).

   The derived_from link points to the wrong need type.

.. comp_req:: Derived from a component instead of a feature requirement
   :id: comp_req__options__bad_link_invalid
   :reqtype: Functional
   :safety: ASIL_B
   :status: invalid
   :security: NO
   :satisfied_by: comp__options_inv_target
   :derived_from: comp__options_inv_target
   :expect_not: but it must reference

   The derived_from link points to the wrong need type.

--- Local check: link references wrong need type end ---



--- Local check: prohibited word in title begin ---

.. comp_req:: The component must start
   :id: comp_req__options__weak_title_valid
   :reqtype: Functional
   :safety: QM
   :status: valid
   :security: NO
   :satisfied_by: comp__options_inv_target
   :expect: comp_req__options__weak_title_valid: contains a weak word: `must` in option: `title`. Please revise the wording.

   The title contains a prohibited word.

.. comp_req:: The component must start
   :id: comp_req__options__weak_title_invalid
   :reqtype: Functional
   :safety: QM
   :status: invalid
   :security: NO
   :satisfied_by: comp__options_inv_target
   :expect_not: contains a weak word

   The title contains a prohibited word.

--- Local check: prohibited word in title end ---



--- Local check: id exceeds maximum length begin ---

.. comp_req:: Id is too long
   :id: comp_req__options__id_exceeds_the_max_length_valid
   :reqtype: Functional
   :safety: QM
   :status: valid
   :security: NO
   :satisfied_by: comp__options_inv_target
   :expect: exceeds the maximum allowed length of 45 characters

   The id is longer than 45 characters.

.. comp_req:: Id is too long
   :id: comp_req__options__id_exceeds_the_max_length_inv
   :reqtype: Functional
   :safety: QM
   :status: invalid
   :security: NO
   :satisfied_by: comp__options_inv_target
   :expect_not: exceeds the maximum allowed length

   The id is longer than 45 characters.

--- Local check: id exceeds maximum length end ---



--- Graph check: QM requirement derived from ASIL requirement begin ---

.. comp_req:: QM requirement derived from an ASIL_B requirement
   :id: comp_req__options__qm_from_asil_valid
   :reqtype: Functional
   :safety: QM
   :status: valid
   :security: NO
   :satisfied_by: comp__options_inv_target
   :derived_from: feat_req__options__asil_parent
   :expect: comp_req__options__qm_from_asil_valid: Parent need `feat_req__options__asil_parent` does not fulfill condition `safety == QM`. Explanation: QM requirements cannot be derived from ASIL requirements.

   A QM requirement cannot be derived from an ASIL_B requirement.

.. Invalid child: the graph check must not select it.

.. comp_req:: QM requirement derived from an ASIL_B requirement
   :id: comp_req__options__qm_from_asil_invalid
   :reqtype: Functional
   :safety: QM
   :status: invalid
   :security: NO
   :satisfied_by: comp__options_inv_target
   :derived_from: feat_req__options__asil_parent
   :expect_not: QM requirements cannot be derived from ASIL requirements.

   A QM requirement cannot be derived from an ASIL_B requirement.

.. Invalid parent: invalid needs stay part of the graph, so a valid child is still checked against them.

.. comp_req:: QM requirement derived from an invalid ASIL_B requirement
   :id: comp_req__options__qm_from_inv_parent
   :reqtype: Functional
   :safety: QM
   :status: valid
   :security: NO
   :satisfied_by: comp__options_inv_target
   :derived_from: feat_req__options__asil_parent_inv
   :expect: comp_req__options__qm_from_inv_parent: Parent need `feat_req__options__asil_parent_inv` does not fulfill condition `safety == QM`. Explanation: QM requirements cannot be derived from ASIL requirements.

   The parent is invalid, but still visible to the graph check.

--- Graph check: QM requirement derived from ASIL requirement end ---



--- All checks at once begin ---

.. An invalid need that violates every check above must not produce any warning.
.. Every metamodel warning starts with the need id, so `expect_not` on the id catches all of them.

.. comp_req:: The component shall do everything wrong
   :id: comp_req__options__all_checks_violated_invalid
   :safety: QM
   :status: invalid
   :security: MAYBE
   :satisfied_by: comp__options_inv_target
   :derived_from: comp__options_inv_target, feat_req__options__asil_parent
   :expect_not: comp_req__options__all_checks_violated_invalid

--- All checks at once end ---
