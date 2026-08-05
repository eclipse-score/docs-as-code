# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
import json
from pathlib import Path
from types import SimpleNamespace
from typing import cast

from score_cross_module_compatibility import (
    MANDATORY_ATTRIBUTE,
    MANDATORY_LINK,
    VERSION_MISMATCH,
    CompatibilityReporter,
    classify_version_conditions,
    get_reporter,
    setup,
)
from sphinx.application import Sphinx
from sphinx_needs.need_item import NeedItem, NeedLink


class FakeNeed(dict[str, object]):
    def iter_links_items(self, *, as_str: bool = False):
        assert not as_str
        yield "links", self["links"]


class FakeSphinx:
    def __init__(self, allow_version_mismatches: bool):
        self.config = SimpleNamespace(
            score_cross_module_compatibility_allow_version_mismatches=allow_version_mismatches
        )
        self.connections: list[tuple[str, object]] = []

    def add_config_value(self, name: str, default: object, rebuild: str) -> None:
        if not hasattr(self.config, name):
            setattr(self.config, name, default)

    def connect(self, event: str, handler: object) -> None:
        self.connections.append((event, handler))


def _classify(app: SimpleNamespace, needs: dict[str, FakeNeed]) -> None:
    classify_version_conditions(cast(Sphinx, app), cast(dict[str, NeedItem], needs))


def _links(need: FakeNeed) -> list[NeedLink]:
    return cast(list[NeedLink], need["links"])


def test_reporter_records_external_owner_and_writes_report(tmp_path: Path) -> None:
    manifest = tmp_path / "mounts.json"
    manifest.write_text(
        json.dumps(
            {
                "mounts": [
                    {"mount_at": "process", "external": True, "repository": "process+"}
                ]
            }
        )
    )
    reporter = CompatibilityReporter.from_manifest(
        manifest, frozenset({VERSION_MISMATCH})
    )
    origin = {"id": "req__consumer", "docname": "index"}
    target = {"id": "req__producer", "docname": "process/index"}

    assert reporter.record(
        origin, VERSION_MISMATCH, "version differs", "index.rst:12", target=target
    )
    reporter.write(tmp_path)

    document = json.loads((tmp_path / "compatibility-findings.json").read_text())
    assert document["summary"] == {"count": 1, "modules": 1}
    assert document["findings"][0]["target_id"] == "req__producer"


def test_setup_skips_version_precheck_when_version_compatibility_is_disabled() -> None:
    app = FakeSphinx(allow_version_mismatches=False)

    setup(app)  # type: ignore[arg-type]

    assert {event for event, _ in app.connections} == {"build-finished"}


def test_setup_registers_version_precheck_when_version_compatibility_is_enabled() -> (
    None
):
    app = FakeSphinx(allow_version_mismatches=True)

    setup(app)  # type: ignore[arg-type]

    assert (
        "needs-before-post-processing",
        classify_version_conditions,
    ) in app.connections
    assert {event for event, _ in app.connections} == {
        "needs-before-post-processing",
        "html-page-context",
        "build-finished",
    }


def test_setup_registers_reporting_hooks_for_non_version_compatibility() -> None:
    app = FakeSphinx(allow_version_mismatches=False)
    app.config.score_cross_module_compatibility_allow_missing_mandatory_attributes = (
        True
    )

    setup(app)  # type: ignore[arg-type]

    assert (
        "needs-before-post-processing",
        classify_version_conditions,
    ) not in app.connections
    assert {event for event, _ in app.connections} == {
        "html-page-context",
        "build-finished",
    }


def test_reporter_requires_each_category_to_be_enabled(tmp_path: Path) -> None:
    manifest = tmp_path / "mounts.json"
    manifest.write_text(
        json.dumps(
            {
                "mounts": [
                    {"mount_at": "process", "external": True, "repository": "process+"}
                ]
            }
        )
    )
    reporter = CompatibilityReporter.from_manifest(
        manifest, frozenset({MANDATORY_ATTRIBUTE})
    )
    need = {"id": "req__producer", "docname": "process/index"}

    assert reporter.record(
        need, MANDATORY_ATTRIBUTE, "missing attribute", "process/index.rst:12"
    )
    assert not reporter.record(
        need, MANDATORY_LINK, "missing link", "process/index.rst:12"
    )
    assert not reporter.record(
        need, VERSION_MISMATCH, "version differs", "process/index.rst:12"
    )


def test_reporter_recognizes_an_external_bundle_mounted_at_the_root(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "mounts.json"
    manifest.write_text(
        json.dumps(
            {
                "mounts": [
                    {"mount_at": "", "external": True, "repository": "root+"},
                    {
                        "mount_at": "process",
                        "external": True,
                        "repository": "process+",
                    },
                ]
            }
        )
    )
    reporter = CompatibilityReporter.from_manifest(
        manifest, frozenset({MANDATORY_ATTRIBUTE})
    )

    assert reporter.module_for_need({"docname": "index"}) == "root+"
    assert reporter.module_for_need({"docname": "other/page"}) == "root+"
    assert reporter.module_for_need({"docname": "process/index"}) == "process+"


def test_cross_module_version_condition_is_reported_and_neutralized(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "mounts.json"
    manifest.write_text(
        json.dumps(
            {
                "mounts": [
                    {"mount_at": "process", "external": True, "repository": "process+"}
                ]
            }
        )
    )
    app = SimpleNamespace(
        config=SimpleNamespace(
            mounts_manifest=str(manifest),
            score_cross_module_compatibility_allow_version_mismatches=True,
        )
    )
    origin = FakeNeed(
        id="req__consumer",
        docname="index",
        doctype=".rst",
        lineno=12,
        links=[NeedLink(id="req__producer", condition="version==1")],
    )
    target = FakeNeed(
        id="req__producer", docname="process/index", version="2", links=[]
    )

    _classify(app, {"req__consumer": origin, "req__producer": target})

    assert _links(origin)[0].condition is None
    assert len(get_reporter(cast(Sphinx, app)).findings) == 1


def test_local_version_condition_remains_strict(tmp_path: Path) -> None:
    app = SimpleNamespace(config=SimpleNamespace(mounts_manifest=""))
    origin = FakeNeed(
        id="req__one",
        docname="index",
        links=[NeedLink(id="req__two", condition="version == 1")],
    )
    target = FakeNeed(id="req__two", docname="other", version="2", links=[])

    _classify(app, {"req__one": origin, "req__two": target})

    assert _links(origin)[0].condition == "version == 1"


def test_external_version_condition_remains_strict_by_default(tmp_path: Path) -> None:
    manifest = tmp_path / "mounts.json"
    manifest.write_text(
        json.dumps(
            {
                "mounts": [
                    {"mount_at": "process", "external": True, "repository": "process+"}
                ]
            }
        )
    )
    app = SimpleNamespace(config=SimpleNamespace(mounts_manifest=str(manifest)))
    origin = FakeNeed(
        id="req__consumer",
        docname="index",
        links=[NeedLink(id="req__producer", condition="version == 1")],
    )
    target = FakeNeed(
        id="req__producer", docname="process/index", version="2", links=[]
    )

    _classify(app, {"req__consumer": origin, "req__producer": target})

    assert _links(origin)[0].condition == "version == 1"
