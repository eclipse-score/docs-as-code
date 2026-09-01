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

from typing import cast
from unittest.mock import Mock

import pytest
from score_metamodel.checks import check_needs_extends
from sphinx_needs.data import NeedsExtendType, NeedsMutable
from sphinx_needs.need_item import NeedItem

# TODO(#688): Replace these mocked tests with multi-file RST tests once the
# RST runner can build complete cross-document test cases.
CROSS_DOCUMENT_WARNING = (
    "Needextends may only modify needs in the current document. "
    "Matching needs: remote-need."
)


def _need(need_id: str, document: str) -> NeedItem:
    """Create the minimal need record used by the location check."""
    return cast(
        NeedItem,
        {"id": need_id, "docname": document, "is_external": False},
    )


def _needextend(target: str, *, target_is_id: bool) -> NeedsExtendType:
    """Create a needextend with no modifications; only target resolution matters."""
    return cast(
        NeedsExtendType,
        {
            "docname": "local",
            "lineno": 1,
            "filter": target,
            "filter_is_id": target_is_id,
            "strict": False,
            "list_modifications": [],
            "modifications": [],
        },
    )


def _run_check(
    monkeypatch: pytest.MonkeyPatch,
    all_needs: NeedsMutable,
    needextend: NeedsExtendType,
    *,
    filter_matches: list[NeedItem] | None = None,
) -> tuple[Mock, Mock]:
    """Run the wrapper with isolated Sphinx-Needs dependencies."""
    warnings = Mock()
    original_function = Mock()
    monkeypatch.setattr(check_needs_extends, "log_warning", warnings)
    monkeypatch.setattr(check_needs_extends, "original_function", original_function)
    if filter_matches is not None:
        monkeypatch.setattr(
            check_needs_extends,
            "filter_needs_mutable",
            Mock(return_value=filter_matches),
        )

    check_needs_extends.score_extend_needs_data_func(
        all_needs, {"needextend-1": needextend}, Mock()
    )
    return original_function, warnings


def _assert_cross_document_warning(warnings: Mock) -> None:
    messages = [call.args[1] for call in warnings.call_args_list]
    assert CROSS_DOCUMENT_WARNING in messages


def test_filter_reports_cross_document_or_match_without_changing_directive(
    monkeypatch: pytest.MonkeyPatch,
):
    local_need = _need("local-need", "local")
    remote_need = _need("remote-need", "remote")
    all_needs = cast(
        NeedsMutable,
        {"local-need": local_need, "remote-need": remote_need},
    )
    needextend = _needextend("c.this_doc() or id == 'remote-need'", target_is_id=False)

    original_function, warnings = _run_check(
        monkeypatch,
        all_needs,
        needextend,
        filter_matches=[local_need, remote_need],
    )

    assert original_function.call_args.args[1]["needextend-1"] is needextend
    _assert_cross_document_warning(warnings)


def test_id_shorthand_reports_cross_document_match(monkeypatch: pytest.MonkeyPatch):
    remote_need = _need("remote-need", "remote")
    all_needs = cast(NeedsMutable, {"remote-need": remote_need})

    _, warnings = _run_check(
        monkeypatch,
        all_needs,
        _needextend("remote-need", target_is_id=True),
    )

    _assert_cross_document_warning(warnings)
