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
from pathlib import Path
from typing import Any

from docutils import nodes
from sphinx.util.docutils import SphinxDirective

from src.extensions.score_source_code_linker.xml_parser import short_hash
from src.helper_lib import find_ws_root


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


class LobsterTraceabilityReportDirective(SphinxDirective):
    """Render a Lobster traceability report as one section per pool
    ("level") found in the JSON: Feature Requirements, Component
    Requirements, Unit Test, Architecture, Public API, Failure Modes,
    Control Measures, Root Causes, etc. Component Requirements and Unit
    Test are rendered together as a single cross-linked table (using
    ``:need:`` references); every other pool is rendered generically
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

    def _need_ref(self, need_id: str) -> list[nodes.Node]:
        """Parse a ``:need:`<need_id>``` role, so it resolves (at doctree-
        resolved time) into a real link to that need's directive/element,
        exactly like a hand-written ``:need:`` reference elsewhere in the
        docs."""
        text_nodes, _messages = self.state.inline_text(
            f":need:`{need_id}`", self.lineno
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
    def _comp_req_need_id(req: dict[str, Any]) -> str:
        # A requirement's TRLC-qualified "name" is "<Package>.<id>", but the
        # ".. comp_req::" directive registers the need under just "<id>".
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

    def _comp_req_unit_test_section(
        self, comp_req_level: dict[str, Any], unit_test_level: dict[str, Any]
    ) -> nodes.section:
        comp_reqs = comp_req_level.get("items", [])
        unit_tests = unit_test_level.get("items", [])

        # A requirement's own "tag" carries a "@<version>" suffix (e.g.
        # "req Foo.bar@1"), but a test's "ref_up" entries reference it
        # unversioned (e.g. "req Foo.bar"). Match on the unversioned
        # requirement name so links are found reliably across versions.
        def _req_key(name: str) -> str:
            return f"req {name}"

        # Group unit tests by the (unversioned) requirement name they trace
        # up to.
        tests_by_req: dict[str, list[dict[str, Any]]] = {}
        for test in unit_tests:
            for ref in test.get("ref_up") or ["<untraced>"]:
                tests_by_req.setdefault(ref.split("@")[0], []).append(test)

        rows: list[list[nodes.Node | str]] = []
        for req in sorted(comp_reqs, key=lambda r: r.get("name", "")):
            tests = sorted(
                tests_by_req.get(_req_key(req.get("name", "")), []),
                key=lambda t: t.get("name", ""),
            )

            req_cell = nodes.paragraph()
            req_cell += self._anchor_target(req.get("tag") or req.get("name") or "")
            req_cell += self._need_ref(self._comp_req_need_id(req))
            req_cell += nodes.Text(": " + req.get("text", ""))

            if tests:
                test_list = nodes.bullet_list()
                for test in tests:
                    item = nodes.list_item()
                    para = nodes.paragraph()
                    para += self._anchor_target(
                        test.get("tag") or test.get("name") or ""
                    )
                    para += self._need_ref(self._unit_test_need_id(test))
                    para += nodes.Text(f" [{test.get('status', '')}]")
                    item += para
                    test_list += item
                test_cell: nodes.Node = test_list
            else:
                test_cell = nodes.paragraph(text="(no linked tests)")

            rows.append([req_cell, test_cell, req.get("tracing_status", "")])

        total_tests = len(unit_tests)
        linked_tests = sum(1 for t in unit_tests if t.get("ref_up"))
        summary = nodes.paragraph()
        summary += nodes.Text(
            f"{linked_tests} / {total_tests} unit tests are linked to a "
            "component requirement."
        )

        section = self._section("Component Requirements \u2194 Unit Tests")
        section += summary
        section += _table(["Requirement", "Linked Unit Tests", "Status"], rows)
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

    def _generic_level_section(self, level: dict[str, Any]) -> nodes.section:
        """Render a pool generically, straight from its JSON items, with no
        pool-specific knowledge -- this is what makes Failure Modes,
        Control Measures, Root Causes, Architecture, Public API, Feature
        Requirements and Forwarded AoUs show up automatically, without
        needing a hand-written case for each one."""
        name = level.get("name", "")
        items = level.get("items", [])
        coverage = level.get("coverage")

        section = self._section(name)

        summary = nodes.paragraph()
        summary_text = f"{len(items)} item(s)"
        if coverage is not None:
            summary_text += f", {coverage:.1f}% coverage"
        summary += nodes.Text(summary_text)
        section += summary

        if not items:
            section += nodes.paragraph(text="(no items)")
            return section

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

        section += _table(["Item", "Text", "References", "Status"], rows)
        return section

    def _build_nodes(self, report: dict[str, Any]) -> list[nodes.Node]:
        levels_list = report.get("levels", [])
        levels_by_name = {lvl.get("name"): lvl for lvl in levels_list}
        self._tag_index = self._build_tag_index(levels_list)
        rendered_names: set[str] = set()
        result: list[nodes.Node] = []

        comp_req_level = levels_by_name.get("Component Requirements")
        unit_test_level = levels_by_name.get("Unit Test")
        if comp_req_level is not None and unit_test_level is not None:
            result.append(
                self._comp_req_unit_test_section(comp_req_level, unit_test_level)
            )
            rendered_names.add("Component Requirements")
            rendered_names.add("Unit Test")

        for level in levels_list:
            name = level.get("name")
            if name in rendered_names:
                continue
            rendered_names.add(name)
            result.append(self._generic_level_section(level))

        return result
