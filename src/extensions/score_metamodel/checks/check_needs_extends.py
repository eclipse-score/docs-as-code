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
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

import sphinx_needs.directives.need
from sphinx_needs.config import NeedsSphinxConfig
from sphinx_needs.data import (
    ExtendType,
    NeedsExtendType,
    NeedsMutable,
)
from sphinx_needs.directives.needextend import extend_needs_data as original_function
from sphinx_needs.filter_common import filter_needs_mutable
from sphinx_needs.logging import get_logger, log_warning
from sphinx_needs.need_item import NeedItem
from sphinx_needs.needs_schema import (
    FieldFunctionArray,
    FieldLiteralValue,
    LinksFunctionArray,
    LinksLiteralValue,
)

logger = get_logger(__name__)

NeedextendLocation = tuple[str, int]


def _location(needextend: NeedsExtendType) -> NeedextendLocation:
    """Return the source location used for every diagnostic of one directive."""
    return needextend["docname"], needextend["lineno"]


def _warn(message: str, location: NeedextendLocation) -> None:
    """Report a needextend violation at the directive, not at its target need."""
    log_warning(logger, message, "needextend", location=location)


def _resolve_needextend_targets(
    local_needs: NeedsMutable,
    all_needs: NeedsMutable,
    needextend: NeedsExtendType,
    needs_config: NeedsSphinxConfig,
) -> list[NeedItem]:
    """Find local targets and report violations of the document scope rules."""
    location = _location(needextend)
    if needextend["filter_is_id"]:
        need_id = needextend["filter"]
        if need_id in local_needs:
            return [local_needs[need_id]]
        elif need_id in all_needs:
            _warn(
                "Needextends may only modify needs in the current document. "
                f"Matching needs: {need_id}.",
                location,
            )
        # Sphinx-Needs reports unknown IDs when it applies the directive.
        return []

    else:
        need_filter = needextend["filter"]

        # The local Needs enforce document scope. This check enforces the authoring
        # convention that filters explicitly include c.this_doc().
        if "c.this_doc()" not in need_filter:
            _warn(
                "needextend in S-CORE must always be used per document only. "
                "Please add 'c.this_doc()' to the needextend to limit its effects to the correct document. "
                "See https://eclipse-score.github.io/docs-as-code/main/how-to/write_docs.html#needextend for more information.",
                location,
            )

        try:
            return filter_needs_mutable(
                local_needs,
                needs_config,
                need_filter,
                location=location,
                origin_docname=location[0],
            )
        except Exception as e:
            _warn(f"Invalid filter {need_filter!r}: {e}", location)
            return []


def _validate_list_modifications(
    need: NeedItem,
    needextend: NeedsExtendType,
    location: NeedextendLocation,
) -> None:
    """Warn about destructive changes to link lists that would erase traceability."""
    for _, action, value in needextend["list_modifications"]:
        replaces_or_deletes_links = action in {
            ExtendType.REPLACE,
            ExtendType.DELETE,
        } and isinstance(value, LinksLiteralValue | LinksFunctionArray)
        if replaces_or_deletes_links:
            _warn(
                f"Error when extending need: {need['id']}. "
                "Replace or Delete action is not allowed via needextends.",
                location,
            )


def _validate_field_modifications(
    need: NeedItem,
    needextend: NeedsExtendType,
    location: NeedextendLocation,
) -> None:
    """Warn about field changes that discard data or append to scalar fields."""
    for option_name, action, value in needextend["modifications"]:
        is_scalar_append = (
            action == ExtendType.APPEND
            and isinstance(value, FieldLiteralValue)
            and isinstance(value.value, str)
        )
        is_supported_replacement = action == ExtendType.REPLACE and (
            value is None or isinstance(value, FieldLiteralValue | FieldFunctionArray)
        )

        if action == ExtendType.DELETE:
            _warn(
                f"Error when extending need: {need['id']}. "
                "Delete action is not allowed via needextends.",
                location,
            )
        elif is_scalar_append:
            _warn(
                f"Error when extending need: {need['id']}. "
                "Append action is not allowed via needextends on 'string type options'.",
                location,
            )
        elif is_supported_replacement and need[option_name]:
            _warn(
                f"Error when extending need: {need['id']}. "
                "Replacing of options that are already set is not allowed via needextends.",
                location,
            )


def _ensure_non_destructive_changes(
    need: NeedItem,
    needextend: NeedsExtendType,
    location: NeedextendLocation,
) -> None:
    """Warn about changes that violate SCORE's needextend policy."""
    if need["is_external"]:
        _warn(
            f"Error when extending need: {need['id']}. "
            "It is not allowed to modify external needs via needextend",
            location,
        )
    _validate_list_modifications(need, needextend, location)
    _validate_field_modifications(need, needextend, location)


@dataclass
class _NeedsAndExtends:
    needextends: dict[str, NeedsExtendType] = field(default_factory=dict)
    needs: NeedsMutable = field(default_factory=lambda: NeedsMutable({}))


# Keyed by the Sphinx source document name.
_DocumentToNeedsAndExtends = dict[str, _NeedsAndExtends]


def _group_needs_and_extends_by_document(
    all_needs: NeedsMutable, needextends: dict[str, NeedsExtendType]
) -> _DocumentToNeedsAndExtends:
    """Build the local candidate maps shared by validation and application.

    Sphinx-Needs 8.5 stores mutable Needs by ID. Its filter walks every Need
    it receives, even for c.this_doc(). Indexing by docname once lets every
    directive scan only the Needs in its own document.
    """
    by_docname: _DocumentToNeedsAndExtends = defaultdict(_NeedsAndExtends)
    # Start with directives because only those documents will request a
    # candidate map. This also gives directives in a document without Needs
    # an empty map, so they still go through validation and application.
    for needextend_id, needextend in needextends.items():
        by_docname[needextend["docname"]].needextends[needextend_id] = needextend

    # The ID map does not tell us which Needs belong to a document, so read
    # each Need's source docname once. c.this_doc() uses that same source.
    for need_id, need in all_needs.items():
        docname = need.source.dict_repr.get("docname")
        if docname is not None and docname in by_docname:
            # Share the original Need object. Sphinx-Needs applies updates in
            # place, so later filters and the full graph must see those updates.
            by_docname[docname].needs[need_id] = need

    # Parallel reads can change insertion order. Sort for stable diagnostics.
    return dict(sorted(by_docname.items()))


def score_extend_needs_data_func(
    all_needs: NeedsMutable,
    extends: dict[str, NeedsExtendType],
    needs_config: NeedsSphinxConfig,
):
    """Validate SCORE's needextend policy, then let Sphinx-Needs apply it.

    This wrapper intentionally only reports violations. The unmodified directives
    are still passed to Sphinx-Needs so its normal processing and diagnostics remain
    authoritative.
    """

    if not extends:
        return

    by_docname = _group_needs_and_extends_by_document(all_needs, extends)

    # Give both passes the same local map so they enforce the same scope and
    # both avoid scanning the full graph. Preserve source order for diagnostics
    # and for directives that depend on earlier changes.
    for document_data in by_docname.values():
        # Sphinx-Needs applies extensions in source order as well. Matching that order
        # keeps warning output stable and mirrors the later application order.
        ordered_extends = sorted(document_data.needextends.values(), key=_location)

        for needextend in ordered_extends:
            target_needs = _resolve_needextend_targets(
                document_data.needs, all_needs, needextend, needs_config
            )
            for need in target_needs:
                _ensure_non_destructive_changes(need, needextend, _location(needextend))
        original_function(document_data.needs, document_data.needextends, needs_config)


sphinx_needs.directives.need.extend_needs_data = score_extend_needs_data_func
