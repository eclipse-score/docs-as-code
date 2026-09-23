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

from types import SimpleNamespace
from typing import cast

import pytest
from sphinx.application import Sphinx
from sphinx_needs.data import NeedsInfoType
from sphinx_needs.need_item import NeedItem, NeedItemSourceUnknown, NeedsContent

import src.extensions.score_metamodel.bundle_metadata as bundle_metadata
from src.extensions.score_mounts._resolver import BazelTarget, BundleMetadata


def _need(
    *,
    bazel_target: str = "",
    bazel_type: str = "",
) -> NeedItem:
    """Create a local component Need named ``memory`` for the test bundle."""
    core = cast(
        NeedsInfoType,
        {
            "id": "comp__memory",
            "type": "comp",
            "title": "Memory",
            "status": "open",
            "tags": [],
            "collapse": False,
            "hide": False,
            "layout": None,
            "style": None,
            "external_css": "",
            "type_name": "Component",
            "type_prefix": "comp__",
            "type_color": "",
            "type_style": "",
            "constraints": [],
            "arch": {},
            "sections": (),
            "signature": None,
            "has_dead_links": False,
            "has_forbidden_dead_links": False,
        },
    )
    return NeedItem(
        source=NeedItemSourceUnknown(docname="index"),
        content=NeedsContent(doctype="rst", content="The original content."),
        core=core,
        extras={
            "bazel_target": bazel_target,
            "bazel_type": bazel_type,
        },
        links={},
        _validate=False,
    )


def _bundle() -> BundleMetadata:
    """Create a bundle named ``memory`` with one direct Bazel target."""
    return BundleMetadata(
        label="//:memory",
        name="memory",
        code_targets=(BazelTarget(label="//:memory_core", type="cc_library"),),
    )


def test_multiple_bundle_targets_keep_declaration_order_in_json() -> None:
    """Multiple targets use matching compact JSON arrays in source order."""
    bundle = BundleMetadata(
        label="//:memory",
        name="memory",
        code_targets=(
            BazelTarget(label="//:memory_core", type="cc_library"),
            BazelTarget(label="//:memory_test", type="cc_test"),
        ),
    )

    values = bundle_metadata._encode_target_values(  # pyright: ignore[reportPrivateUsage]
        bundle
    )

    assert values == {
        "bazel_target": '["//:memory_core","//:memory_test"]',
        "bazel_type": '["cc_library","cc_test"]',
    }


def test_matching_updates_need_in_place_and_returns_affected_document(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The ``memory`` bundle adds its target to the local ``comp__memory`` Need."""
    need = _need()
    original_content = need.content

    class FakeNeedsData:
        def __init__(self, _env: object) -> None:
            self.needs = {"comp__memory": need}

        def get_needs_mutable(self):
            return self.needs

        def remove_need(self, _need_id: str) -> None:
            raise AssertionError("matching must not remove the Need")

        def add_need(self, _need: NeedItem) -> None:
            raise AssertionError("matching must not replace the Need")

    monkeypatch.setattr(bundle_metadata, "SphinxNeedsData", FakeNeedsData)
    monkeypatch.setattr(
        bundle_metadata,
        "get_document_bundles",
        lambda _app: {"index": _bundle()},
    )
    app = SimpleNamespace(env=SimpleNamespace(), srcdir=".")

    changed = bundle_metadata.apply_bundle_metadata(cast(Sphinx, app), None)

    assert changed == ["index"]
    assert need.content is original_content
    assert need["bazel_target"] == "//:memory_core"
    assert need["bazel_type"] == "cc_library"


def test_external_bundle_updates_local_need_like_internal_bundle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A mounted external bundle receives metadata through the same path."""
    need = _need()

    class FakeNeedsData:
        def __init__(self, _env: object) -> None:
            self.needs = {"comp__memory": need}

        def get_needs_mutable(self):
            return self.needs

    external_bundle = BundleMetadata(
        label="@@external_repo//:memory",
        name="memory",
        code_targets=_bundle().code_targets,
    )
    monkeypatch.setattr(bundle_metadata, "SphinxNeedsData", FakeNeedsData)
    monkeypatch.setattr(
        bundle_metadata,
        "get_document_bundles",
        lambda _app: {"index": external_bundle},
    )
    app = SimpleNamespace(env=SimpleNamespace(), srcdir=".")

    changed = bundle_metadata.apply_bundle_metadata(cast(Sphinx, app), None)

    assert changed == ["index"]
    assert need["bazel_target"] == "//:memory_core"
    assert need["bazel_type"] == "cc_library"


def test_unchanged_bundle_metadata_does_not_rewrite_the_document(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reapplying unchanged bundle metadata does not rewrite the document."""
    need = _need(
        bazel_target="//:memory_core",
        bazel_type="cc_library",
    )

    class FakeNeedsData:
        def __init__(self, _env: object) -> None:
            self.needs = {"comp__memory": need}

        def get_needs_mutable(self):
            return self.needs

    monkeypatch.setattr(bundle_metadata, "SphinxNeedsData", FakeNeedsData)
    monkeypatch.setattr(
        bundle_metadata,
        "get_document_bundles",
        lambda _app: {"index": _bundle()},
    )
    app = SimpleNamespace(env=SimpleNamespace(), srcdir=".")

    changed = bundle_metadata.apply_bundle_metadata(cast(Sphinx, app), None)

    assert changed == []
    assert need["bazel_target"] == "//:memory_core"
    assert need["bazel_type"] == "cc_library"


def test_bundle_metadata_is_cleared_when_matching_is_lost(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A renamed bundle no longer matches and loses its old metadata."""
    need = _need(
        bazel_target="//:memory_core",
        bazel_type="cc_library",
    )

    class FakeNeedsData:
        def __init__(self, _env: object) -> None:
            self.needs = {"comp__memory": need}

        def get_needs_mutable(self):
            return self.needs

    unmatched_bundle = BundleMetadata(
        label="//:memory",
        name="other",
        code_targets=_bundle().code_targets,
    )
    monkeypatch.setattr(bundle_metadata, "SphinxNeedsData", FakeNeedsData)
    monkeypatch.setattr(
        bundle_metadata,
        "get_document_bundles",
        lambda _app: {"index": unmatched_bundle},
    )
    app = SimpleNamespace(env=SimpleNamespace(), srcdir=".")

    changed = bundle_metadata.apply_bundle_metadata(cast(Sphinx, app), None)

    assert changed == ["index"]
    assert need["bazel_target"] == ""
    assert need["bazel_type"] == ""


def test_current_bundle_metadata_replaces_old_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The current bundle metadata is authoritative for the matching Need."""
    need = _need(bazel_target="//:old", bazel_type="old_type")

    class FakeNeedsData:
        def __init__(self, _env: object) -> None:
            self.needs = {"comp__memory": need}

        def get_needs_mutable(self):
            return self.needs

    monkeypatch.setattr(bundle_metadata, "SphinxNeedsData", FakeNeedsData)
    monkeypatch.setattr(
        bundle_metadata,
        "get_document_bundles",
        lambda _app: {"index": _bundle()},
    )
    app = SimpleNamespace(env=SimpleNamespace(), srcdir=".")

    changed = bundle_metadata.apply_bundle_metadata(cast(Sphinx, app), None)

    assert changed == ["index"]
    assert need["bazel_target"] == "//:memory_core"
    assert need["bazel_type"] == "cc_library"
