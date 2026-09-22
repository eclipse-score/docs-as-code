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
"""Copy Bazel target information from documentation bundles to local Needs.

Each documentation bundle can own one or more Sphinx documents and can expose
the Bazel targets that produced its source files.  This module finds the Needs
declared in those documents, adds the target information to the matching Need,
and removes the values from local Needs that no longer have a matching bundle.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass

from sphinx.application import Sphinx
from sphinx_needs import logging
from sphinx_needs.data import SphinxNeedsData
from sphinx_needs.need_item import NeedItem

from src.extensions.score_metamodel.bundle_matching import match_bundle_to_need
from src.extensions.score_mounts import get_document_bundles
from src.extensions.score_mounts._resolver import BundleMetadata

logger = logging.get_logger(__name__)


@dataclass
class _BundleMetadataUpdate:
    """Results of applying bundle metadata to the current Needs.

    This object exists only for one ``env-updated`` pass.  Matching must finish
    before cleanup can run, so the cleanup step needs both the complete set of
    successful matches and the documents changed while applying them.

    ``matched_need_ids`` identifies Needs whose bundle still matches, and
    ``changed_docnames`` contains documents whose Need values were changed.
    The latter is returned to Sphinx so those documents can be considered
    changed by the build.
    """

    matched_need_ids: set[str]
    changed_docnames: set[str]


def _render_target_values(bundle: BundleMetadata) -> dict[str, str]:
    """Convert a bundle's Bazel targets to values stored on a Need.

    This is called for an unambiguous bundle match during ``env-updated``.
    Bundle metadata is the authoritative source for these extension-owned
    fields, so the current targets must be rendered before they are written to
    the Need.  A single target keeps the existing scalar representation;
    multiple targets use compact JSON because the Need fields are strings.

    A single target is stored as a plain label and rule type.  Multiple targets
    are stored as compact JSON lists, keeping labels and types in the same
    declared order.
    """
    targets = bundle.code_targets
    labels = [target.label for target in targets]
    types = [target.type for target in targets]
    if len(targets) == 1:
        return {"bazel_target": labels[0], "bazel_type": types[0]}
    return {
        "bazel_target": json.dumps(labels, separators=(",", ":")),
        "bazel_type": json.dumps(types, separators=(",", ":")),
    }


def _clear_bundle_values(need: NeedItem) -> bool:
    """Clear extension-owned values from a Need with no current match.

    This is used during the final cleanup step of ``env-updated``.  Sphinx
    keeps Needs from unchanged documents in its environment, so a value that
    was correct in an earlier build can remain after a bundle is renamed,
    removed, or can no longer be matched.  The return value tells the caller
    whether the owning document must be reported as changed.
    """
    changed = False
    for field in ("bazel_target", "bazel_type"):
        if need.get(field):
            need[field] = ""
            changed = True
    return changed


def _update_bundle_values(
    need: NeedItem,
    values: dict[str, str],
) -> bool:
    """Apply current bundle values and report whether the Need was changed.

    This is called for every unambiguous match during ``env-updated``.  The
    bundle is authoritative for these generated fields, so current values are
    written even when an older value is already present.  The boolean is
    needed only to avoid asking Sphinx to rebuild a document whose Need values
    are already current.
    """
    changed = False
    for field in ("bazel_target", "bazel_type"):
        value = values[field]
        raw_current = need.get(field, "")
        current = "" if raw_current is None else str(raw_current)
        if current == value:
            continue
        need[field] = value
        changed = True
    return changed


def _group_bundle_needs(
    owners: dict[str, BundleMetadata],
    needs: dict[str, NeedItem],
) -> tuple[dict[str, BundleMetadata], dict[str, list[NeedItem]]]:
    """Collect each bundle's own Needs before matching by bundle name.

    This runs at the start of ``env-updated`` from the current Sphinx
    environment.  Matching needs this grouping because the same Need ID shape
    can occur in different documents, while a bundle must only receive
    metadata for Needs declared in its own documents.

    Imported and external Needs are excluded: a bundle must only receive
    metadata for Needs declared in its own documents, not for requirements
    copied in from another documentation bundle.
    """
    grouped: dict[str, list[NeedItem]] = defaultdict(list)
    bundle_by_label: dict[str, BundleMetadata] = {}
    for owner in owners.values():
        if owner.label and owner.code_targets:
            bundle_by_label.setdefault(owner.label, owner)

    for need in needs.values():
        if need.get("is_external") or need.get("is_import"):
            continue
        docname = need.get("docname")
        if not isinstance(docname, str):
            continue
        owner = owners.get(docname)
        if owner is None or not owner.label or not owner.code_targets:
            continue
        grouped[owner.label].append(need)
    return bundle_by_label, grouped


def _apply_matching_bundles(
    bundles: dict[str, BundleMetadata],
    grouped: dict[str, list[NeedItem]],
) -> _BundleMetadataUpdate:
    """Add each bundle's target information to its uniquely matching Need.

    This runs after ``_group_bundle_needs`` and before cleanup in the same
    ``env-updated`` pass.  It records only successful matches so cleanup can
    distinguish a Need that still has a valid bundle from one carrying stale
    metadata.  It also records changed documents because Sphinx tracks rebuilds
    by document, not by individual Need.
    """
    matched_need_ids: set[str] = set()
    changed_docnames: set[str] = set()
    for bundle_label, bundle in sorted(bundles.items()):
        result = match_bundle_to_need(bundle.name, grouped.get(bundle_label, []))
        if result.error:
            logger.info(
                f"bundle {bundle.label!r} ({bundle.name!r}) has direct code targets "
                f"but cannot be associated with one local Need: {result.error}",
                type="score_metamodel",
            )
            continue

        matching_need = next(
            need for need in grouped[bundle_label] if need["id"] == result.need_id
        )
        need_id = str(matching_need["id"])
        changed = _update_bundle_values(
            matching_need,
            _render_target_values(bundle),
        )
        matched_need_ids.add(need_id)
        if changed:
            # Sphinx tracks changes by document, while the metadata is stored
            # on individual Needs. Rebuild the owning document when one of its
            # Need values changes.
            docname = matching_need.get("docname")
            if isinstance(docname, str):
                changed_docnames.add(docname)

    return _BundleMetadataUpdate(
        matched_need_ids=matched_need_ids,
        changed_docnames=changed_docnames,
    )


def _clear_unmatched_bundle_metadata(
    needs: dict[str, NeedItem],
    matched_need_ids: set[str],
) -> set[str]:
    """Remove stale bundle metadata after all current bundles were matched.

    This must run once, after ``_apply_matching_bundles`` has seen every
    bundle; running it earlier could clear a Need before a later bundle has a
    chance to match it.  It is necessary because Sphinx reuses Needs from
    unchanged documents, so removed or renamed bundles otherwise leave their
    old generated Bazel values behind.  The returned document names tell
    Sphinx to include documents affected by that cleanup in the rebuild.
    """
    changed_docnames: set[str] = set()
    for need_id, current_need in needs.items():
        if need_id in matched_need_ids:
            continue
        if current_need.get("is_external") or current_need.get("is_import"):
            continue
        if _clear_bundle_values(current_need):
            # Clearing bundle values changes the Need in this document, so it
            # belongs in the same document-change set as updating a match.
            docname = current_need.get("docname")
            if isinstance(docname, str):
                changed_docnames.add(docname)
    return changed_docnames


def apply_bundle_metadata(app: Sphinx, _: object) -> list[str]:
    """Update local Needs after Sphinx has collected the current documents.

    This is the ``env-updated`` callback and runs after collection and other
    extensions have finished updating the environment.  It gets the current
    bundle ownership map, matches bundles to their own Needs, updates the
    generated Bazel fields, then removes stale values from unmatched local
    Needs.  It returns the affected documents because Sphinx uses callback
    return values to decide which documents need to be written again.
    """
    owners = get_document_bundles(app)
    needs_data = SphinxNeedsData(app.env)
    needs = needs_data.get_needs_mutable()
    bundles, grouped = _group_bundle_needs(owners, needs)
    update = _apply_matching_bundles(bundles, grouped)
    # A document is changed both when new metadata is written and when stale
    # metadata is removed because its bundle no longer matches.
    update.changed_docnames.update(
        _clear_unmatched_bundle_metadata(needs, update.matched_need_ids)
    )
    return sorted(update.changed_docnames)
