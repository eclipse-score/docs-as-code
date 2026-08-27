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

import re
from collections.abc import Callable, Sequence
from typing import Any, ClassVar, Final

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

#: Explicit section headings; the only option that does not reach the Need.
TITLES_OPTION: Final = "titles"

#: ``.. _<report id>__<slug>:`` -- the targets the template emits.
TARGET_RE = re.compile(r"^\.\. _(\S+):$", re.MULTILINE)


class ModuleVerificationReportDirective(SphinxDirective):
    """Emit one ``mod_ver_report`` Need plus a flat list of real sections."""

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = True
    # Any option is accepted and forwarded to the Need. The metamodel decides
    # which options are mandatory, which are links and what they may target.
    # Annotated with docutils' own type: ``Directive.option_spec`` is a mutable
    # class variable, so a narrower type here is an invalid override.
    option_spec: ClassVar[dict[str, Callable[[str], Any]] | None] = DummyOptionSpec()

    options: dict[str, str | None]

    def _warn(self, message: str, subtype: str = "report") -> None:
        logger.warning(
            f"{REPORT_TYPE}: {message}",
            location=self.get_location(),
            type=REPORT_TYPE,
            subtype=subtype,
        )

    def _ids(self, option: str) -> list[str]:
        ids, warnings = rendering.parse_ids(self.options.get(option))
        for message in warnings:
            self._warn(message, option)
        return ids

    def run(self) -> Sequence[nodes.Node]:
        options = dict(self.options)
        titles_raw = options.pop(TITLES_OPTION, None)

        report_id = (options.get("id") or "").strip()
        try:
            rendering.quote_for_filter(report_id)
        except ValueError:
            self._warn(
                f"missing or unusable ':id:' ({report_id!r}); nothing rendered", "id"
            )
            return []

        component_ids = self._ids("covers")
        module_id = next(iter(self._ids("belongs_to")), "")

        titles, warnings = rendering.parse_titles(titles_raw)
        for message in warnings:
            self._warn(message, TITLES_OPTION)
        for unknown in sorted(set(titles) - set(component_ids)):
            self._warn(
                f"title for {unknown!r}, which is not in ':covers:'", TITLES_OPTION
            )

        text = rendering.render_need(
            REPORT_NEED_DIRECTIVE,
            self.arguments[0].strip(),
            options,
            list(self.content),
        )
        text += "\n" + rendering.render_report(
            {
                "report_id": report_id,
                "module_id": module_id,
                "module_slug": rendering.derive_slug(module_id, ""),
                "feature_id": rendering.derive_feature_id(module_id),
                "components": [
                    {
                        "id": component_id,
                        "title": titles.get(component_id)
                        or rendering.derive_title(component_id),
                        "slug": rendering.derive_slug(component_id, module_id),
                    }
                    for component_id in component_ids
                ],
            },
            self.config.needs_template_folder or None,
        )

        parsed = self.parse_text_to_nodes(text, allow_section_headings=True)
        _promote_report_anchors(
            parsed, _emitted_anchors(text, report_id), self.state.document
        )
        return parsed


def _emitted_anchors(text: str, report_id: str) -> set[str]:
    """The section targets the template emitted, as docutils will id them.

    Scanning the rendered text rather than duplicating the section list in
    Python keeps the template the single owner of the report's structure.
    """
    prefix = f"{report_id}__"
    return {
        nodes.make_id(name)
        for name in TARGET_RE.findall(text)
        if name.startswith(prefix)
    }


def _promote_report_anchors(
    parsed: Sequence[nodes.Node], wanted: set[str], document: nodes.document
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
