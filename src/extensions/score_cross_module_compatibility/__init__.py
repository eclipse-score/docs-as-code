# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Compatibility reporting at documentation-module boundaries.

The metamodel defines valid needs.  This extension owns the separate policy for
integrating independently released documentation modules.
"""

from __future__ import annotations

import html
import json
import os
import re
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, cast

from sphinx.application import Sphinx
from sphinx.util import logging
from sphinx_needs.need_item import NeedItem

from src.helper_lib import find_ws_root, get_runfiles_dir

_VERSION_CONDITION = re.compile(r"^\s*version\s*==\s*(\d+)\s*$")
logger = logging.getLogger(__name__)

MANDATORY_ATTRIBUTE = "mandatory-attribute"
MANDATORY_LINK = "mandatory-link"
VERSION_MISMATCH = "version-mismatch"

_CONFIG_BY_CATEGORY = {
    MANDATORY_ATTRIBUTE: "score_cross_module_compatibility_allow_missing_mandatory_attributes",
    MANDATORY_LINK: "score_cross_module_compatibility_allow_missing_mandatory_links",
    VERSION_MISMATCH: "score_cross_module_compatibility_allow_version_mismatches",
}


@dataclass(frozen=True)
class ExternalMount:
    mount_at: str
    module: str


@dataclass(frozen=True)
class CompatibilityFinding:
    module: str
    need_id: str
    source: str
    category: str
    message: str
    target_id: str = ""
    target_module: str = ""


class CompatibilityReporter:
    """Collect compatibility findings and identify needs owned by external modules."""

    def __init__(
        self,
        mounts: list[ExternalMount],
        enabled_categories: frozenset[str] = frozenset(),
    ):
        self._mounts = mounts
        self._enabled_categories = enabled_categories
        self._findings: dict[CompatibilityFinding, None] = {}

    @classmethod
    def from_manifest(
        cls,
        manifest_path: str | Path | None,
        enabled_categories: frozenset[str] = frozenset(),
    ) -> CompatibilityReporter:
        if not manifest_path:
            return cls([], enabled_categories)
        try:
            raw: dict[str, object] = json.loads(
                Path(manifest_path).read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            return cls([], enabled_categories)
        entries = raw.get("mounts", [])
        if not isinstance(entries, list):
            return cls([], enabled_categories)
        mounts: list[ExternalMount] = []
        for entry in cast("list[object]", entries):
            if not isinstance(entry, dict):
                continue
            fields = cast("dict[str, object]", entry)
            if not fields.get("external"):
                continue
            mount_at = fields.get("mount_at")
            if not isinstance(mount_at, str):
                continue
            repository = fields.get("repository", "external")
            mounts.append(ExternalMount(mount_at.strip("/"), str(repository)))
        return cls(mounts, enabled_categories)

    def module_for_need(self, need: NeedItem | dict[str, Any]) -> str | None:
        if bool(need.get("is_external", False)):
            # Imported needs.json entries are external even when their source
            # directory is unavailable in this build.  The URL is stable enough
            # for the report; use it as a conservative module identifier.
            url = need.get("external_url")
            return str(url) if url else "external-needs"
        docname = need.get("docname")
        if not isinstance(docname, str):
            return None
        normalized = docname.strip("/")
        candidates = [
            mount
            for mount in self._mounts
            if not mount.mount_at
            or normalized == mount.mount_at
            or normalized.startswith(mount.mount_at + "/")
        ]
        return (
            max(candidates, key=lambda mount: len(mount.mount_at)).module
            if candidates
            else None
        )

    def record(
        self,
        need: NeedItem | dict[str, Any],
        category: str,
        message: str,
        source: str,
        *,
        target: NeedItem | dict[str, Any] | None = None,
    ) -> bool:
        if category not in self._enabled_categories:
            return False
        module = self.module_for_need(need)
        target_module = self.module_for_need(target) if target is not None else None
        owner = module or target_module
        if owner is None:
            return False
        finding = CompatibilityFinding(
            owner,
            str(need.get("id", "")),
            source,
            category,
            message,
            str(target.get("id", "")) if target is not None else "",
            target_module or "",
        )
        if finding in self._findings:
            return True
        self._findings[finding] = None
        logger.info(
            "Compatibility finding: module=%s need=%s source=%s category=%s%s: %s",
            owner,
            need.get("id", ""),
            source,
            category,
            f" target={target.get('id', '')}" if target is not None else "",
            message,
        )
        return True

    @property
    def findings(self) -> list[CompatibilityFinding]:
        return sorted(
            self._findings,
            key=lambda item: (item.module, item.need_id, item.target_id, item.message),
        )

    def document(self) -> dict[str, object]:
        findings = self.findings
        return {
            "summary": {
                "count": len(findings),
                "modules": len({item.module for item in findings}),
            },
            "findings": [asdict(item) for item in findings],
        }

    def write(self, outdir: str | Path) -> None:
        outdir_path = Path(outdir)
        outdir_path.joinpath("compatibility-findings.json").write_text(
            json.dumps(self.document(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        groups: dict[str, list[CompatibilityFinding]] = {}
        for finding in self.findings:
            groups.setdefault(finding.module, []).append(finding)
        sections = (
            "".join(
                "<section><h2>"
                + html.escape(module)
                + "</h2><ul>"
                + "".join(
                    "<li><strong>"
                    + html.escape(item.need_id)
                    + "</strong>"
                    + (" → " + html.escape(item.target_id) if item.target_id else "")
                    + " ("
                    + html.escape(item.category)
                    + "): "
                    + html.escape(item.message)
                    + "</li>"
                    for item in items
                )
                + "</ul></section>"
                for module, items in groups.items()
            )
            or "<p>No compatibility findings.</p>"
        )
        outdir_path.joinpath("compatibility-findings.html").write_text(
            '<!doctype html><html><head><meta charset="utf-8"><title>Compatibility findings</title>'
            "</head><body><h1>Compatibility findings</h1>"
            + sections
            + "</body></html>\n",
            encoding="utf-8",
        )


def _manifest_path(app: Sphinx) -> Path | None:
    raw = getattr(app.config, "mounts_manifest", "") or os.environ.get(
        "MOUNTS_MANIFEST", ""
    )
    if not isinstance(raw, str) or not raw.strip():
        return None
    direct = Path(raw)
    runfiles = get_runfiles_dir() / raw
    # ``mounts_manifest`` may be an execroot path, while the environment value
    # passed to ``bazel run`` is runfiles-relative.  Prefer an existing path so
    # the policy does not depend on the current working directory.
    if direct.is_file():
        return direct
    if runfiles.is_file():
        return runfiles
    return runfiles if find_ws_root() else direct


def get_reporter(app: Sphinx) -> CompatibilityReporter:
    reporter = getattr(app, "_score_compatibility_reporter", None)
    if not isinstance(reporter, CompatibilityReporter):
        enabled_categories = frozenset(
            category
            for category, config_name in _CONFIG_BY_CATEGORY.items()
            if bool(getattr(app.config, config_name, False))
        )
        reporter = CompatibilityReporter.from_manifest(
            _manifest_path(app), enabled_categories
        )
        app._score_compatibility_reporter = reporter  # pyright: ignore[reportAttributeAccessIssue]
    return reporter


def _need_location(need: NeedItem) -> str:
    return (
        f"{need.get('docname', '')}{need.get('doctype', '')}:{need.get('lineno', '')}"
    )


def classify_version_conditions(app: Sphinx, needs: dict[str, NeedItem]) -> None:
    """Downgrade only eligible cross-module exact-version link mismatches.

    This event runs immediately before Sphinx-Needs resolves conditions. A
    classified condition is removed after being recorded, so its normal
    backlink and rendered relationship remain available without a fatal
    Sphinx-Needs warning. All other conditions remain untouched.
    """
    reporter = get_reporter(app)
    for need in needs.values():
        for _, links in need.iter_links_items(as_str=False):
            for index, link in enumerate(links):
                match = _VERSION_CONDITION.fullmatch(link.condition or "")
                target = needs.get(link.id)
                if match is None or target is None:
                    continue
                expected = match.group(1)
                actual = str(target.get("version", ""))
                if actual == expected or not reporter.record(
                    need,
                    VERSION_MISMATCH,
                    f"requires target version {expected}, but target is version {actual or 'unset'}",
                    _need_location(need),
                    target=target,
                ):
                    continue
                links[index] = replace(link, condition=None)


def _inject_notice(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: dict[str, object],
    doctree: object,
) -> None:
    if pagename != "index":
        return
    findings = get_reporter(app).findings
    body = context.get("body")
    if findings and isinstance(body, str):
        context["body"] = (
            '<div class="admonition warning"><p class="admonition-title">'
            "External documentation compatibility findings</p><p>"
            f"{len(findings)} finding(s) require review; "
            '<a href="compatibility-findings.html">open the report</a>.</p></div>'
            + body
        )


def _write_report(app: Sphinx, exception: Exception | None) -> None:
    if exception is None:
        get_reporter(app).write(app.outdir)


def setup(app: Sphinx) -> dict[str, object]:
    for config_name in _CONFIG_BY_CATEGORY.values():
        app.add_config_value(config_name, False, rebuild="env")

    if app.config.score_cross_module_compatibility_allow_version_mismatches:
        app.connect("needs-before-post-processing", classify_version_conditions)

    if any(
        bool(getattr(app.config, config_name))
        for config_name in _CONFIG_BY_CATEGORY.values()
    ):
        app.connect("html-page-context", _inject_notice)

    app.connect("build-finished", _write_report)

    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
