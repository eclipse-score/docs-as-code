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
    """Render a Lobster traceability report (Component Requirements <-> Unit
    Tests) as a table.

    Usage::

        .. lobster-traceability-report::
           bazel-bin/score/bitmanipulation/dependable_element_bitmanipulation_index_report.json

    The path is resolved relative to the workspace root, the same way
    ``score_source_code_linker`` locates ``bazel-testlogs``. The referenced
    report is a plain build artifact and must already exist, e.g. via::

        bazel build //score/bitmanipulation:dependable_element_bitmanipulation
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

    def _build_nodes(self, report: dict[str, Any]) -> list[nodes.Node]:
        levels = {lvl.get("name"): lvl for lvl in report.get("levels", [])}
        comp_reqs = levels.get("Component Requirements", {}).get("items", [])
        unit_tests = levels.get("Unit Test", {}).get("items", [])

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
            req_cell += self._need_ref(self._comp_req_need_id(req))
            req_cell += nodes.Text(": " + req.get("text", ""))

            if tests:
                test_list = nodes.bullet_list()
                for test in tests:
                    item = nodes.list_item()
                    para = nodes.paragraph()
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

        table = _table(["Requirement", "Linked Unit Tests", "Status"], rows)
        return [summary, table]
