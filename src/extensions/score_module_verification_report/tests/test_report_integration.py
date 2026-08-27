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
"""Acceptance tests for the module verification report.

"It looks right in the sidebar" is not evidence.  These tests assert on the
doctree, on ``env.tocs`` and on rendered output.

Acceptance test 7 (a component in ``mod.includes`` but missing from
``:covers:`` fails the build via the *metamodel* rule, not via extension code)
deliberately lives with the metamodel:
``src/extensions/score_metamodel/tests/rst/graph/test_mod_ver_report_scope.rst``.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from docutils import nodes
from sphinx.testing.util import SphinxTestApp

EXTERNAL_NEEDS: dict[str, Any] = {
    "current_version": "1.0",
    "project": "external",
    "versions": {
        "1.0": {
            "needs": {
                "comp__external_thing": {
                    "docname": "index",
                    "id": "comp__external_thing",
                    "lineno": 1,
                    "status": "valid",
                    "title": "External Component",
                    "type": "comp",
                    "type_name": "comp",
                }
            }
        }
    },
}

CONF_PY = """
extensions = ["sphinx_needs", "score_module_verification_report"]
needs_id_regex = "^[a-zA-Z0-9_]+$"
needs_types = [
    dict(directive="feat", title="Feature", prefix="feat__", color="#FFF", style="node"),
    dict(directive="comp", title="Component", prefix="comp__", color="#FFF", style="node"),
    dict(directive="mod", title="Module", prefix="mod__", color="#FFF", style="node"),
    dict(
        directive="mod_ver_report",
        title="Module Verification Report",
        prefix="mod_vrep__",
        color="#FFF",
        style="node",
    ),
    dict(directive="tcase", title="Test Case", prefix="tcase__", color="#FFF", style="node"),
]
needs_extra_options = ["safety", "security", "verification_method"]
needs_extra_links = [
    dict(option="belongs_to", incoming="belongs to", outgoing="belongs to"),
    dict(option="includes", incoming="included by", outgoing="includes"),
    dict(option="covers", incoming="covered by", outgoing="covers"),
    dict(option="contains", incoming="contained by", outgoing="contains"),
    dict(option="evidence", incoming="evidence for", outgoing="evidence"),
]
needs_external_needs = [
    dict(base_url="https://example.invalid/docs", json_path="external_needs.json")
]
suppress_warnings = ["app.add_directive", "epub.unknown_project_files"]
"""

ARCHITECTURE = """
.. comp:: JSON
   :id: comp__baselibs_json
   :safety: ASIL_B
   :security: NO
   :status: valid

.. comp:: Bit Manipulation
   :id: comp__baselibs_bit_manipulation
   :safety: ASIL_B
   :security: NO
   :status: valid

.. mod:: Baselibs
   :id: mod__baselibs
   :includes: comp__baselibs_json, comp__baselibs_bit_manipulation

.. tcase:: A test case
   :id: tcase__baselibs_1
   :status: valid
"""

REPORT = """
Baselibs
========

.. mod_ver_report:: Baselibs Verification Report
   :id: mod_vrep__baselibs
   :belongs_to: mod__baselibs
   :covers: comp__baselibs_json, comp__baselibs_bit_manipulation
   :safety: ASIL_B
   :security: NO
   :status: valid
   :verification_method: test
   :contains: tcase__baselibs_1
   :titles:
      comp__baselibs_json = JSON Utilities

   Verification report for the Baselibs module.
"""


def _write_sources(root: Path, docs: dict[str, str], conf: str = CONF_PY) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "conf.py").write_text(conf)
    (root / "external_needs.json").write_text(json.dumps(EXTERNAL_NEEDS))
    for name, text in docs.items():
        path = root / f"{name}.rst"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def _index(*docnames: str) -> str:
    entries = "\n   ".join(docnames)
    return f"Docs\n====\n\n.. toctree::\n   :maxdepth: 3\n\n   {entries}\n"


AppFactory = Callable[..., SphinxTestApp]


@pytest.fixture
def build(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppFactory:
    """Build a source tree and return the finished app."""

    def _build(
        docs: dict[str, str],
        *,
        buildername: str = "html",
        parallel: int = 1,
        srcdir: Path | None = None,
        outdir: Path | None = None,
        freshenv: bool = True,
        conf: str = CONF_PY,
    ) -> SphinxTestApp:
        src = srcdir or (tmp_path / "src")
        _write_sources(src, docs, conf)
        monkeypatch.chdir(src)
        app = SphinxTestApp(
            freshenv=freshenv,
            srcdir=src,
            confdir=src,
            outdir=outdir or (tmp_path / f"out-{buildername}"),
            buildername=buildername,
            parallel=parallel,
        )
        app.build()
        return app

    return _build


def _sections(doctree: nodes.document) -> list[nodes.section]:
    return list(doctree.findall(nodes.section))


def _section_ids(doctree: nodes.document) -> list[str]:
    return [section["ids"][0] for section in _sections(doctree) if section["ids"]]


def _titles(doctree: nodes.document) -> list[str]:
    return [section[0].astext() for section in _sections(doctree)]


# --------------------------------------------------------------------------
# The core promise: real sections, produced during the read phase.
# --------------------------------------------------------------------------


def test_report_emits_real_sections_as_siblings_of_the_need(
    build: AppFactory,
) -> None:
    app = build({"index": _index("report"), "report": REPORT + ARCHITECTURE})
    doctree = app.env.get_doctree("report")

    titles = _titles(doctree)
    assert "Report Metadata" in titles
    assert "Verification Scope" in titles
    assert "JSON Utilities" in titles  # explicit override
    assert "Baselibs Bit Manipulation" in titles  # derived fallback
    assert "Verification Evidence" in titles

    # The Need is a sibling of the sections, not their container: no section
    # may be a descendant of the Need node.
    from sphinx_needs.nodes import Need

    for need in doctree.findall(Need):
        assert not list(need.findall(nodes.section, include_self=False)), (
            "a section ended up inside the Need node; "
            "sphinx-needs parses need content with match_titles=False, so those "
            "headings would silently stop being sections"
        )


def test_generated_sections_are_flat(build: AppFactory) -> None:
    """Constraint 3: a flat list of top-level entries is sufficient."""
    app = build({"index": _index("report"), "report": REPORT + ARCHITECTURE})
    doctree = app.env.get_doctree("report")

    page = next(iter(doctree.findall(nodes.section)))  # "Baselibs"
    generated = [child for child in page.children if isinstance(child, nodes.section)]
    assert [child[0].astext() for child in generated] == [
        "Report Metadata",
        "Verification Scope",
        "JSON Utilities",
        "Baselibs Bit Manipulation",
        "Verification Evidence",
    ]
    for section in generated:
        assert not list(section.findall(nodes.section, include_self=False))


# --------------------------------------------------------------------------
# Acceptance test 1: :ref: from another page resolves and links.
# --------------------------------------------------------------------------


def test_ref_from_another_page_resolves(build: AppFactory) -> None:
    other = (
        "Other\n=====\n\n"
        "See :ref:`mod_vrep__baselibs__comp__baselibs_json` for details.\n"
    )
    app = build(
        {
            "index": _index("report", "other"),
            "report": REPORT + ARCHITECTURE,
            "other": other,
        }
    )
    assert "undefined label" not in app.warning.getvalue()

    html = (Path(app.outdir) / "other.html").read_text()
    assert 'href="report.html#mod-vrep-baselibs-comp-baselibs-json"' in html
    # An implicit :ref: takes its text from the section title -- proof that the
    # target really is a section and not a synthesized anchor.
    assert "JSON Utilities" in html


# --------------------------------------------------------------------------
# Acceptance test 2: local ToC entries for every component section.
# --------------------------------------------------------------------------


def test_toc_contains_every_generated_section(build: AppFactory) -> None:
    app = build({"index": _index("report"), "report": REPORT + ARCHITECTURE})

    toc = app.env.tocs["report"]
    toc_titles = [ref.astext() for ref in toc.findall(nodes.reference)]
    for expected in (
        "Report Metadata",
        "Verification Scope",
        "JSON Utilities",
        "Baselibs Bit Manipulation",
        "Verification Evidence",
    ):
        assert expected in toc_titles

    toc_anchors = [ref["anchorname"] for ref in toc.findall(nodes.reference)]
    assert "#mod-vrep-baselibs-comp-baselibs-json" in toc_anchors


# --------------------------------------------------------------------------
# Acceptance test 3: stable, collision-free anchors.
# --------------------------------------------------------------------------


SECOND_REPORT = """
.. mod_ver_report:: Second Verification Report
   :id: mod_vrep__second
   :belongs_to: mod__baselibs
   :covers: comp__baselibs_json
   :safety: ASIL_B
   :security: NO
   :status: valid
   :verification_method: test
   :titles:
      comp__baselibs_json = JSON Utilities
"""


def test_two_reports_on_one_page_do_not_collide(build: AppFactory) -> None:
    app = build(
        {"index": _index("report"), "report": REPORT + SECOND_REPORT + ARCHITECTURE}
    )
    ids = _section_ids(app.env.get_doctree("report"))

    assert "mod-vrep-baselibs-comp-baselibs-json" in ids
    assert "mod-vrep-second-comp-baselibs-json" in ids
    # Same heading text twice, but no docutils "-1" disambiguation suffix.
    assert not [i for i in ids if re.search(r"-\d+$", i)]
    assert len(ids) == len(set(ids))


def test_anchors_are_stable_across_rebuilds(tmp_path: Path, build: AppFactory) -> None:
    src, out = tmp_path / "src", tmp_path / "out"
    docs = {"index": _index("report"), "report": REPORT + ARCHITECTURE}

    first = build(docs, srcdir=src, outdir=out)
    before = _section_ids(first.env.get_doctree("report"))
    first.cleanup()

    second = build(docs, srcdir=src, outdir=out, freshenv=False)
    assert _section_ids(second.env.get_doctree("report")) == before


# --------------------------------------------------------------------------
# Acceptance test 4: heading depth follows placement.
# --------------------------------------------------------------------------


def test_heading_depth_at_root_and_nested(build: AppFactory) -> None:
    # The report placed below an existing sub-heading. REPORT's own page title
    # is dropped so only the directive is re-used.
    nested = (
        "Page\n====\n\nChapter\n-------\n\n" + "\n".join(REPORT.splitlines()[3:]) + "\n"
    )
    app = build(
        {
            "index": _index("rootlevel", "nested"),
            "rootlevel": REPORT + ARCHITECTURE,
            "nested": nested + ARCHITECTURE,
        }
    )

    def depth_of(docname: str, title: str) -> int:
        doctree = app.env.get_doctree(docname)
        for section in doctree.findall(nodes.section):
            if section[0].astext() == title:
                depth = 0
                node = section.parent
                while node is not None:
                    if isinstance(node, nodes.section):
                        depth += 1
                    node = node.parent
                return depth
        raise AssertionError(f"{title!r} not found in {docname}")

    # Root level: directly below the page title.
    assert depth_of("rootlevel", "JSON Utilities") == 1
    # Nested below an existing heading: one level deeper.
    assert depth_of("nested", "JSON Utilities") == 2
    # ... and still flat among themselves at that level.
    assert depth_of("nested", "Report Metadata") == 2


# --------------------------------------------------------------------------
# Acceptance test 5: a non-HTML builder keeps the sections.
# --------------------------------------------------------------------------


def test_singlehtml_builder_keeps_sections(build: AppFactory) -> None:
    app = build(
        {"index": _index("report"), "report": REPORT + ARCHITECTURE},
        buildername="singlehtml",
    )
    html = (Path(app.outdir) / "index.html").read_text()
    assert 'id="mod-vrep-baselibs-comp-baselibs-json"' in html
    assert "JSON Utilities" in html


def test_latex_builder_keeps_sections(build: AppFactory) -> None:
    app = build(
        {"index": _index("report"), "report": REPORT + ARCHITECTURE},
        buildername="latex",
    )
    tex = next(Path(app.outdir).glob("*.tex")).read_text()
    assert "JSON Utilities" in tex
    assert "Verification Scope" in tex


# --------------------------------------------------------------------------
# Acceptance test 6: identical under -j 1 and parallel reading.
# --------------------------------------------------------------------------


def test_structure_identical_serial_and_parallel(
    tmp_path: Path, build: AppFactory
) -> None:
    # Sphinx only forks when there are more than five documents to read.
    filler = {f"filler{i}": f"Filler {i}\n=========\n\ntext\n" for i in range(8)}
    docs = {
        "index": _index("report", *filler),
        "report": REPORT + ARCHITECTURE,
        **filler,
    }

    serial = build(docs, srcdir=tmp_path / "s1", outdir=tmp_path / "o1", parallel=1)
    serial_ids = _section_ids(serial.env.get_doctree("report"))
    serial_titles = _titles(serial.env.get_doctree("report"))
    serial.cleanup()

    parallel = build(docs, srcdir=tmp_path / "s2", outdir=tmp_path / "o2", parallel=4)
    assert _section_ids(parallel.env.get_doctree("report")) == serial_ids
    assert _titles(parallel.env.get_doctree("report")) == serial_titles


# --------------------------------------------------------------------------
# Acceptance test 8: a needtable resolves an external Need.
# --------------------------------------------------------------------------


EXTERNAL_REPORT = """
External
========

.. mod_ver_report:: External Verification Report
   :id: mod_vrep__external
   :belongs_to: mod__baselibs
   :covers: comp__external_thing
   :safety: QM
   :security: NO
   :status: valid
   :verification_method: inspection
"""


def test_needtable_resolves_an_external_need(build: AppFactory) -> None:
    app = build(
        {"index": _index("report"), "report": EXTERNAL_REPORT + ARCHITECTURE},
    )
    html = (Path(app.outdir) / "report.html").read_text()
    # Resolved by sphinx-needs from needs.json, including its external URL --
    # the extension itself never looked at the need.
    assert "External Component" in html
    assert "https://example.invalid/docs" in html


# --------------------------------------------------------------------------
# Acceptance tests 9 + 10 at build level.
# --------------------------------------------------------------------------


DUPLICATE_REPORT = """
Dupes
=====

.. mod_ver_report:: Duplicate Report
   :id: mod_vrep__dupes
   :belongs_to: mod__baselibs
   :covers: comp__baselibs_json, comp__baselibs_json, comp__baselibs_bit_manipulation
   :safety: QM
   :security: NO
   :status: valid
   :verification_method: test
   :titles:
      comp__baselibs_json = Same Title
      comp__baselibs_bit_manipulation = Same Title
"""


def test_duplicates_and_title_collisions_are_deterministic(
    build: AppFactory,
) -> None:
    app = build({"index": _index("report"), "report": DUPLICATE_REPORT + ARCHITECTURE})

    assert "duplicate entry 'comp__baselibs_json'" in app.warning.getvalue()

    doctree = app.env.get_doctree("report")
    titles = _titles(doctree)
    assert titles.count("Same Title") == 2  # collision allowed ...
    ids = _section_ids(doctree)
    assert "mod-vrep-dupes-comp-baselibs-json" in ids  # ... anchors still differ
    assert "mod-vrep-dupes-comp-baselibs-bit-manipulation" in ids
    assert len(ids) == len(set(ids))


HOSTILE_REPORT = """
Hostile
=======

.. mod_ver_report:: Hostile Report
   :id: mod_vrep__hostile
   :belongs_to: mod__baselibs
   :covers: comp__baselibs_json, comp__baselibs_bit_manipulation, evil"or(1)
   :safety: QM
   :security: NO
   :status: valid
   :verification_method: test
"""


def test_hostile_component_id_is_rejected_not_interpolated(
    build: AppFactory,
) -> None:
    app = build({"index": _index("report"), "report": HOSTILE_REPORT + ARCHITECTURE})
    warnings = app.warning.getvalue()
    assert "is not a valid need id and is skipped" in warnings

    titles = _titles(app.env.get_doctree("report"))
    assert "Baselibs Json" in titles or "Json" in " ".join(titles)
    # The rejected token never became a section.
    assert not [t for t in titles if "evil" in t.lower()]


# --------------------------------------------------------------------------
# Version qualifiers are reported, not silently stripped.
# --------------------------------------------------------------------------


VERSIONED_REPORT = """
Versioned
=========

.. mod_ver_report:: Versioned Report
   :id: mod_vrep__versioned
   :belongs_to: mod__baselibs
   :covers: comp__baselibs_json[version==1], comp__baselibs_bit_manipulation
   :safety: QM
   :security: NO
   :status: valid
   :verification_method: test
"""


def test_version_qualifier_warns(build: AppFactory) -> None:
    app = build({"index": _index("report"), "report": VERSIONED_REPORT + ARCHITECTURE})
    assert "ignoring version qualifier" in app.warning.getvalue()
    assert "Baselibs Json" in _titles(app.env.get_doctree("report"))


# --------------------------------------------------------------------------
# The extension owns no build lifecycle beyond registering its directives.
# --------------------------------------------------------------------------


NEEDS_EXTRA_LINKS_BLOCK = """needs_extra_links = [
    dict(option="belongs_to", incoming="belongs to", outgoing="belongs to"),
    dict(option="includes", incoming="included by", outgoing="includes"),
    dict(option="covers", incoming="covered by", outgoing="covers"),
    dict(option="contains", incoming="contained by", outgoing="contains"),
    dict(option="evidence", incoming="evidence for", outgoing="evidence"),
]"""

NEEDS_LINKS_BLOCK = """needs_links = {
    "belongs_to": dict(incoming="belongs to", outgoing="belongs to"),
    "includes": dict(incoming="included by", outgoing="includes"),
    "covers": dict(incoming="covered by", outgoing="covers"),
    "contains": dict(incoming="contained by", outgoing="contains"),
    "evidence": dict(incoming="evidence for", outgoing="evidence"),
}"""

NO_EVIDENCE_LINKS_BLOCK = """needs_extra_links = [
    dict(option="belongs_to", incoming="belongs to", outgoing="belongs to"),
    dict(option="includes", incoming="included by", outgoing="includes"),
    dict(option="covers", incoming="covered by", outgoing="covers"),
]"""


def test_evidence_section_honours_the_needs_links_dict(build: AppFactory) -> None:
    """``score_metamodel`` writes ``needs_links``, not ``needs_extra_links``.

    Looking only at the deprecated list silently drops the Verification
    Evidence section in every real project.
    """
    conf = CONF_PY.replace(NEEDS_EXTRA_LINKS_BLOCK, NEEDS_LINKS_BLOCK)
    assert conf != CONF_PY
    app = build({"index": _index("report"), "report": REPORT + ARCHITECTURE}, conf=conf)
    assert "Verification Evidence" in _titles(app.env.get_doctree("report"))


def test_evidence_section_is_skipped_when_the_links_are_not_configured(
    build: AppFactory,
) -> None:
    conf = CONF_PY.replace(NEEDS_EXTRA_LINKS_BLOCK, NO_EVIDENCE_LINKS_BLOCK)
    assert conf != CONF_PY
    report = REPORT.replace("   :contains: tcase__baselibs_1\n", "")
    app = build({"index": _index("report"), "report": report + ARCHITECTURE}, conf=conf)
    titles = _titles(app.env.get_doctree("report"))
    assert "Verification Evidence" not in titles
    assert "Verification Scope" in titles


def test_extension_has_no_build_lifecycle_hooks() -> None:
    import inspect

    import score_module_verification_report as ext

    source = inspect.getsource(ext)
    connects = re.findall(r'app\.connect\(\s*"([^"]+)"', source)
    assert connects == ["config-inited"], (
        "The extension must own no build lifecycle: no env-updated re-read, no "
        "build-finished consistency pass, no registry. The single config-inited "
        f"handler registers directives only. Found: {connects}"
    )
