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


def _verify_needs_are_in_document(
    needs: list[NeedItem], location: NeedextendLocation
) -> None:
    """Report selected needs outside the directive's source document.

    Both ID and expression targets resolve to need records. Validating that shared
    representation keeps the document-boundary policy identical for both syntaxes.
    """
    remote_ids = {need["id"] for need in needs if need["docname"] != location[0]}
    if remote_ids:
        _warn(
            "Needextends may only modify needs in the current document. "
            f"Matching needs: {', '.join(sorted(remote_ids))}.",
            location,
        )


def _fetch_needs(
    all_needs: NeedsMutable,
    needextend: NeedsExtendType,
    needs_config: NeedsSphinxConfig,
) -> list[NeedItem]:
    """Resolve either supported target syntax to the needs it selects."""
    location = _location(needextend)

    if needextend["filter_is_id"]:
        # ``.. needextend:: NEED_ID`` has no expression to constrain, so inspect
        # its resolved target in the shared document-boundary check below.
        need_id = needextend["filter"]
        try:
            return [all_needs[need_id]]
        except KeyError:
            _warn(
                f"Provided id {need_id!r} for needextend does not exist.",
                location,
            )
            return []

    else:
        need_filter = needextend["filter"]

        if "c.this_doc()" not in need_filter:
            _warn(
                "needextend in S-CORE must always be used per document only. "
                "Please add 'c.this_doc()' to the needextend to limit its effects to the correct document. "
                "See https://eclipse-score.github.io/docs-as-code/main/how-to/write_docs.html#needextend for more information.",
                location,
            )

        try:
            return filter_needs_mutable(
                all_needs,
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
    """Reject destructive changes to link lists, which would erase traceability."""
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
    """Reject field changes that discard data or append to scalar fields."""
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
    """Apply SCORE's non-destructive extension policy to one selected need."""
    if need["is_external"]:
        _warn(
            f"Error when extending need: {need['id']}. "
            "It is not allowed to modify external needs via needextend",
            location,
        )
    _validate_list_modifications(need, needextend, location)
    _validate_field_modifications(need, needextend, location)


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
    # Sphinx-Needs applies extensions in source order as well. Matching that order
    # keeps warning output stable and mirrors the later application order.
    ordered_extends = sorted(extends.values(), key=_location)

    for needextend in ordered_extends:
        needs = _fetch_needs(all_needs, needextend, needs_config)
        _verify_needs_are_in_document(needs, _location(needextend))

        for n in needs:
            _ensure_non_destructive_changes(n, needextend, _location(needextend))

    return original_function(all_needs, extends, needs_config)


sphinx_needs.directives.need.extend_needs_data = score_extend_needs_data_func
