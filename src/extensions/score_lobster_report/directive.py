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
"""Directive that renders a Lobster traceability JSON report as a table."""

import hashlib
import json
import math
from html import escape
from pathlib import Path
from typing import Any

from docutils import nodes
from sphinx.util.docutils import SphinxDirective

from src.extensions.score_source_code_linker.xml_parser import short_hash
from src.helper_lib import find_ws_root

# Colours for the coverage pie charts: "covered" green, "not covered" red.
# Chosen to stay legible on both the light and the dark theme variant.
_COVERED_COLOR = "#2e8b57"
_UNCOVERED_COLOR = "#c0392b"

# Generically-rendered pools that additionally get an explanatory summary
# sentence and a coverage pie chart, mapped to (sentence, chart title).
# Coverage is "item has at least one ``ref_up``", i.e. it traces up to the
# pool above it.
_PIE_INFO = {
    "Architecture": (
        "{covered} / {total} architecture component(s) are covered by at "
        "least one component requirement.",
        "Components covered by at least one component requirement",
    ),
}


def _pie_chart(title: str, segments: list[tuple[str, int, str]]) -> list[nodes.Node]:
    """A small inline-SVG pie chart with a legend, rendered as raw HTML.

    ``segments`` is a list of ``(label, value, colour)``. Everything is
    emitted as a self-contained ``<svg>`` so no plotting library, image
    file or build-time asset generation is needed; non-HTML writers simply
    drop the raw node.
    """
    total = sum(value for _label, value, _colour in segments)
    if total <= 0:
        return []

    size = 160
    radius = size / 2
    center = size / 2

    paths: list[str] = []
    angle = -math.pi / 2  # start at 12 o'clock instead of 3 o'clock
    for label, value, colour in segments:
        if value <= 0:
            continue
        sweep = 2 * math.pi * value / total
        if value == total:
            # A full-circle arc would start and end on the same point and
            # therefore collapse to nothing; draw a plain circle instead.
            paths.append(
                f'<circle cx="{center}" cy="{center}" r="{radius}" '
                f'fill="{colour}"><title>{escape(label)}: {value} '
                f"(100%)</title></circle>"
            )
            continue
        end = angle + sweep
        x0, y0 = center + radius * math.cos(angle), center + radius * math.sin(angle)
        x1, y1 = center + radius * math.cos(end), center + radius * math.sin(end)
        large_arc = 1 if sweep > math.pi else 0
        paths.append(
            f'<path d="M {center:.2f} {center:.2f} L {x0:.2f} {y0:.2f} '
            f"A {radius:.2f} {radius:.2f} 0 {large_arc} 1 {x1:.2f} {y1:.2f} Z\" "
            f'fill="{colour}"><title>{escape(label)}: {value} '
            f"({100 * value / total:.1f}%)</title></path>"
        )
        angle = end

    legend = "".join(
        f'<li style="list-style:none;margin:0 0 0.25em 0">'
        f'<span style="display:inline-block;width:0.8em;height:0.8em;'
        f'margin-right:0.5em;vertical-align:middle;background:{colour}">'
        f"</span>{escape(label)}: {value} ({100 * value / total:.1f}%)</li>"
        for label, value, colour in segments
    )

    html = (
        '<div style="display:flex;align-items:center;justify-content:center;'
        'gap:1.5em;flex-wrap:wrap;margin:1em auto">'
        f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" '
        f'role="img" aria-label="{escape(title)}">'
        f"<title>{escape(title)}</title>{''.join(paths)}</svg>"
        f'<ul style="margin:0;padding:0">{legend}</ul>'
        "</div>"
    )
    return [nodes.raw("", html, format="html")]


def _coverage_pie(title: str, covered: int, total: int) -> list[nodes.Node]:
    return _pie_chart(
        title,
        [
            ("covered", covered, _COVERED_COLOR),
            ("not covered", total - covered, _UNCOVERED_COLOR),
        ],
    )


def _row(cells: list[nodes.Node | str]) -> nodes.row:
    row = nodes.row()
    for cell in cells:
        entry = nodes.entry()
        if isinstance(cell, nodes.Node):
            entry += cell
        else:
            entry += nodes.paragraph(text=str(cell))
        row += entry
    return row


def _table(header: list[str], rows: list[list[nodes.Node | str]]) -> nodes.table:
    table = nodes.table()
    tgroup = nodes.tgroup(cols=len(header))
    table += tgroup
    for _ in header:
        tgroup += nodes.colspec(colwidth=1)
    thead = nodes.thead()
    tgroup += thead
    thead += _row(list(header))
    tbody = nodes.tbody()
    tgroup += tbody
    for row in rows:
        tbody += _row(row)
    return table


def _foldable(summary: str, body: nodes.Node) -> list[nodes.Node]:
    """Wrap ``body`` (typically a table) in a native HTML ``<details>``
    element so long tables can be collapsed away.

    Implemented with raw HTML rather than e.g. sphinx-design's ``dropdown``
    because ``<details>``/``<summary>`` needs no extra CSS or JavaScript and
    keeps the wrapped node a plain docutils table -- non-HTML writers just
    drop the two raw nodes and still render the table.

    The element starts collapsed, so the page opens as a compact overview of
    section headings, summaries and pie charts. Because the report
    cross-links its own rows via ``#lobster-item-...`` anchors, and not every
    browser expands a collapsed ``<details>`` when the fragment target lives
    inside it, ``_ANCHOR_SCRIPT`` re-opens the relevant ones on navigation.
    """
    return [
        nodes.raw(
            "",
            '<details style="margin:1em 0">'
            '<summary style="cursor:pointer;font-weight:bold;'
            f'margin-bottom:0.5em">{escape(summary)}</summary>',
            format="html",
        ),
        body,
        nodes.raw("", "</details>", format="html"),
    ]


# Opens every collapsed <details> on the way to the element the current URL
# fragment points at, then scrolls it into view -- without this, following an
# in-report "#lobster-item-..." link would jump to a row hidden inside a
# folded table. Emitted once per directive instance.
_ANCHOR_SCRIPT = """<script>
(function () {
  function revealHashTarget() {
    var hash = window.location.hash;
    if (!hash || hash.length < 2) { return; }
    var target;
    try { target = document.getElementById(decodeURIComponent(hash.slice(1))); }
    catch (e) { return; }
    if (!target) { return; }
    var opened = false;
    for (var node = target.parentElement; node; node = node.parentElement) {
      if (node.tagName === "DETAILS" && !node.open) {
        node.open = true;
        opened = true;
      }
    }
    if (opened) { target.scrollIntoView(); }
  }
  window.addEventListener("hashchange", revealHashTarget);
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", revealHashTarget);
  } else {
    revealHashTarget();
  }
})();
</script>"""


class LobsterTraceabilityReportDirective(SphinxDirective):
    """Render a Lobster traceability report as one section per pool
    ("level") found in the JSON: Feature Requirements, Component
    Requirements, Unit Test, Architecture, Public API, Failure Modes,
    Control Measures, Root Causes, etc. The requirement chain is rendered
    first and top-down as two cross-linked tables (using ``:need:``
    references): Feature Requirements against the Component Requirements
    refining them, then Component Requirements against the Unit Tests
    verifying them. Every other pool follows, rendered generically
    straight from the JSON (name/text/references/status), with no
    special-casing per pool name.

    Usage::

        .. lobster-traceability-report::
           bazel-bin/score/bitmanipulation/dependable_element_bitmanipulation_index_report.json

    The path is resolved relative to the workspace root, the same way
    ``score_source_code_linker`` locates ``bazel-testlogs``. The referenced
    report is a plain build artifact and must already exist, e.g. via::

        bazel build //score/bitmanipulation:dependable_element_bitmanipulation

    All information rendered here comes exclusively from that JSON file
    (never from any separately-generated Lobster HTML report).
    """

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = False

    def run(self) -> list[nodes.Node]:
        rel_path = self.arguments[0].strip()
        ws_root = find_ws_root()
        if ws_root is None:
            return [self._warning(
                "Could not determine the workspace root; skipping the "
                "Lobster traceability report."
            )]

        report_path = ws_root / rel_path
        if not report_path.exists():
            return [self._warning(
                f"Lobster report not found at '{rel_path}' (resolved to "
                f"'{report_path}'). Build it first, e.g. `bazel build "
                "//score/bitmanipulation:dependable_element_bitmanipulation`, "
                "then re-run the docs build."
            )]

        try:
            report = json.loads(report_path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            return [self._warning(
                f"Failed to read Lobster report '{rel_path}': {exc}"
            )]

        return self._build_nodes(report)

    def _warning(self, text: str) -> nodes.warning:
        return nodes.warning("", nodes.paragraph(text=text))

    def _need_ref(self, need_id: str, display: str | None = None) -> list[nodes.Node]:
        """Parse a ``:need:`<need_id>``` role, so it resolves (at doctree-
        resolved time) into a real link to that need's directive/element,
        exactly like a hand-written ``:need:`` reference elsewhere in the
        docs.

        ``display``, if given, is rendered as explicit link text (RST's
        ``:need:`text <need_id>``` syntax) instead of the default, which
        would otherwise show ``need_id`` itself. Useful when ``need_id`` is
        a generated, machine-friendly id (e.g. ``testcase__Foo__Bar_a1b2c"``)
        whose repeated double underscores read as stacked lines once the
        browser's own link-underline decoration overlaps them - passing the
        original, human-authored name instead avoids that.
        """
        role_text = f"{display} <{need_id}>" if display else need_id
        text_nodes, _messages = self.state.inline_text(
            f":need:`{role_text}`", self.lineno
        )
        return list(text_nodes)

    @staticmethod
    def _strip_version(tag: str) -> str:
        # Some pools reference an item's tag with its "@<version>" suffix
        # (e.g. "req Foo.bar@1"), others reference the same item unversioned
        # ("req Foo.bar"). Normalize away the suffix so both spellings hit
        # the same index entry.
        base, sep, version = tag.rpartition("@")
        return base if sep and version.isdigit() else tag

    @staticmethod
    def _strip_kind_prefix(tag: str) -> str:
        # A tag is "<kind> <qualified name>" (e.g. "req Foo.bar", "gtest
        # Foo:bar", "arch //foo:bar", "fta Foo.bar"); drop the kind for a
        # more readable fallback label.
        _kind, sep, rest = tag.partition(" ")
        return rest if sep else tag

    @staticmethod
    def _anchor_id(tag: str) -> str:
        # A stable, docutils-safe anchor id for cross-linking items *within*
        # this report, independent of any "real" Sphinx-needs id -- mirrors
        # the "lobster-item-<hash>" anchors dependable_element's own
        # traceability_report already generates.
        return "lobster-item-" + hashlib.sha1(tag.encode("utf-8")).hexdigest()

    def _build_tag_index(
        self, levels_list: list[dict[str, Any]]
    ) -> dict[str, tuple[str, str]]:
        """Map every item's tag (and its version-stripped spelling) to the
        anchor id it will be given and its display name, across *all* pools
        -- so any item's ``refs``/``ref_up``/``ref_down`` entry can be
        turned into a clickable link to wherever that item is rendered on
        this same page, regardless of which pool defines it or which pool
        references it."""
        index: dict[str, tuple[str, str]] = {}
        for level in levels_list:
            for item in level.get("items", []):
                tag = item.get("tag") or item.get("name") or ""
                if not tag:
                    continue
                display = item.get("name") or tag
                entry = (self._anchor_id(tag), display)
                index[tag] = entry
                index.setdefault(self._strip_version(tag), entry)
        return index

    def _anchor_target(self, tag: str) -> nodes.target:
        """An invisible anchor at an item's own row/cell, so other items'
        references can link to it."""
        anchor_id, _display = self._tag_index.get(tag, (self._anchor_id(tag), ""))
        target = nodes.target(ids=[anchor_id])
        self.state.document.note_explicit_target(target, target)
        return target

    def _ref_link(self, ref_tag: str) -> nodes.Node:
        """Turn one raw ``refs``/``ref_up``/``ref_down`` tag into a clickable
        internal link to that item's anchor, falling back to plain text if
        the referenced item isn't part of this report."""
        entry = self._tag_index.get(ref_tag) or self._tag_index.get(
            self._strip_version(ref_tag)
        )
        if entry is None:
            return nodes.Text(self._strip_kind_prefix(ref_tag))
        anchor_id, display = entry
        return nodes.reference("", "", nodes.Text(display), refid=anchor_id, internal=True)

    # Requirement-kind ids that are actually registered as real Sphinx-needs
    # elsewhere in the docs (unlike e.g. the FailureMode/ControlMeasure/
    # Interface TRLC records, which only exist for this Lobster report and
    # have no matching need).
    _REQ_ID_PREFIXES = (
        "feat_req__",
        "comp_req__",
        "aou_req__",
        "tool_req__",
        "stkh_req__",
    )

    @classmethod
    def _generic_req_need_id(cls, item: dict[str, Any]) -> str | None:
        """If a generically-rendered pool's item is itself a genuine
        requirement (feature, component, AoU, tool or stakeholder
        requirement), return its need id so it can be linked with
        ``:need:``, same as Component Requirements already are. Returns
        ``None`` for items with no matching real need (e.g. Failure Modes,
        Control Measures, Root Causes, Architecture, Public API)."""
        tag = item.get("tag") or ""
        if not tag.startswith("req "):
            return None
        name = item.get("name", "")
        need_id = name.split(".", 1)[-1] if "." in name else name
        return need_id if need_id.startswith(cls._REQ_ID_PREFIXES) else None

    @staticmethod
    def _req_need_id(req: dict[str, Any]) -> str:
        # A requirement's TRLC-qualified "name" is "<Package>.<id>", but the
        # ".. comp_req::"/".. feat_req::" directive registers the need under
        # just "<id>".
        name = req.get("name", "")
        return name.split(".", 1)[-1] if "." in name else name

    @staticmethod
    def _unit_test_need_id(test: dict[str, Any]) -> str:
        # score_source_code_linker builds gtest need ids from the JUnit
        # "classname"/"name" pair joined with "__" (e.g.
        # "HalfByte__CanBeConstructedFromUInt8"), whereas the Lobster report
        # renders the same test as "HalfByte:CanBeConstructedFromUInt8".
        # Reconstruct the same id: testcase__<classname>__<name>_<hash>.
        suite, sep, case = test.get("name", "").partition(":")
        xml_style_name = f"{suite}__{case}" if sep else suite
        file = test.get("location", {}).get("file", "") or ""
        return f"testcase__{xml_style_name}_{short_hash(file + xml_style_name)}"

    def _section(self, title: str) -> nodes.section:
        """A docutils section with a title, wired up like a normal RST
        heading (implicit target registered so it gets an id / shows up in
        the local table of contents), so every pool actually renders as its
        own section rather than a flat, unheaded dump."""
        section = nodes.section(ids=[nodes.make_id(title)])
        section += nodes.title(text=title)
        self.state.document.note_implicit_target(section, section)
        return section

    @staticmethod
    def _req_key(name: str) -> str:
        # A requirement's own "tag" carries a "@<version>" suffix (e.g.
        # "req Foo.bar@1"), but items below it reference it unversioned in
        # their "ref_up" (e.g. "req Foo.bar"). Match on the unversioned
        # requirement name so links are found reliably across versions.
        return f"req {name}"

    def _feat_req_comp_req_section(
        self, feat_req_level: dict[str, Any], comp_req_level: dict[str, Any]
    ) -> nodes.section:
        feat_reqs = feat_req_level.get("items", [])
        comp_reqs = comp_req_level.get("items", [])

        # Group component requirements by the (unversioned) feature
        # requirement name they trace up to.
        comp_reqs_by_feat: dict[str, list[dict[str, Any]]] = {}
        for comp_req in comp_reqs:
            for ref in comp_req.get("ref_up") or ["<untraced>"]:
                comp_reqs_by_feat.setdefault(ref.split("@")[0], []).append(comp_req)

        rows: list[list[nodes.Node | str]] = []
        for feat_req in sorted(feat_reqs, key=lambda r: r.get("name", "")):
            linked = sorted(
                comp_reqs_by_feat.get(self._req_key(feat_req.get("name", "")), []),
                key=lambda r: r.get("name", ""),
            )

            feat_cell = nodes.paragraph()
            feat_cell += self._anchor_target(
                feat_req.get("tag") or feat_req.get("name") or ""
            )
            feat_cell += self._need_ref(self._req_need_id(feat_req))
            feat_cell += nodes.Text(": " + feat_req.get("text", ""))

            if linked:
                comp_req_list = nodes.bullet_list()
                for comp_req in linked:
                    item = nodes.list_item()
                    para = nodes.paragraph()
                    para += self._need_ref(self._req_need_id(comp_req))
                    para += nodes.Text(": " + comp_req.get("text", ""))
                    item += para
                    comp_req_list += item
                comp_cell: nodes.Node = comp_req_list
            else:
                comp_cell = nodes.paragraph(text="(no linked component requirements)")

            rows.append([feat_cell, comp_cell, feat_req.get("tracing_status", "")])

        total_feat_reqs = len(feat_reqs)
        covered_feat_reqs = sum(
            1
            for r in feat_reqs
            if comp_reqs_by_feat.get(self._req_key(r.get("name", "")))
        )
        summary = nodes.paragraph()
        summary += nodes.Text(
            f"{covered_feat_reqs} / {total_feat_reqs} feature requirements are "
            "refined by at least one component requirement."
        )

        section = self._section("Feature Requirements \u2194 Component Requirements")
        section += summary
        section.extend(
            _coverage_pie(
                "Feature requirements refined by component requirements",
                covered_feat_reqs,
                total_feat_reqs,
            )
        )
        section.extend(
            _foldable(
                f"Show {len(rows)} feature requirement(s)",
                _table(
                    ["Feature Requirement", "Linked Component Requirements", "Status"],
                    rows,
                ),
            )
        )
        return section

    def _comp_req_unit_test_section(
        self, comp_req_level: dict[str, Any], unit_test_level: dict[str, Any]
    ) -> nodes.section:
        comp_reqs = comp_req_level.get("items", [])
        unit_tests = unit_test_level.get("items", [])

        # Group unit tests by the (unversioned) requirement name they trace
        # up to.
        tests_by_req: dict[str, list[dict[str, Any]]] = {}
        for test in unit_tests:
            for ref in test.get("ref_up") or ["<untraced>"]:
                tests_by_req.setdefault(ref.split("@")[0], []).append(test)

        rows: list[list[nodes.Node | str]] = []
        for req in sorted(comp_reqs, key=lambda r: r.get("name", "")):
            tests = sorted(
                tests_by_req.get(self._req_key(req.get("name", "")), []),
                key=lambda t: t.get("name", ""),
            )

            req_cell = nodes.paragraph()
            req_cell += self._anchor_target(req.get("tag") or req.get("name") or "")
            req_cell += self._need_ref(self._req_need_id(req))
            req_cell += nodes.Text(": " + req.get("text", ""))

            if tests:
                test_list = nodes.bullet_list()
                for test in tests:
                    item = nodes.list_item()
                    para = nodes.paragraph()
                    para += self._anchor_target(
                        test.get("tag") or test.get("name") or ""
                    )
                    para += self._need_ref(
                        self._unit_test_need_id(test), display=test.get("name")
                    )
                    para += nodes.Text(f" [{test.get('status', '')}]")
                    item += para
                    test_list += item
                test_cell: nodes.Node = test_list
            else:
                test_cell = nodes.paragraph(text="(no linked tests)")

            rows.append([req_cell, test_cell, req.get("tracing_status", "")])

        total_tests = len(unit_tests)
        linked_tests = sum(1 for t in unit_tests if t.get("ref_up"))
        total_comp_reqs = len(comp_reqs)
        covered_comp_reqs = sum(
            1 for r in comp_reqs if tests_by_req.get(self._req_key(r.get("name", "")))
        )
        summary = nodes.paragraph()
        summary += nodes.Text(
            f"{covered_comp_reqs} / {total_comp_reqs} component requirements are "
            f"verified by at least one unit test; {linked_tests} / {total_tests} "
            "unit tests are linked to a component requirement."
        )

        section = self._section("Component Requirements \u2194 Unit Tests")
        section += summary
        section.extend(
            _coverage_pie(
                "Component requirements verified by unit tests",
                covered_comp_reqs,
                total_comp_reqs,
            )
        )
        section.extend(
            _foldable(
                f"Show {len(rows)} component requirement(s)",
                _table(["Requirement", "Linked Unit Tests", "Status"], rows),
            )
        )
        return section

    @staticmethod
    def _item_references(item: dict[str, Any]) -> list[str]:
        # Different pools use different reference field names in the JSON
        # ("refs" for e.g. FailureMode->Architecture, "ref_up"/"ref_down"
        # for pools chained via lobster's own up/down tracing). Collect
        # whichever is present.
        refs: list[str] = []
        for field in ("refs", "ref_up", "ref_down"):
            refs.extend(item.get(field) or [])
        return refs

    def _generic_level_section(
        self, level: dict[str, Any], pie_info: tuple[str, str] | None = None
    ) -> nodes.section:
        """Render a pool generically, straight from its JSON items, with no
        pool-specific knowledge -- this is what makes Architecture and any
        further pool (e.g. Forwarded AoUs) show up automatically, without
        needing a hand-written case for each one.

        ``pie_info``, if given, is a (summary sentence, chart title) pair
        that replaces the bare item count with a spelled-out coverage
        statement plus a covered/not-covered pie chart. An item counts as
        covered when it traces up to at least one item of the pool above it
        (``ref_up``).
        """
        name = level.get("name", "")
        items = level.get("items", [])
        coverage = level.get("coverage")

        section = self._section(name)
        covered = sum(1 for item in items if item.get("ref_up"))

        summary = nodes.paragraph()
        if pie_info:
            summary += nodes.Text(
                pie_info[0].format(covered=covered, total=len(items))
            )
        else:
            summary_text = f"{len(items)} item(s)"
            if coverage is not None:
                summary_text += f", {coverage:.1f}% coverage"
            summary += nodes.Text(summary_text)
        section += summary

        if not items:
            section += nodes.paragraph(text="(no items)")
            return section

        if pie_info:
            section.extend(_coverage_pie(pie_info[1], covered, len(items)))

        rows: list[list[nodes.Node | str]] = []
        for item in sorted(items, key=lambda i: i.get("name") or i.get("tag") or ""):
            name_cell = nodes.paragraph()
            name_cell += self._anchor_target(item.get("tag") or item.get("name") or "")
            need_id = self._generic_req_need_id(item)
            if need_id:
                name_cell += self._need_ref(need_id)
            else:
                name_cell += nodes.Text(item.get("name") or item.get("tag", ""))
            text_cell = nodes.paragraph(text=item.get("text") or "")
            refs = self._item_references(item)
            refs_cell = nodes.paragraph()
            if refs:
                for index, ref in enumerate(refs):
                    if index:
                        refs_cell += nodes.Text(", ")
                    refs_cell += self._ref_link(ref)
            else:
                refs_cell += nodes.Text("-")
            status_cell = item.get("tracing_status") or item.get("status") or ""
            rows.append([name_cell, text_cell, refs_cell, status_cell])

        section.extend(
            _foldable(
                f"Show {len(rows)} item(s)",
                _table(["Item", "Text", "References", "Status"], rows),
            )
        )
        return section

    # The four pools produced by the FMEA/FTA chain. They are rendered as a
    # single joined table instead of four separate ones, because on their own
    # each is just a list of names whose meaning only emerges from the chain:
    # a fault tree's basic event (root cause) is mitigated by a control
    # measure and leads, via the tree's top event, to a failure mode of a
    # public API interface.
    _SAFETY_LEVEL_NAMES = (
        "Public API",
        "Failure Modes",
        "Control Measures",
        "Root Causes",
    )

    def _safety_analysis_section(
        self, levels_by_name: dict[str, dict[str, Any]]
    ) -> nodes.section:
        by_tag: dict[str, dict[str, Any]] = {}
        for level_name in self._SAFETY_LEVEL_NAMES:
            for item in levels_by_name[level_name].get("items", []):
                tag = item.get("tag") or ""
                by_tag[tag] = item
                by_tag.setdefault(self._strip_version(tag), item)

        root_causes = levels_by_name["Root Causes"].get("items", [])

        # A fault tree lives in one .puml file and contains exactly one top
        # event (the failure mode it analyses) plus the basic events (the
        # root causes) leading to it, so the file is what links a root cause
        # to its failure mode.
        top_event_by_file: dict[str, dict[str, Any]] = {}
        for item in root_causes:
            if item.get("kind") == "TopEvent":
                top_event_by_file[item.get("location", {}).get("file", "")] = item

        spelled_out: set[str] = set()

        def cell(tag: str | None) -> nodes.paragraph:
            """Render one referenced item: spelled out in full (name plus
            descriptive text) the first time it appears, and as the bare
            name on every repeat -- so e.g. the one public API interface
            shared by all rows is described once, not four times."""
            para = nodes.paragraph()
            item = by_tag.get(tag or "") or by_tag.get(self._strip_version(tag or ""))
            if item is None:
                para += nodes.Text("-")
                return para
            item_tag = item.get("tag") or ""
            display = (item.get("name") or item_tag).rsplit(".", 1)[-1]
            if item_tag in spelled_out:
                para += nodes.Text(display)
                return para
            spelled_out.add(item_tag)
            para += self._anchor_target(item_tag)
            para += nodes.strong(text=display)
            if item.get("text"):
                para += nodes.Text(": " + item["text"])
            return para

        rows: list[list[nodes.Node | str]] = []
        for root_cause in sorted(root_causes, key=lambda i: i.get("name") or ""):
            if root_cause.get("kind") == "TopEvent":
                # Top events are the failure modes themselves and show up in
                # the "Failure Mode" column of their tree's rows.
                continue
            top_event = top_event_by_file.get(
                root_cause.get("location", {}).get("file", "")
            )
            failure_mode_tag = (top_event or {}).get("ref_up") or [None]
            failure_mode = by_tag.get(
                self._strip_version(failure_mode_tag[0] or "")
            )
            public_api_tag = (failure_mode or {}).get("ref_up") or [None]
            control_measure_tag = root_cause.get("ref_up") or [None]

            rows.append(
                [
                    cell(root_cause.get("tag")),
                    cell(failure_mode_tag[0]),
                    cell(public_api_tag[0]),
                    cell(control_measure_tag[0]),
                ]
            )

        summary = nodes.paragraph()
        summary += nodes.Text(
            f"{len(rows)} root cause(s) across {len(top_event_by_file)} fault "
            "tree(s), each shown with the failure mode it leads to, the public "
            "API interface that failure mode belongs to, and the control "
            "measure mitigating it."
        )

        section = self._section("Safety Analysis")
        section += summary
        section.extend(
            _foldable(
                f"Show {len(rows)} root cause(s)",
                _table(
                    ["Root Cause", "Failure Mode", "Public API", "Control Measure"],
                    rows,
                ),
            )
        )
        return section

    def _build_nodes(self, report: dict[str, Any]) -> list[nodes.Node]:
        levels_list = report.get("levels", [])
        levels_by_name = {lvl.get("name"): lvl for lvl in levels_list}
        self._tag_index = self._build_tag_index(levels_list)
        rendered_names: set[str] = set()
        result: list[nodes.Node] = [nodes.raw("", _ANCHOR_SCRIPT, format="html")]

        # Render the requirement chain top-down first -- feature
        # requirements refined into component requirements, then component
        # requirements verified by unit tests -- so the report reads along
        # the direction of decomposition before the remaining pools follow
        # in whatever order the JSON lists them.
        feat_req_level = levels_by_name.get("Feature Requirements")
        comp_req_level = levels_by_name.get("Component Requirements")
        unit_test_level = levels_by_name.get("Unit Test")
        if feat_req_level is not None and comp_req_level is not None:
            result.append(
                self._feat_req_comp_req_section(feat_req_level, comp_req_level)
            )
            rendered_names.add("Feature Requirements")
        if comp_req_level is not None and unit_test_level is not None:
            result.append(
                self._comp_req_unit_test_section(comp_req_level, unit_test_level)
            )
            rendered_names.add("Component Requirements")
            rendered_names.add("Unit Test")

        # The FMEA/FTA pools only make sense as one joined table, so keep
        # them out of the generic loop and append that table at the end.
        safety_section: nodes.section | None = None
        if all(name in levels_by_name for name in self._SAFETY_LEVEL_NAMES):
            safety_section = self._safety_analysis_section(levels_by_name)
            rendered_names.update(self._SAFETY_LEVEL_NAMES)

        for level in levels_list:
            name = level.get("name")
            if name in rendered_names:
                continue
            rendered_names.add(name)
            result.append(
                self._generic_level_section(level, _PIE_INFO.get(name or ""))
            )

        if safety_section is not None:
            result.append(safety_section)

        return result
