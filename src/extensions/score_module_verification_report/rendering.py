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

# Section headings emitted by the report all use the same underline character.
# ``parse_text_to_nodes(allow_section_headings=True)`` parses the generated text
# in a *fresh title-style context*, so a single character makes every generated
# heading a sibling of every other one -- a flat list, exactly one level below
# wherever the directive was placed.  See the module docstring of ``directive``.
UNDERLINE = "+"

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
    """Last-resort heading text for a component without an explicit override.

    This is intentionally dumb.  The *real* title lives on the Need and is
    rendered by the ``:need:`` reference inside the section -- resolved by
    sphinx-needs, not by us.  ``comp__baselibs_json`` becoming "Baselibs Json"
    is an accepted fallback, not the intended output; authors who care pass
    ``:titles:``.
    """
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
        anchor(report_id, "report-metadata"),
        anchor(report_id, "verification-scope"),
        *(anchor(report_id, component_id) for component_id in component_ids),
        anchor(report_id, "verification-evidence"),
    ]


def _needtable(filter_expr: str, columns: str) -> str:
    return (
        ".. needtable::\n"
        f"   :filter: {filter_expr}\n"
        f"   :columns: {columns}\n"
        "   :style: table\n"
    )


def render_need(
    directive_name: str,
    title: str,
    options: dict[str, str | None],
    content: list[str],
) -> str:
    """Render the ``mod_ver_report`` Need itself.

    Options are passed through verbatim: the metamodel -- not this extension --
    decides which of them are mandatory, which are links and what they may
    point at.
    """
    lines = [f".. {directive_name}:: {title}"]
    for key, value in options.items():
        lines.append(f"   :{key}: {'' if value is None else value}")
    if content:
        lines.append("")
        lines.extend(f"   {line}" if line else "" for line in content)
    return "\n".join(lines) + "\n"


def render_metadata_section(report_id: str, columns: str) -> str:
    return _section(
        anchor(report_id, "report-metadata"),
        "Report Metadata",
        _needtable(f"id == {quote_for_filter(report_id)}", columns),
    )


def render_scope_section(report_id: str, component_ids: list[str], columns: str) -> str:
    quoted = ", ".join(quote_for_filter(c) for c in component_ids)
    if quoted:
        filter_expr = f"id in [{quoted}]"
        body = _needtable(filter_expr, columns)
    else:
        body = "This report does not declare any covered components.\n"
    return _section(anchor(report_id, "verification-scope"), "Verification Scope", body)


def render_component_section(
    report_id: str,
    component_id: str,
    title: str,
    filter_template: str,
    columns: str,
) -> str:
    quoted = quote_for_filter(component_id)
    body = f":need:`{component_id}`\n\n" + _needtable(
        filter_template.format(component_id=quoted), columns
    )
    return _section(anchor(report_id, component_id), title, body)


def render_evidence_section(
    report_id: str, evidence_links: list[str], columns: str
) -> str:
    quoted = quote_for_filter(report_id)
    clauses = [f"{quoted} in {link}_back" for link in evidence_links]
    return _section(
        anchor(report_id, "verification-evidence"),
        "Verification Evidence",
        _needtable(" or ".join(clauses), columns),
    )
