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
the Bazel targets that produced its source files.  This module adds those
targets to the explicitly configured primary Need of the bundle and removes
the values from local Needs that no longer have a current bundle association.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass

from sphinx.application import Sphinx
from sphinx_needs import logging
from sphinx_needs.data import SphinxNeedsData
from sphinx_needs.need_item import NeedItem

from src.extensions.score_mounts import get_document_bundles
from src.extensions.score_mounts._resolver import BundleMetadata

logger = logging.get_logger(__name__)


@dataclass
class _BundleMetadataUpdate:
    """Results of applying bundle metadata to the current Needs.

    This object exists only for one ``env-updated`` pass. Primary Need
    association must finish before cleanup can run, so the cleanup step needs
    both the complete set of successful associations and the documents changed
    while applying them.

    ``matched_need_ids`` identifies Needs whose explicit bundle association is
    still current, and
    ``changed_docnames`` contains documents whose Need values were changed.
    The latter is returned to Sphinx so those documents can be considered
    changed by the build.
    """

    matched_need_ids: set[str]
    changed_docnames: set[str]


def _encode_target_values(bundle: BundleMetadata) -> dict[str, str]:
    """Encode a bundle's Bazel target metadata for storage in Need fields.

    This is called for a bundle with a valid explicit primary Need during
    ``env-updated``.
    Bundle metadata is the authoritative source for these extension-owned
    fields.  A single target keeps the existing scalar representation;
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
    """Clear extension-owned values from a Need with no current association.

    This is used during the final cleanup step of ``env-updated``. Sphinx
    keeps Needs from unchanged documents in its environment, so a value that
    was correct in an earlier build can remain after a bundle is renamed,
    removed, or no longer declares the Need. The return value tells the caller
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

    This is called for every valid primary Need association during
    ``env-updated``. The bundle is authoritative for these generated fields,
    so current values are written even when an older value is already present.
    The boolean is
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
    """Collect each bundle's own Needs before resolving explicit primary IDs.

    This runs at the start of ``env-updated`` from the current Sphinx
    environment.  Resolution needs this grouping because a primary Need must
    be declared by the bundle's own documents, not merely be present somewhere
    in the composed Sphinx environment.

    Imported Needs and external-reference Needs are excluded: a bundle must
    only receive metadata for Needs declared in its own documents, not for
    requirements copied in from another documentation bundle. A bundle
    mounted from another repository is still parsed into this Sphinx build, so
    its local Needs are intentionally handled like Needs from an in-tree
    bundle.
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


def _apply_primary_bundle_metadata(
    bundles: dict[str, BundleMetadata],
    grouped: dict[str, list[NeedItem]],
) -> _BundleMetadataUpdate:
    """Add each bundle's target information to its explicitly selected Need.

    This runs after ``_group_bundle_needs`` and before cleanup in the same
    ``env-updated`` pass. It records only successful associations so cleanup
    can distinguish a Need that still has a valid bundle from one carrying
    stale metadata. It also records changed documents because Sphinx tracks
    rebuilds by document, not by individual Need.
    """
    matched_need_ids: set[str] = set()
    changed_docnames: set[str] = set()
    for bundle_label, bundle in sorted(bundles.items()):
        if not bundle.primary_need_id:
            logger.info(
                f"bundle {bundle.label!r} ({bundle.name!r}) has direct code targets "
                "but no primary_need_id; bundle metadata is not attached to a Need",
                type="score_metamodel",
            )
            continue

        primary_need = next(
            (
                need
                for need in grouped.get(bundle_label, [])
                if str(need.get("id", "")) == bundle.primary_need_id
            ),
            None,
        )
        if primary_need is None:
            logger.error(
                f"bundle {bundle.label!r} ({bundle.name!r}) declares primary_need_id "
                f"{bundle.primary_need_id!r}, but that Need is not declared by the "
                "bundle's own documents",
                type="score_metamodel",
            )
            continue

        need_id = str(primary_need["id"])
        changed = _update_bundle_values(
            primary_need,
            _encode_target_values(bundle),
        )
        matched_need_ids.add(need_id)
        if changed:
            # Sphinx tracks changes by document, while the metadata is stored
            # on individual Needs. Rebuild the owning document when one of its
            # Need values changes.
            docname = primary_need.get("docname")
            if isinstance(docname, str):
                changed_docnames.add(docname)

    return _BundleMetadataUpdate(
        matched_need_ids=matched_need_ids,
        changed_docnames=changed_docnames,
    )


def _clear_unassociated_bundle_metadata(
    needs: dict[str, NeedItem],
    matched_need_ids: set[str],
) -> set[str]:
    """Remove stale bundle metadata after all current bundles were processed.

    This must run once, after ``_apply_primary_bundle_metadata`` has seen every
    bundle; running it earlier could clear a Need before a later bundle has a
    chance to match it.  It is necessary because Sphinx reuses Needs from
    unchanged documents, including documents mounted from external bundles,
    so removed or renamed bundles otherwise leave their old generated Bazel
    values behind.  The returned document names tell Sphinx to include
    documents affected by that cleanup in the rebuild.
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
    extensions have finished updating the environment. It gets the current
    bundle ownership map, resolves each configured primary Need, updates the
    generated Bazel fields, then removes stale values from local Needs without
    a current association. It returns the affected documents because Sphinx
    uses callback return values to decide which documents need to be written
    again.
    """
    owners = get_document_bundles(app)
    needs_data = SphinxNeedsData(app.env)
    needs = needs_data.get_needs_mutable()
    bundles, grouped = _group_bundle_needs(owners, needs)
    update = _apply_primary_bundle_metadata(bundles, grouped)
    # A document is changed both when new metadata is written and when stale
    # metadata is removed because its bundle no longer has a current
    # association.
    update.changed_docnames.update(
        _clear_unassociated_bundle_metadata(needs, update.matched_need_ids)
    )
    return sorted(update.changed_docnames)
