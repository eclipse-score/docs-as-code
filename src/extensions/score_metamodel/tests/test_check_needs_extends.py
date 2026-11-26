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

from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, Mock

import pytest
from score_metamodel.checks import check_needs_extends
from score_pytest.attribute_plugin import add_test_properties
from sphinx.testing.util import SphinxTestApp
from sphinx_needs.config import NeedsSphinxConfig
from sphinx_needs.data import NeedsExtendType, NeedsMutable, SphinxNeedsData
from sphinx_needs.need_item import NeedItem, NeedItemSourceUnknown


def _mock_need(need_id: str, docname: str) -> NeedItem:
    """Provide the source and fields used by the needextend checks."""
    need = MagicMock(spec=NeedItem, source=NeedItemSourceUnknown(docname=docname))
    need.__getitem__.side_effect = {
        "id": need_id,
        "docname": docname,
        "is_external": False,
    }.__getitem__
    return need


def _make_needextend(target: str, *, target_is_id: bool) -> NeedsExtendType:
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


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_id_shorthand_warns_for_a_need_in_another_document(
    monkeypatch: pytest.MonkeyPatch,
):
    """Check a direct ID in a document with no Needs of its own.

    SCORE warns that the target belongs to another document and forwards the
    directive with an empty candidate map.
    """
    remote_need = _mock_need("remote-need", "remote")
    all_needs = NeedsMutable({"remote-need": remote_need})
    log_warning_mock = Mock()
    apply_needextends_mock = Mock()
    monkeypatch.setattr(check_needs_extends, "log_warning", log_warning_mock)
    monkeypatch.setattr(
        check_needs_extends, "original_function", apply_needextends_mock
    )

    check_needs_extends.score_extend_needs_data_func(
        all_needs,
        {"needextend-1": _make_needextend("remote-need", target_is_id=True)},
        Mock(spec=NeedsSphinxConfig),
    )

    apply_needextends_mock.assert_called_once()
    candidate_needs, needextends, _ = apply_needextends_mock.call_args.args
    assert not candidate_needs
    assert tuple(needextends) == ("needextend-1",)
    log_warning_mock.assert_called_once()
    assert "Matching needs: remote-need." in log_warning_mock.call_args.args[1]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_both_passes_use_the_document_index(monkeypatch: pytest.MonkeyPatch):
    """Check two filters in a document with one local Need.

    SCORE evaluates both filters against the local Need alone. Application
    receives the same candidate map and both directives.
    """
    local_need = _mock_need("local-need", "local")
    remote_need = _mock_need("remote-need", "remote")
    all_needs = NeedsMutable({"remote-need": remote_need, "local-need": local_need})
    config = Mock(spec=NeedsSphinxConfig)
    needextends = {
        "extend-a": _make_needextend("c.this_doc()", target_is_id=False),
        "extend-b": _make_needextend(
            "docname is not None and c.this_doc()", target_is_id=False
        ),
    }
    filter_needs_mock = Mock(return_value=[])
    apply_needextends_mock = Mock()
    monkeypatch.setattr(check_needs_extends, "filter_needs_mutable", filter_needs_mock)
    monkeypatch.setattr(
        check_needs_extends, "original_function", apply_needextends_mock
    )

    check_needs_extends.score_extend_needs_data_func(all_needs, needextends, config)

    assert [tuple(call.args[0]) for call in filter_needs_mock.call_args_list] == [
        ("local-need",),
        ("local-need",),
    ]
    apply_needextends_mock.assert_called_once_with(
        filter_needs_mock.call_args.args[0], needextends, config
    )


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_local_needextend_can_match_fields_set_by_an_earlier_directive(
    tmp_path: Path,
):
    """Check two successive needextends in a real build with two documents.

    The first filter names the remote Need in an OR branch, but adds a tag only
    to the local Need. The second sees that tag and checks that its `needs`
    collection excludes the remote Need before adding the verification tag.
    """
    (tmp_path / "conf.py").write_text(
        "extensions = ['sphinx_needs']\n", encoding="utf-8"
    )
    (tmp_path / "index.rst").write_text(
        """Local
=====

.. toctree::

   remote

.. req:: Local requirement
   :id: REQ_LOCAL

.. needextend:: c.this_doc() or id == 'REQ_REMOTE'
   :+tags: selected

.. needextend:: c.this_doc() and 'selected' in tags and not any(n['id'] == 'REQ_REMOTE' for n in needs)
   :+tags: verified
""",
        encoding="utf-8",
    )
    (tmp_path / "remote.rst").write_text(
        """Remote
======

.. req:: Remote requirement
   :id: REQ_REMOTE
""",
        encoding="utf-8",
    )
    app = SphinxTestApp(srcdir=tmp_path)
    try:
        app.build()
        needs = SphinxNeedsData(app.env).get_needs_view()
        assert "verified" in needs["REQ_LOCAL"]["tags"]
        assert needs["REQ_REMOTE"]["tags"] == []
        assert not app.warning.getvalue()
    finally:
        app.cleanup()
