# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

from src.extensions.score_metamodel.bundle_matching import match_bundle_to_need


def need(*, need_id: str, need_type: str) -> dict[str, str]:
    """Represent the matching fields of one local Sphinx-Needs item."""
    return {"id": need_id, "type": need_type}


def test_matches_the_exact_name_and_unique_type() -> None:
    """The ``memory`` bundle matches the only local Need named ``memory``."""
    bundle_name = "memory"
    own_needs = [
        # This Need has the expected ``<type>__<bundle name>`` ID.
        need(need_id="comp__memory", need_type="comp"),
        # This Need belongs to another bundle and must not affect the match.
        need(need_id="feat__storage", need_type="feat"),
    ]

    result = match_bundle_to_need(bundle_name, own_needs)

    assert result.need_id == "comp__memory"


def test_does_not_match_case_insensitively() -> None:
    """A bundle name must match the Need ID with the same casing."""
    bundle_name = "memory"
    own_needs = [
        # ``comp__Memory`` is not the exact ID for the ``memory`` bundle.
        need(need_id="comp__Memory", need_type="comp"),
    ]

    result = match_bundle_to_need(bundle_name, own_needs)

    assert result.error == "no Need has the exact ID suffix for 'memory'"


def test_rejects_multiple_matching_names_across_types() -> None:
    """The matcher refuses when two Need types claim the same bundle."""
    bundle_name = "memory"
    own_needs = [
        need(need_id="comp__memory", need_type="comp"),
        need(need_id="feat__memory", need_type="feat"),
    ]

    result = match_bundle_to_need(bundle_name, own_needs)

    # Both IDs match the bundle name, so choosing one type would be arbitrary.
    assert (
        result.error
        == "multiple Needs have the exact bundle name: comp__memory, feat__memory"
    )


def test_rejects_a_second_need_of_the_matching_type() -> None:
    """The matching Need type must be unique within the bundle."""
    bundle_name = "memory"
    own_needs = [
        need(need_id="comp__memory", need_type="comp"),
        need(need_id="comp__other", need_type="comp"),
    ]

    result = match_bundle_to_need(bundle_name, own_needs)

    # The name identifies ``comp__memory``, but the ``comp`` type is not unique.
    assert (
        result.error
        == "Need type is not unique in the bundle: comp__memory, comp__other"
    )


def test_does_not_use_an_arbitrary_need_as_fallback() -> None:
    """A different Need name is not used as a fallback match."""
    bundle_name = "memory"
    own_needs = [
        # There is a component Need, but it belongs to ``other``, not ``memory``.
        need(need_id="comp__other", need_type="comp"),
    ]

    result = match_bundle_to_need(bundle_name, own_needs)

    assert result.error == "no Need has the exact ID suffix for 'memory'"
