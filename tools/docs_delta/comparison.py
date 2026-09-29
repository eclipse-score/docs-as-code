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
"""Need inventory types, loading, and comparison rules."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

JsonObject = dict[str, object]
NeedMap = Mapping[str, JsonObject]
MISSING = object()
# Source locations, generated IDs, and test-result links vary with the build
# revision without changing the requirement represented by a Need.
VOLATILE_NEED_FIELDS = frozenset(
    {
        "lineno",
        "lineno_content",
        "source",
        "target_id",
        "is_modified",
        "source_code_link",
        "testlink",
    }
)


class DocsDeltaError(ValueError):
    """A user-actionable input or report-generation error."""


@dataclass(frozen=True)
class NeedChange:
    """A Need identified by ID, with whichever before/after versions exist.

    An absent baseline means the Need was added; an absent current value means
    it was removed. When both versions exist, ``changed_fields`` reports only
    differences that are meaningful under the comparison's volatile-field
    policy.
    """

    need_id: str
    baseline: JsonObject | None
    current: JsonObject | None

    @property
    def changed_fields(self) -> tuple[str, ...]:
        """Return changed non-volatile fields in deterministic order."""

        if self.baseline is None or self.current is None:
            return ()
        names = set(self.baseline) | set(self.current)
        return tuple(
            sorted(
                name
                for name in names
                if name not in VOLATILE_NEED_FIELDS
                and not _json_values_equal(
                    self.baseline.get(name, MISSING),
                    self.current.get(name, MISSING),
                )
            )
        )


@dataclass(frozen=True)
class NeedComparison:
    """Added, removed, modified, and unchanged counts for Need inventories.

    Changed entries are stored in sorted-ID order by :func:`compare_needs`,
    which makes both the Markdown output and its review order reproducible.
    """

    added: tuple[NeedChange, ...]
    removed: tuple[NeedChange, ...]
    modified: tuple[NeedChange, ...]
    unchanged_count: int


@dataclass(frozen=True)
class PageChange:
    """One rendered HTML path that was added, removed, or modified."""

    path: str


@dataclass(frozen=True)
class PageComparison:
    """Added, removed, modified, and unchanged counts for rendered pages.

    A page's relative path determines its identity; a rename therefore appears
    as one removal and one addition rather than a guessed rename relationship.
    """

    added: tuple[PageChange, ...]
    removed: tuple[PageChange, ...]
    modified: tuple[PageChange, ...]
    unchanged_count: int


def _json_values_equal(left: object, right: object) -> bool:
    """Compare JSON-shaped values consistently and distinguish missing keys.

    Python considers ``True == 1``. Serializing the values keeps those Need
    field changes visible, while the private sentinel separates a missing
    field from an explicit JSON ``null``.
    """

    if left is MISSING or right is MISSING:
        return left is right
    return json.dumps(left, sort_keys=True, ensure_ascii=False) == json.dumps(
        right, sort_keys=True, ensure_ascii=False
    )


def _flatten_needs(path: Path) -> dict[str, JsonObject]:
    """Flatten versioned Sphinx-Needs output into one ID-to-record mapping.

    Sphinx-Needs exports a ``versions`` map, with each version holding its own
    ``needs`` map. Version names are not part of a Need's identity for this
    report, so entries from all versions are combined by ID; if an ID occurs
    more than once, the last entry in JSON iteration order supplies its record.
    Unexpectedly shaped version containers are skipped; malformed individual
    Need entries fail with a useful error rather than silently disappearing.
    """

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DocsDeltaError(f"cannot read needs JSON {path}: {exc}") from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("versions"), dict):
        raise DocsDeltaError(f"needs JSON has no versions map: {path}")

    versions = cast(dict[str, object], payload["versions"])
    result: dict[str, JsonObject] = {}
    for version_value in versions.values():
        if not isinstance(version_value, dict):
            continue
        version = cast(dict[str, object], version_value)
        needs_value = version.get("needs")
        if not isinstance(needs_value, dict):
            continue
        needs = cast(dict[object, object], needs_value)
        for need_id, need in needs.items():
            if not isinstance(need_id, str) or not isinstance(need, dict):
                raise DocsDeltaError(f"invalid Need entry in {path}")
            result[need_id] = cast(JsonObject, need)
    return result


def load_needs(directory: Path) -> dict[str, JsonObject]:
    """Load the root ``needs.json`` inventory from a rendered docs directory."""

    needs_path = directory / "needs.json"
    if not needs_path.is_file():
        raise DocsDeltaError(f"needs JSON is missing: {needs_path}")
    return _flatten_needs(needs_path)


def compare_needs(baseline: NeedMap, current: NeedMap) -> NeedComparison:
    """Compare Needs by ID, ignoring only explicitly volatile fields.

    A field added or removed from a record counts as a modification. All
    result groups are sorted by Need ID so report order does not depend on JSON
    object insertion order.
    """

    added: list[NeedChange] = []
    removed: list[NeedChange] = []
    modified: list[NeedChange] = []
    unchanged_count = 0

    for need_id in sorted(set(baseline) | set(current)):
        old = baseline.get(need_id)
        new = current.get(need_id)
        change = NeedChange(need_id, old, new)
        if old is None:
            added.append(change)
        elif new is None:
            removed.append(change)
        elif change.changed_fields:
            modified.append(change)
        else:
            unchanged_count += 1

    return NeedComparison(
        added=tuple(added),
        removed=tuple(removed),
        modified=tuple(modified),
        unchanged_count=unchanged_count,
    )
