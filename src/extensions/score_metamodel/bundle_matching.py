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
"""Find the local Sphinx-Needs item belonging to a documentation bundle."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from sphinx_needs.need_item import NeedItem


@dataclass(frozen=True)
class BundleNeedMatch:
    """Result of matching one bundle against its local Needs.

    This result is created during the ``env-updated`` pass, after Sphinx has
    collected the current Needs.  Keeping either the unambiguous Need ID or a
    diagnostic in one object lets the caller decide whether it is safe to
    write bundle metadata without guessing on an ambiguous match.

    Exactly one of ``need_id`` and ``error`` is populated. The error is already
    formatted for the diagnostic emitted by the caller.
    """

    need_id: str | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        """Reject a result that is neither a match nor a diagnostic."""
        if bool(self.need_id) == bool(self.error):
            raise ValueError("exactly one of need_id and error must be non-empty")


def match_bundle_to_need(
    bundle_name: str,
    own_needs: Iterable[NeedItem | Mapping[str, object]],
) -> BundleNeedMatch:
    """Find the Need whose ID follows ``<type>__<bundle_name>``.

    The bundle-metadata callback calls this once per current bundle after it
    has grouped the Needs declared in that bundle's documents.  The exact ID
    and unique-type checks are necessary because a bundle name alone is not a
    safe global identifier; when they fail, the caller must leave the Need
    unchanged rather than attach metadata to an arbitrary Need.

    The caller supplies only the Needs declared in the bundle's own documents.
    The function deliberately does not guess when no Need matches, when more
    than one Need type uses the same bundle name, or when the type is not
    unique within the bundle.
    """
    needs = list(own_needs)

    # A Need belongs to this bundle only when its ID combines its type with
    # the bundle name, for example ``comp__memory`` for ``memory``.
    candidates = sorted(
        (need for need in needs if need["id"] == f"{need['type']}__{bundle_name}"),
        key=lambda need: str(need["id"]),
    )
    candidate_ids = tuple(str(need["id"]) for need in candidates)
    if not candidates:
        return BundleNeedMatch(
            error=f"no Need has the exact ID suffix for {bundle_name!r}"
        )

    # Never choose between multiple Needs that claim the same bundle name.
    if len(candidates) != 1:
        return BundleNeedMatch(
            error="multiple Needs have the exact bundle name: "
            + ", ".join(candidate_ids)
        )

    candidate = candidates[0]
    candidate_type = str(candidate["type"])

    # A single name match is safe only when that Need type is unique in the
    # bundle; otherwise another Need of the same type could be the intended one.
    same_type = sorted(
        (need for need in needs if need.get("type") == candidate_type),
        key=lambda need: str(need["id"]),
    )
    conflicting_ids = tuple(str(need["id"]) for need in same_type)
    if len(same_type) != 1:
        return BundleNeedMatch(
            error="Need type is not unique in the bundle: " + ", ".join(conflicting_ids)
        )

    # The name and type checks above leave exactly one unambiguous Need.
    return BundleNeedMatch(need_id=str(candidate["id"]))
