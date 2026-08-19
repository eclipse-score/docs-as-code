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
"""Sphinx directive that generates the per-module verification report body.

Components are discovered by a shallow filesystem scan of the docs source
tree for ``.. comp::`` (and ``.. document::``) directives, cached on the
Sphinx environment at ``env-before-read-docs`` time. This keeps the
extension ``parallel_read_safe`` — no dependency on sphinx-needs internal
state during the read phase.

Per-work-product realization is delegated to sphinx-needs: each
"Realized by" cell renders a ``.. needlist::`` filtered by the component
slug (normalised underscore-free substring match on the doc id) and by
the ``realizes`` link to the work product. Coverage status is derived
from ``coverage_summary.json``. Only components whose docs are named
differently from the component slug (see ``overrides`` in the config)
need explicit per-component data.

Usage in RST::

    .. module-verification-report::
       :config: reporting/module_verification_report.yaml   # optional

The config file has the shape::

    module_id: mod__baselibs
    # optional; derived from module_id if omitted
    component_prefix: comp__baselibs_
    # optional; standard workproducts checked per component
    workproducts:
      - key: requirements_inspect
        label: Requirements Inspection
        wp_id: wp__requirements_inspect
      - ...
    # optional; per-component overrides for irregular cases (documents
    # whose id does not contain the component slug, e.g.
    # ``comp__baselibs_nlohman_json`` → ``doc__json_*``)
    overrides:
      comp__baselibs_some_component:
        workproducts:
          requirements_inspect: doc__some_component_req_inspection
          ...
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

import yaml
from docutils import nodes
from docutils.statemachine import ViewList
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import nested_parse_with_titles


# ---------------------------------------------------------------------------
# Need discovery (filesystem scan)
# ---------------------------------------------------------------------------
#
# We deliberately do **not** query ``SphinxNeedsData`` here: doing so would
# require reading the report source strictly after every source registering
# a ``.. comp::`` / ``.. document::`` need, which forces ``parallel_read_safe
# = False`` on the extension and produces two Sphinx-level warnings per
# build (``the score_module_verification_report extension is not safe for
# parallel reading`` / ``doing serial read``). Those warnings are fatal
# under ``-W``.
#
# The RST directive syntax used across baselibs is stable:
#
#     .. comp:: <title>
#        :id: comp__baselibs_<slug>
#        :safety: ASIL_B
#        :security: NO
#        :status: valid
#        ...
#
#     .. document:: <title>
#        :id: doc__<slug>_<suffix>
#        :realizes: wp__<key>[version==<N>]
#        ...
#
# Documents are matched to a work product entirely on the sphinx-needs
# side, at render time: each per-component "Realized by" cell is a
# ``.. needlist::`` filtered by ``type == "document"``, by a
# normalised-slug substring match of the component slug against the doc
# id, and by the ``realizes`` link containing the WP id. This scan only
# needs to enumerate components and their titles.
#
# A shallow regex scan of the source tree at ``env-before-read-docs``
# gives us everything the directive needs, and works in every process of
# a parallel build.

_DIRECTIVE_HEADER_RE = re.compile(
    r"^\.\.[ \t]+(?P<name>[a-z_-]+)::[ \t]*(?P<title>.*?)\s*$"
)
_OPTION_LINE_RE = re.compile(r"^[ \t]+:(?P<key>[^:]+):[ \t]*(?P<value>.*?)\s*$")

# Options captured from ``:key: value`` lines. Everything else
# (safety, security, status, realizes, tags, ...) is intentionally
# dropped: the report delegates all attribute and link resolution to
# sphinx-needs at render time (``.. needtable::`` / ``.. needlist::``).
# ``includes`` is captured only for ``.. mod::`` needs (whitelist of
# components; see :func:`_module_includes`); ``version`` is captured
# on ``.. comp::`` needs to honour ``[version==N]`` filters coming from
# that whitelist.
_SCANNED_OPTIONS = frozenset({"id", "includes", "version"})


def _scan_rst_needs(srcdir: str, directives: set[str]) -> list[dict]:
    """Return every need declared by one of *directives* under *srcdir*.

    Each result carries ``directive`` (e.g. ``comp``), ``id`` and
    ``title``. Silently skips unreadable files.
    """
    results: list[dict] = []
    for root, _dirs, files in os.walk(srcdir):
        for fname in files:
            if not fname.endswith(".rst"):
                continue
            path = os.path.join(root, fname)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    lines = fh.readlines()
            except (OSError, UnicodeDecodeError):
                continue
            i = 0
            while i < len(lines):
                m = _DIRECTIVE_HEADER_RE.match(lines[i])
                if not m or m.group("name") not in directives:
                    i += 1
                    continue
                entry: dict[str, Any] = {
                    "directive": m.group("name"),
                    "title": m.group("title").strip(),
                }
                j = i + 1
                while j < len(lines):
                    opt = _OPTION_LINE_RE.match(lines[j])
                    if not opt:
                        break
                    key = opt.group("key").strip()
                    if key in _SCANNED_OPTIONS:
                        entry[key] = opt.group("value").strip()
                    j += 1
                if "id" in entry:
                    results.append(entry)
                i = j if j > i else i + 1
    return results


def _normalize_slug(text: str) -> str:
    """Return *text* stripped of underscores and lower-cased.

    Component ids and document ids sometimes spell the same component
    with different underscoring (``bit_manipulation`` vs.
    ``bitmanipulation``). Comparing on the underscore-free form makes
    that difference invisible without introducing per-component config.
    """
    return text.replace("_", "").lower()


_INCLUDE_ENTRY_RE = re.compile(
    r"^(?P<id>[^\[\s]+)(?:\[version==(?P<version>[^\]]+)\])?\s*$"
)


def _module_includes(
    needs: list[dict], module_id: str
) -> dict[str, str | None] | None:
    """Return the component ids listed in ``:includes:`` on the
    ``.. mod::`` need whose id equals *module_id*, mapped to their
    required version (or ``None`` if no ``[version==N]`` filter was set).

    Entries in ``:includes:`` have the form ``<id>[version==<N>]`` and
    are comma-separated. Returns ``None`` if no matching mod need is
    found in *needs* (spec error → caller renders an ``error`` node).
    """
    for entry in needs:
        if entry.get("directive") != "mod" or entry.get("id") != module_id:
            continue
        raw = entry.get("includes", "")
        result: dict[str, str | None] = {}
        for part in raw.split(","):
            m = _INCLUDE_ENTRY_RE.match(part.strip())
            if m:
                result[m.group("id")] = m.group("version")
        return result
    return None


def _discover_components(
    env, component_prefix: str, whitelist: dict[str, str | None]
) -> list[dict]:
    """Return every ``.. comp::`` need whose id (and, when a
    ``[version==N]`` filter was declared, whose ``:version:``) matches
    an entry in *whitelist*.

    Sourced from the filesystem scan cached on ``env`` at
    ``env-before-read-docs``. Components are returned sorted by id for a
    stable display order. Whitelist entries with no matching
    ``.. comp::`` scan result are silently ignored (caller may want to
    warn).
    """
    result: list[dict] = []
    for entry in getattr(env, "module_verification_report_needs", []):
        if entry.get("directive") != "comp":
            continue
        need_id = entry.get("id", "")
        if need_id not in whitelist:
            continue
        required_version = whitelist[need_id]
        if required_version is not None and entry.get("version") != required_version:
            continue
        slug = (
            need_id[len(component_prefix):]
            if need_id.startswith(component_prefix)
            else need_id
        )
        result.append(
            {
                "id": need_id,
                "slug": slug,
                "title": entry.get("title") or need_id,
            }
        )
    result.sort(key=lambda c: c["id"])
    return result


# ---------------------------------------------------------------------------
# RST rendering
# ---------------------------------------------------------------------------

_COMPONENT_TEMPLATE = """
.. _{ref}:

{title}
{title_underline}

.. raw:: html

   <hr style="border-top: 2px solid #333333; margin: 0.5em 0 1.5em 0;">

Component Requirements Statistics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. grid:: 1 2 2 2
   :gutter: 3

   .. grid-item::

      .. needpie:: {title} Requirements Status
         :labels: valid, invalid
         :colors: #37a12d, #ca2828
         :legend:

         type == "comp_req" and "{comp_id}" in satisfied_by and status == "valid"
         type == "comp_req" and "{comp_id}" in satisfied_by and status == "invalid"

   .. grid-item::

      .. needpie:: {title} Requirements Test Coverage
         :labels: fully covered, partially covered, not covered
         :colors: #37a12d, #f0a500, #ca2828
         :legend:

         type == "comp_req" and "{comp_id}" in satisfied_by and ("fully_verifies_back" in locals() and len(fully_verifies_back) > 0)
         type == "comp_req" and "{comp_id}" in satisfied_by and ("partially_verifies_back" in locals() and len(partially_verifies_back) > 0) and not ("fully_verifies_back" in locals() and len(fully_verifies_back) > 0)
         type == "comp_req" and "{comp_id}" in satisfied_by and not ("fully_verifies_back" in locals() and len(fully_verifies_back) > 0) and not ("partially_verifies_back" in locals() and len(partially_verifies_back) > 0)

Component Architecture Statistics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. grid:: 1 2 2 2
   :gutter: 3

   .. grid-item::

      .. needpie:: {title} Architecture Elements Status
         :labels: valid, invalid
         :colors: #37a12d, #ca2828
         :legend:

         type in ["comp_arc_sta", "comp_arc_dyn"] and "{comp_id}" in belongs_to and status == "valid"
         type in ["comp_arc_sta", "comp_arc_dyn"] and "{comp_id}" in belongs_to and status == "invalid"

   .. grid-item::

      .. needpie:: {title} Architecture Elements Inspection Status
         :labels: inspected, not inspected
         :colors: #37a12d, #ca2828
         :legend:

         type in ["comp_arc_sta", "comp_arc_dyn"] and "{comp_id}" in belongs_to and "inspected" in tags
         type in ["comp_arc_sta", "comp_arc_dyn"] and "{comp_id}" in belongs_to and "inspected" not in tags

Requirements Traceability
^^^^^^^^^^^^^^^^^^^^^^^^^

The following table lists all requirements of this component together with their
verification status and the tests that (fully or partially) verify them:

.. dropdown:: Show requirements table
   :animate: fade-in

   .. needtable::
      :filter: type == "comp_req" and "{comp_id}" in satisfied_by
      :style: table
      :columns: id;title;safety;status;fully_verifies_back;partially_verifies_back
      :colwidths: 13,22,8,10,23,24
      :sort: id

Architectural Elements
^^^^^^^^^^^^^^^^^^^^^^

The following table lists the architectural elements of this component
together with their inspection status. Elements that have been formally
inspected carry the ``inspected`` tag; elements without that tag have not
yet been inspected.

.. dropdown:: Show architectural elements table
   :animate: fade-in

   .. needtable::
      :filter: type in ["comp_arc_sta", "comp_arc_dyn"] and "{comp_id}" in belongs_to
      :style: table
      :columns: id;title;safety;status;tags
      :colwidths: 25,30,10,15,20
      :sort: id

Verification & Safety Analysis Documents
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Presence of the standard verification and safety analysis work products for
this component. A dash (``\u2014``) means the corresponding document is missing.

.. dropdown:: Show work products table
   :animate: fade-in

   .. list-table::
      :header-rows: 1
      :widths: 30 25 25 20
      :class: wp-doc-table

      * - Work Product
        - Kind
        - Realized by
        - Status
{workproduct_rows}
"""


# Kept for later re-activation. To re-enable the Unit Test Coverage
# section, append this fragment to ``_COMPONENT_TEMPLATE`` and restore
# the ``coverage_intro=_coverage_intro(comp, coverage_data)`` kwarg in
# ``_render_component``.
_COMPONENT_COVERAGE_SECTION_DISABLED = """\

Unit Test Coverage
^^^^^^^^^^^^^^^^^^

{coverage_intro}
.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Metric
     - Coverage
   * - Lines
     - |coverage_{slug}_lines|
   * - Functions
     - |coverage_{slug}_functions|
   * - Branches
     - |coverage_{slug}_branches|
"""


_COVERAGE_INTRO_MEASURED = (
    "Aggregated from ``bazel coverage``. Regenerate via\n"
    "``python3 tools/extract_coverage.py \"$(bazel info output_path)"
    "/_coverage/_coverage_report.dat\" docs/reporting/coverage_summary.json``.\n"
)
_COVERAGE_INTRO_SPEC_ONLY = (
    "This component is specification-only and has no dedicated unit\n"
    "test binary in ``//score/\u2026``.\n"
)

_COVERAGE_SUMMARY_REL_PATH = os.path.join("reporting", "coverage_summary.json")


def _load_coverage_summary(env) -> dict:
    """Return the parsed ``coverage_summary.json`` (empty dict on failure).

    The JSON is produced by ``tools/extract_coverage.py`` from an LCOV
    report. Its top-level keys are component slugs (matching
    ``comp__<module>_<slug>`` in the sphinx-needs data). Presence of a
    slug with real metric values marks that component as *measured*;
    absence marks it as *specification-only*.
    """
    path = os.path.join(env.srcdir, _COVERAGE_SUMMARY_REL_PATH)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    if os.path.isfile(path):
        env.note_dependency(path)
    return data or {}


_DEFAULT_WORKPRODUCTS = [
    {"key": "requirements_inspect", "label": "Requirements Inspection",
     "wp_id": "wp__requirements_inspect"},
    {"key": "sw_arch_verification", "label": "Architecture Inspection",
     "wp_id": "wp__sw_arch_verification"},
    {"key": "sw_implementation_inspection", "label": "Implementation Inspection",
     "wp_id": "wp__sw_implementation_inspection"},
    {"key": "sw_component_dfa", "label": "DFA",
     "wp_id": "wp__sw_component_dfa"},
    {"key": "sw_component_fmea", "label": "FMEA",
     "wp_id": "wp__sw_component_fmea"},
]


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _workproduct_rows(
    slug_norm: str,
    overrides: dict,
    workproducts: list[dict],
) -> str:
    """Render the work-product rows for one component or the feature.

    Each row has four cells: the work-product ``:need:`` link, its
    label, the realising document, and its status. The "Realized by"
    and "Status" cells are populated by sphinx-needs so their content
    stays in sync with the actual sphinx-needs data model:

    1. **Overrides** — when ``overrides['workproducts'][wp_key]`` names
       an explicit doc id, the row renders a direct ``:need:`` link
       and a ``:ndf:`copy('status', ...)``` call that pulls the doc's
       status field verbatim.
    2. **Filter** — otherwise, both cells render a ``.. needtable::``
       with the same filter (``type == "document"``, normalised-slug
       substring match on the doc id, ``realizes`` link containing
       ``wp['wp_id']``) but different ``:columns:``. If nothing matches,
       both cells are empty.
    """
    explicit = overrides.get("workproducts") or {}
    lines: list[str] = []
    for wp in workproducts:
        override_doc = explicit.get(wp["key"])
        lines.append(f"      * - :need:`{wp['wp_id']}`")
        lines.append(f"        - {wp['label']}")
        if override_doc:
            lines.append(f"        - :need:`{override_doc}`")
            lines.append(
                f"        - :ndf:`copy('status', "
                f"need_id='{override_doc}')`"
            )
        else:
            filter_expr = (
                f"type == \"document\" and "
                f"\"{slug_norm}\" in id.replace(\"_\", \"\") and "
                f"\"{wp['wp_id']}\" in realizes"
            )
            lines.append("        - .. needtable::")
            lines.append(f"             :filter: {filter_expr}")
            lines.append("             :columns: id")
            lines.append("             :style: table")
            lines.append("        - .. needtable::")
            lines.append(f"             :filter: {filter_expr}")
            lines.append("             :columns: status")
            lines.append("             :style: table")
    return "\n".join(lines)


def _coverage_intro(comp: dict, coverage_data: dict) -> str:
    """Choose the intro paragraph based on ``coverage_summary.json``.

    A component counts as *measured* iff its slug appears in the JSON
    with at least one non-null metric percentage. Otherwise it is
    treated as specification-only. This mirrors how the
    ``|coverage_<slug>_*|`` substitutions in ``conf.py`` decide between
    numeric output and ``"not measured"``.
    """
    entry = coverage_data.get(comp["slug"]) or {}
    measured = any(
        entry.get(f"{m}_pct") is not None
        for m in ("lines", "functions", "branches")
    )
    return (_COVERAGE_INTRO_MEASURED if measured else _COVERAGE_INTRO_SPEC_ONLY) + "\n"


def _render_component(
    comp: dict,
    overrides: dict,
    workproducts: list[dict],
    coverage_data: dict,
) -> str:
    title = comp["title"]
    slug = comp["slug"]
    ref = "comp-" + _slugify(title)
    return _COMPONENT_TEMPLATE.format(
        ref=ref,
        title=title,
        title_underline="~" * len(title),
        comp_id=comp["id"],
        slug=slug,
        workproduct_rows=_workproduct_rows(
            _normalize_slug(slug), overrides, workproducts
        ),
        # Unit Test Coverage section disabled — see
        # ``_COMPONENT_COVERAGE_SECTION_DISABLED``. Restore by passing
        # ``coverage_intro=_coverage_intro(comp, coverage_data)``.
    )


_DEFAULT_FEATURE_WORKPRODUCTS = [
    {"key": "requirements_inspect", "label": "Requirements Inspection",
     "wp_id": "wp__requirements_inspect"},
    {"key": "sw_arch_verification", "label": "Architecture Inspection",
     "wp_id": "wp__sw_arch_verification"},
]


_FEATURE_TEMPLATE = """\
Feature
-------

.. needtable::
   :filter: id == "{feature_id}"
   :columns: title as "Name";id as "Id";safety;security;status
   :style: table

Feature Requirements Statistics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. grid:: 1 2 2 2
   :gutter: 3

   .. grid-item::

      .. needpie:: Feature Requirements Status
         :labels: valid, invalid
         :colors: #37a12d, #ca2828
         :legend:

         type == "feat_req" and "{feature_id}" in satisfied_by and status == "valid"
         type == "feat_req" and "{feature_id}" in satisfied_by and status == "invalid"

   .. grid-item::

      .. needpie:: Feature Requirements Test Coverage
         :labels: fully covered, partially covered, not covered
         :colors: #37a12d, #f0a500, #ca2828
         :legend:

         type == "feat_req" and "{feature_id}" in satisfied_by and ("fully_verifies_back" in locals() and len(fully_verifies_back) > 0)
         type == "feat_req" and "{feature_id}" in satisfied_by and ("partially_verifies_back" in locals() and len(partially_verifies_back) > 0) and not ("fully_verifies_back" in locals() and len(fully_verifies_back) > 0)
         type == "feat_req" and "{feature_id}" in satisfied_by and not ("fully_verifies_back" in locals() and len(fully_verifies_back) > 0) and not ("partially_verifies_back" in locals() and len(partially_verifies_back) > 0)

.. dropdown:: Show requirements table
   :animate: fade-in

   .. needtable::
      :filter: type == "feat_req" and "{feature_id}" in satisfied_by
      :style: table
      :columns: id;title;safety;status;fully_verifies_back;partially_verifies_back
      :colwidths: 13,22,8,10,23,24
      :sort: id

Feature Architecture Statistics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. grid:: 1 2 2 2
   :gutter: 3

   .. grid-item::

      .. needpie:: Feature Architecture Elements Status
         :labels: valid, invalid
         :colors: #37a12d, #ca2828
         :legend:

         type in ["feat_arc_sta", "feat_arc_dyn"] and "{feature_id}" in belongs_to and status == "valid"
         type in ["feat_arc_sta", "feat_arc_dyn"] and "{feature_id}" in belongs_to and status == "invalid"

   .. grid-item::

      .. needpie:: Feature Architecture Elements Inspection Status
         :labels: inspected, not inspected
         :colors: #37a12d, #ca2828
         :legend:

         type in ["feat_arc_sta", "feat_arc_dyn"] and "{feature_id}" in belongs_to and "inspected" in tags
         type in ["feat_arc_sta", "feat_arc_dyn"] and "{feature_id}" in belongs_to and "inspected" not in tags

.. dropdown:: Show architectural elements table
   :animate: fade-in

   .. needtable::
      :filter: type in ["feat_arc_sta", "feat_arc_dyn"] and "{feature_id}" in belongs_to
      :style: table
      :columns: id;title;safety;status;tags
      :colwidths: 25,30,10,15,20
      :sort: id

Feature Inspection Statistics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Presence of the feature-level inspection work products.

.. dropdown:: Show work products table
   :animate: fade-in

   .. list-table::
      :header-rows: 1
      :widths: 30 25 25 20
      :class: wp-doc-table

      * - Work Product
        - Kind
        - Realized by
        - Status
{feature_workproduct_rows}
"""


def _render_feature(
    feature_id: str,
    feature_slug: str,
    feature_overrides: dict,
    feature_workproducts: list[dict],
) -> str:
    """Render the ``Feature`` section (Requirements / Architecture /
    Inspection Statistics), delegating all attribute filtering to
    sphinx-needs.

    Feature statistics filter ``feat_req`` / ``feat_arc_*`` by
    ``"{feature_id}" in belongs_to`` — the same link that the source
    RST declares — so the report tracks the sphinx-needs data model
    directly instead of guessing from id substrings. The Feature summary
    ``needtable`` pulls title / safety / security / status from the
    ``feat__*`` need itself. The Inspection Statistics work-product
    rows still substring-match the ``feature_slug`` against document
    ids because documents have no direct link back to the feature.
    """
    return _FEATURE_TEMPLATE.format(
        feature_id=feature_id,
        feature_slug=feature_slug,
        feature_workproduct_rows=_workproduct_rows(
            _normalize_slug(feature_slug),
            feature_overrides,
            feature_workproducts,
        ),
    )


_COMPONENTS_HEADER = """\
Components
----------

"""


# Hide the auto-generated header / chrome of the inner ``.. needtable::``
# widgets that render the "Realized by" / "Status" cells of the WP tables.
# Without this the cells show a nested table with its own "ID" / "Status"
# header row and datatables toolbar, which is visually noisy for a single
# value. Scoped to ``.wp-doc-table`` set as the outer list-table's class.
_WP_TABLE_CSS = """\
.. raw:: html

   <style>
   .wp-doc-table td .needstable_wrapper,
   .wp-doc-table td .pst-scrollable-table-container {
       margin: 0; padding: 0; overflow: visible;
   }
   .wp-doc-table td table.NEEDS_TABLE,
   .wp-doc-table td table.NEEDS_DATATABLES {
       border: 0; margin: 0; box-shadow: none; background: transparent;
       width: auto;
   }
   .wp-doc-table td table.NEEDS_TABLE thead,
   .wp-doc-table td table.NEEDS_DATATABLES thead { display: none; }
   .wp-doc-table td table.NEEDS_TABLE tbody tr,
   .wp-doc-table td table.NEEDS_DATATABLES tbody tr { background: transparent; }
   .wp-doc-table td table.NEEDS_TABLE tbody td,
   .wp-doc-table td table.NEEDS_DATATABLES tbody td {
       border: 0; padding: 0; background: transparent;
   }
   .wp-doc-table td .dataTables_wrapper .dataTables_length,
   .wp-doc-table td .dataTables_wrapper .dataTables_filter,
   .wp-doc-table td .dataTables_wrapper .dataTables_info,
   .wp-doc-table td .dataTables_wrapper .dataTables_paginate { display: none; }
   </style>
"""


_OVERVIEW_TEMPLATE = """\
Component Overview
~~~~~~~~~~~~~~~~~~

.. needtable::
   :filter: id in {ids_literal}
   :columns: id as "Component";safety;security;status
   :style: table
   :sort: id
"""


def _render_overview(components: list[dict]) -> str:
    """Render the component overview as a ``.. needtable::``.

    Delegating to sphinx-needs means ``safety``/``security``/``status``
    come from its data model (validated, normalised, consistent with the
    rest of the site) rather than from raw strings scraped by our
    filesystem scan. Trade-off: the ``Component`` cell links to the
    need's detail page, not to the per-component section further down
    this page.
    """
    ids_literal = "[" + ", ".join(f'"{c["id"]}"' for c in components) + "]"
    return _OVERVIEW_TEMPLATE.format(ids_literal=ids_literal)


def _render_report(
    components: list[dict],
    feature_id: str,
    feature_slug: str,
    overrides_by_id: dict[str, dict],
    workproducts: list[dict],
    feature_workproducts: list[dict],
    coverage_data: dict,
) -> str:
    feature_overrides = overrides_by_id.get(feature_id, {})
    parts = [
        _WP_TABLE_CSS,
        _render_feature(
            feature_id, feature_slug, feature_overrides, feature_workproducts
        ),
        _COMPONENTS_HEADER,
        _render_overview(components),
    ]
    for comp in components:
        overrides = overrides_by_id.get(comp["id"], {})
        parts.append(
            _render_component(
                comp,
                overrides,
                workproducts,
                coverage_data,
            )
        )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Sphinx directive
# ---------------------------------------------------------------------------


class ModuleVerificationReportDirective(SphinxDirective):
    """Expand to the per-module verification report body.

    Discovers components dynamically from the sphinx-needs data model by
    filtering all needs by ``type == "comp"`` and
    ``id.startswith(component_prefix)``.
    """

    required_arguments = 0
    optional_arguments = 0
    option_spec = {"config": str}
    has_content = False

    def _load_config(self, rel_config: str | None) -> dict:
        if not rel_config:
            return {}
        srcdir = self.env.srcdir
        config_path = os.path.join(srcdir, rel_config)
        if not os.path.isfile(config_path):
            self.state_machine.reporter.warning(
                f"module-verification-report: config not found: {config_path}",
                line=self.lineno,
            )
            return {}
        with open(config_path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        self.env.note_dependency(config_path)
        return data

    def run(self) -> list[nodes.Node]:
        config = self._load_config(self.options.get("config"))

        module_id = config.get("module_id", "")
        component_prefix = config.get("component_prefix") or (
            "comp__" + module_id[len("mod__"):] + "_"
            if module_id.startswith("mod__")
            else "comp__"
        )
        module_short = (
            module_id[len("mod__"):]
            if module_id.startswith("mod__")
            else module_id
        )
        feature_id = config.get("feature_id") or f"feat__{module_short}"
        feature_slug = (
            feature_id.split("__", 1)[1]
            if "__" in feature_id
            else feature_id
        )
        workproducts = config.get("workproducts") or _DEFAULT_WORKPRODUCTS
        feature_workproducts = (
            config.get("feature_workproducts") or _DEFAULT_FEATURE_WORKPRODUCTS
        )
        overrides_by_id: dict[str, dict] = config.get("overrides") or {}

        all_needs = getattr(self.env, "module_verification_report_needs", [])
        include_ids = _module_includes(all_needs, module_id)
        if include_ids is None:
            error = self.state_machine.reporter.error(
                f"module-verification-report: no '.. mod::' need with "
                f"id '{module_id}' found in the source tree "
                f"(is 'module_id' set correctly in the config?)",
                line=self.lineno,
            )
            return [error]

        components = _discover_components(
            self.env, component_prefix, include_ids
        )
        missing = set(include_ids) - {c["id"] for c in components}
        for m in sorted(missing):
            required = include_ids[m]
            hint = f" (version=={required})" if required else ""
            self.state_machine.reporter.warning(
                f"module-verification-report: '{module_id}' includes "
                f"'{m}'{hint} but no matching '.. comp::' need was found",
                line=self.lineno,
            )
        if not components:
            error = self.state_machine.reporter.error(
                f"module-verification-report: '{module_id}' has no "
                f"resolvable components in ':includes:'",
                line=self.lineno,
            )
            return [error]

        coverage_data = _load_coverage_summary(self.env)

        rst_text = _render_report(
            components,
            feature_id,
            feature_slug,
            overrides_by_id,
            workproducts,
            feature_workproducts,
            coverage_data,
        )
        view_list = ViewList()
        source = "<module-verification-report>"
        for lineno, line in enumerate(rst_text.splitlines()):
            view_list.append(line, source, lineno)

        # Parse into a plain container (not a ``nodes.section``): a section
        # wrapper would push every heading we emit one level deeper than the
        # surrounding document sections, so ``Component Overview`` would
        # render as ``<h4>`` instead of ``<h3>`` alongside
        # ``Feature Requirements Statistics``.
        container = nodes.container()
        container.document = self.state.document
        nested_parse_with_titles(self.state, view_list, container)
        return container.children


def _scan_source_tree(app, env, docnames):
    """Cache a filesystem scan of all ``.. mod::`` and ``.. comp::``
    needs on ``env`` so the directive can enumerate its components in
    every process of a parallel build.
    """
    env.module_verification_report_needs = _scan_rst_needs(
        env.srcdir, directives={"mod", "comp"}
    )


def setup(app: Any) -> dict:
    app.add_directive(
        "module-verification-report", ModuleVerificationReportDirective
    )
    app.connect("env-before-read-docs", _scan_source_tree)
    return {
        "version": "0.6",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
