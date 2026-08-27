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
"""The ``mod_ver_report`` directive.

Design decisions that are load-bearing and must not be "cleaned up"
-------------------------------------------------------------------

1. **The report body is a sibling of the Need, never its child.**

   Sphinx turns headings into ``section`` nodes exactly once, during the read
   phase.  Sections are what produce anchors, sidebar entries, ``:ref:``
   targets, search-index entries and PDF bookmarks.  After reading, Sphinx
   never looks for headings again.

   sphinx-needs parses Need content with ``match_titles=False``, so a heading
   written inside a ``.need`` template can never become a section.  Therefore
   this directive parses the generated report text with
   ``parse_text_to_nodes(..., allow_section_headings=True)`` and returns the
   resulting nodes *into the surrounding document*.  The generated
   ``mod_ver_report`` Need is the first of those nodes; the sections follow it
   as siblings.

   A reviewer may be tempted to ask for the body to be moved inside the Need
   node so that it renders in the Need's box.  Doing so silently removes every
   section from the document and cannot be spotted by looking at the HTML.
   Do not do it.

2. **The extension emits RST.  It never reads the Need model.**

   The only thing known at read time is *which sections exist*.  Everything
   with semantics -- titles, coverage, backlinks, external needs -- is deferred
   to ``needtable`` filters and ``:need:`` references that sphinx-needs
   resolves after collection.  Consequently this directive needs no
   ``NeedsView``, no lifecycle hook and no model completeness at read time.

   Test for future changes: if new report content needs Python that walks needs
   and computes something, the line has been crossed.  If it needs a new
   ``needtable`` filter in the template, it has not.

3. **Scope is validated by the metamodel, not here.**

   ``:covers:`` is passed through verbatim as a real link field on the Need.
   sphinx-needs validates target existence and type, generates ``covers_back``
   for free, and reports through the normal warning pipeline.  The
   "every component of the module is covered, and vice versa" rule lives in
   ``score_metamodel`` as a graph check.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

from docutils import nodes
from score_module_verification_report import rendering
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective
from sphinx_needs.utils import DummyOptionSpec

logger = logging.getLogger(__name__)

#: Need type / public directive name.
REPORT_TYPE: Final = "mod_ver_report"

#: Internal directive name bound to sphinx-needs' ``NeedDirective`` for
#: ``REPORT_TYPE``.  The public name is taken by this directive, so the
#: generated RST needs an un-shadowed way to actually create the Need.
REPORT_NEED_DIRECTIVE: Final = "mod_ver_report_need"

#: Directive options that steer rendering and must not reach the Need.
PRESENTATION_OPTIONS: Final = ("titles",)


class ModuleVerificationReportDirective(SphinxDirective):
    """Emit one ``mod_ver_report`` Need plus a flat list of real sections."""

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = True
    # Any option is accepted and forwarded to the Need. The metamodel decides
    # which options are mandatory, which are links and what they may target.
    option_spec: Final[DummyOptionSpec] = DummyOptionSpec()

    options: dict[str, str | None]

    def _warn(self, message: str, subtype: str = "report") -> None:
        logger.warning(
            f"{REPORT_TYPE}: {message}",
            location=self.get_location(),
            type=REPORT_TYPE,
            subtype=subtype,
        )

    def run(self) -> Sequence[nodes.Node]:
        options = dict(self.options)
        title = self.arguments[0].strip()

        presentation = {key: options.pop(key, None) for key in PRESENTATION_OPTIONS}

        report_id = (options.get("id") or "").strip()
        if not report_id:
            self._warn("missing mandatory ':id:' option; no report is rendered", "id")
            return []
        try:
            rendering.quote_for_filter(report_id)
        except ValueError:
            self._warn(f"{report_id!r} is not a usable need id", "id")
            return []

        components = rendering.parse_component_list(options.get("covers"))
        for message in components.warnings:
            self._warn(message, "covers")

        title_overrides, title_warnings = rendering.parse_title_overrides(
            presentation["titles"]
        )
        for message in title_warnings:
            self._warn(message, "titles")
        for unknown in sorted(set(title_overrides) - set(components.ids)):
            self._warn(
                f"title override for {unknown!r} which is not listed in ':covers:'",
                "titles",
            )

        text = self._render(title, options, report_id, components.ids, title_overrides)
        parsed = self.parse_text_to_nodes(text, allow_section_headings=True)
        _promote_report_anchors(
            parsed,
            rendering.section_anchors(report_id, components.ids),
            self.state.document,
        )
        return parsed

    def _render(
        self,
        title: str,
        options: dict[str, str | None],
        report_id: str,
        component_ids: list[str],
        title_overrides: dict[str, str],
    ) -> str:
        config = self.config
        parts = [
            rendering.render_need(
                REPORT_NEED_DIRECTIVE, title, options, list(self.content)
            ),
            rendering.render_metadata_section(
                report_id, config.mod_ver_report_metadata_columns
            ),
            rendering.render_scope_section(
                report_id, component_ids, config.mod_ver_report_scope_columns
            ),
        ]
        for component_id in component_ids:
            parts.append(
                rendering.render_component_section(
                    report_id,
                    component_id,
                    title_overrides.get(component_id)
                    or rendering.derive_title(component_id),
                    config.mod_ver_report_component_filter,
                    config.mod_ver_report_component_columns,
                )
            )

        evidence_links = self._configured_evidence_links()
        if evidence_links:
            parts.append(
                rendering.render_evidence_section(
                    report_id, evidence_links, config.mod_ver_report_evidence_columns
                )
            )
        return "\n".join(parts)

    def _configured_evidence_links(self) -> list[str]:
        """Keep only evidence links that are actually configured link fields.

        This reads ``needs_extra_links`` -- configuration, not the Need model --
        so that a project that does not define ``contains``/``evidence`` gets no
        section instead of a broken filter.
        """
        known = {
            link["option"]
            for link in self.config.needs_extra_links
            if isinstance(link, dict) and "option" in link
        }
        return [
            link for link in self.config.mod_ver_report_evidence_links if link in known
        ]


def _promote_report_anchors(
    parsed: Sequence[nodes.Node], anchors: list[str], document: nodes.document
) -> None:
    """Make the namespaced anchor each generated section's *primary* id.

    ``.. _name:`` in front of a heading gives the section a second id, but
    docutils only merges it during the ``PropagateTargets`` transform and then
    appends it, so ``section["ids"][0]`` stays the id docutils derived from the
    heading text.  That id is what Sphinx uses for the ToC entry and the HTML
    element, and it is neither namespaced nor stable: two reports with the same
    heading text on one page make docutils disambiguate with a ``-1`` suffix.

    So the merge is done here instead, at read time, in document order.  Ids
    and names are moved -- not copied -- from the target onto the section, and
    the document's id/name maps are repointed accordingly.  Nothing is
    invented: these are exactly the ids docutils created from the targets the
    report emitted.
    """
    wanted = {nodes.make_id(name) for name in anchors}
    pending: nodes.target | None = None

    # ``parsed`` is the parser's own children list: removing a top-level
    # target below mutates it, so iterate over a snapshot.
    for root in list(parsed):
        for node in root.findall(include_self=True):
            if isinstance(node, nodes.target):
                if not _is_plain_target(node):
                    continue
                if wanted.intersection(node["ids"]):
                    pending = node
            elif isinstance(node, nodes.section) and pending is not None:
                _merge_target_into_section(pending, node, document)
                pending = None


def _is_plain_target(target: nodes.target) -> bool:
    """True for ``.. _name:`` targets that have not been resolved yet."""
    return not any(target.get(key) for key in ("refid", "refuri", "refname"))


def _merge_target_into_section(
    target: nodes.target, section: nodes.section, document: nodes.document
) -> None:
    ids = list(target["ids"])
    names = list(target["names"])

    section["ids"] = ids + [i for i in section["ids"] if i not in ids]
    section["names"] = names + [n for n in section["names"] if n not in names]

    for id_ in ids:
        document.ids[id_] = section
    for name in names:
        document.nameids[name] = ids[0]

    # Emptied so that docutils' PropagateTargets transform does not merge the
    # same ids a second time; removed so no stray anchor is left behind.
    target["ids"] = []
    target["names"] = []
    if target.parent is not None:
        target.parent.remove(target)
