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
"""Pure rendering helpers for the module verification report.

Everything in here is a *string transformation*.  No function in this module
receives, reads or resolves a Need.  That is deliberate and it is the governing
design rule of this extension:

    The extension emits RST.  It never reads the Need model to compute an
    answer.

Rendering, not resolving.  The emitted RST contains ``needtable`` filters and
``:need:`` references; sphinx-needs resolves those later with its own
semantics, its own external-need handling and its own backlinks.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

# Conservative allow-list for anything that gets interpolated into a
# sphinx-needs filter string.  Filter strings are evaluated as Python by
# sphinx-needs, so a need id is never pasted in unchecked.
NEED_ID_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")

# ``comp__foo[version==1]`` -- a link-version qualifier.  sphinx-needs strips
# these itself on real link fields; we must not silently drop them while
# building sections, because the section would then be built for a component
# the author did not literally write.
VERSION_QUALIFIER_RE = re.compile(r"\[[^\]]*\]$")

_SPLIT_RE = re.compile(r"[,\s]+")

_TEMPLATE_NAME = "mod_ver_report_tiny.need"


def _template_environment() -> Environment:
    """Return the environment for the shared report template.

    The template is a Bazel runfile of this extension.  It is deliberately
    rendered from the explicit directive inputs only; it receives no Sphinx
    environment and no Need model.
    """
    template_folder = Path(__file__).parents[2] / "needs_templates"
    return Environment(
        loader=FileSystemLoader(template_folder),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_report_template(
    *,
    directive_name: str,
    title: str,
    options: dict[str, str | None],
    content: list[str],
    report_id: str,
    module_id: str,
    component_ids: list[str],
    title_overrides: dict[str, str],
    evidence_links: list[str],
    config: Any,
) -> str:
    """Render the report from the shared Jinja template.

    ``components`` is intentionally derived from the directive's declared
    ``:covers:`` list.  Passing Need objects here would turn K into a
    read-phase model traversal and reintroduce the lifecycle problem this
    implementation avoids.
    """
    module_short = module_id.removeprefix("mod__")
    components = [
        {
            "id": component_id,
            "title": title_overrides.get(component_id) or derive_title(component_id),
            "slug": component_id.removeprefix(f"comp__{module_short}_"),
        }
        for component_id in component_ids
    ]
    return (
        _template_environment()
        .get_template(_TEMPLATE_NAME)
        .render(
            report_need_directive=directive_name,
            report_title=title,
            report_options=options,
            report_content=content,
            report_id=report_id,
            module_id=module_id,
            module_short=module_short,
            module_slug=module_short.replace("_", "").lower(),
            feature_id=module_id.replace("mod__", "feat__", 1),
            components=components,
            evidence_filter=" or ".join(
                f"{quote_for_filter(report_id)} in {link}_back"
                for link in evidence_links
            ),
            scope_filter=(
                "id in ["
                + ", ".join(
                    quote_for_filter(component_id) for component_id in component_ids
                )
                + "]"
                if component_ids
                else "False"
            ),
        )
    )


@dataclass
class ComponentList:
    """Result of parsing the ``:covers:`` option."""

    ids: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def quote_for_filter(need_id: str) -> str:
    """Return ``need_id`` as a safely quoted literal for a needs filter string.

    Raises ``ValueError`` for anything that is not a plain need id.  Callers
    turn that into a Sphinx warning; nothing unvalidated ever reaches the
    filter string.
    """
    if not NEED_ID_RE.match(need_id):
        raise ValueError(f"{need_id!r} is not a valid need id")
    # json.dumps gives us a double-quoted, escaped literal that is also valid
    # Python -- belt and braces on top of the allow-list above.
    return json.dumps(need_id)


def parse_component_list(raw: str | None) -> ComponentList:
    """Parse the ``:covers:`` option value into an ordered, de-duplicated list.

    Accepts comma and/or whitespace separated ids across multiple lines.
    Version qualifiers are reported instead of being silently ignored, and
    duplicates are dropped deterministically (first occurrence wins).
    """
    result = ComponentList()
    if not raw:
        return result

    seen: set[str] = set()
    for token in _SPLIT_RE.split(raw.strip()):
        if not token:
            continue
        stripped = VERSION_QUALIFIER_RE.sub("", token)
        if stripped != token:
            result.warnings.append(
                f"ignoring version qualifier on {token!r}; the report section "
                f"is built for {stripped!r}"
            )
        if not NEED_ID_RE.match(stripped):
            result.warnings.append(
                f"{stripped!r} is not a valid need id and is skipped"
            )
            continue
        if stripped in seen:
            result.warnings.append(f"duplicate entry {stripped!r} is listed once")
            continue
        seen.add(stripped)
        result.ids.append(stripped)
    return result


def parse_title_overrides(raw: str | None) -> tuple[dict[str, str], list[str]]:
    """Parse the ``:titles:`` option: one ``<need id> = <heading>`` per line."""
    overrides: dict[str, str] = {}
    warnings: list[str] = []
    if not raw:
        return overrides, warnings
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if "=" not in line:
            warnings.append(
                f"cannot parse title override {line!r}; expected 'id = Title'"
            )
            continue
        need_id, _, title = line.partition("=")
        need_id, title = need_id.strip(), title.strip()
        if not need_id or not title:
            warnings.append(
                f"cannot parse title override {line!r}; expected 'id = Title'"
            )
            continue
        overrides[need_id] = title
    return overrides, warnings


def derive_title(need_id: str) -> str:
    """Fallback used because K cannot access the merged Need model at read time."""
    _, _, tail = need_id.partition("__")
    slug = tail or need_id
    return slug.replace("_", " ").strip().title() or need_id


def anchor(report_id: str, slug: str) -> str:
    """Deterministic, collision-free RST target name.

    Anchors are namespaced by the report id, so two reports on one page never
    collide and docutils never has to disambiguate with an unstable ``-1``
    suffix.
    """
    return f"{report_id}__{slug}".lower()


def _heading(title: str) -> str:
    return f"{title}\n{UNDERLINE * max(len(title), 3)}\n"


def _section(target: str, title: str, body: str) -> str:
    return f".. _{target}:\n\n{_heading(title)}\n{body.rstrip()}\n"


def section_anchors(report_id: str, component_ids: list[str]) -> list[str]:
    """Every RST target name the report emits, in document order.

    The directive uses this to promote the namespaced anchor to be each
    section's *primary* id, so the ToC entry, the HTML element id and the
    ``:ref:`` target all agree and stay stable when two reports on one page
    happen to use the same heading text.
    """
    return [
        anchor(report_id, "feature"),
        anchor(report_id, "verification-scope"),
        anchor(report_id, "components"),
        *(anchor(report_id, component_id) for component_id in component_ids),
        anchor(report_id, "verification-evidence"),
    ]
