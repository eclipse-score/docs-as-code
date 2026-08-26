# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
from pathlib import Path

from docutils import nodes
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx_needs.data import SphinxNeedsData
from sphinx_needs.need_item import NeedItem
from sphinx_needs.nodes import Need

from src.helper_lib import config_setdefault

_template_environment: BuildEnvironment | None = None
# Templates containing this marker need a second read after parallel Need
# collection has been merged.
_RENDER_AFTER_NEEDS_COLLECTION_MARKER = "score: render-after-needs-collection"


def _needs_template_folder() -> Path:
    """Locate the shared ``.need`` template directory for Sphinx-Needs."""
    template_folder = Path(__file__).parents[2] / "needs_templates"
    if not template_folder.is_dir():
        raise FileNotFoundError(
            f"Sphinx-Needs template folder does not exist: {template_folder}"
        )
    return template_folder


class _LinkedNeeds:
    """Provide link traversal to Need templates as a pickleable callable.

    Calling the object with a Need ID and a link field returns the target
    ``NeedItem`` objects in the order declared by the source Need. This lets a
    template derive sections from the Need graph instead of embedding IDs.

    The object is deliberately a top-level class instance because Sphinx puts
    the render context into its parallel-reader configuration. A plain
    function would make that configuration unpickleable. The build environment
    is kept process-local and captured once Sphinx has created ``app.env``.
    """

    def __call__(self, need_id: str, link_name: str) -> list[NeedItem]:
        if _template_environment is None:
            return []

        needs = SphinxNeedsData(_template_environment).get_needs_mutable()
        source = needs.get(need_id)
        if source is None:
            return []

        linked: list[NeedItem] = []
        for link in source.get_links(link_name, as_str=False):
            target = needs.get(link.id)
            if target is not None:
                linked.append(target)
        return linked


_linked_needs_callable = _LinkedNeeds()


def _complex_template_names(app: Sphinx) -> set[str]:
    """Return template names opting into the post-merge rendering pass."""
    template_folder = Path(str(app.config.needs_template_folder))
    return {
        template.stem
        for template in template_folder.glob("*.need")
        if (
            _RENDER_AFTER_NEEDS_COLLECTION_MARKER
            in template.read_text(encoding="utf-8")
        )
    }


def _rerender_pages_with_complex_templates(
    app: Sphinx, env: BuildEnvironment
) -> list[str]:
    """Re-read marked pages after the parallel Need environments are merged.

    Need templates are expanded while source documents are read. A parallel
    worker cannot see Needs collected by other workers at that point. The
    marked pages are therefore purged and read once more from the main
    environment before Sphinx-Needs post-processing begins.
    """
    if app.builder.name != "html":
        return []

    complex_templates = _complex_template_names(app)
    if not complex_templates:
        return []

    needs_data = SphinxNeedsData(env)
    if needs_data.needs_is_post_processed:
        return []

    complex_template_docs: set[str] = set()
    for need in needs_data.get_needs_mutable().values():
        if need["template"] not in complex_templates:
            continue
        docname = need["docname"]
        if isinstance(docname, str) and docname:
            complex_template_docs.add(docname)

    pages_to_rerender = sorted(complex_template_docs)
    for docname in pages_to_rerender:
        app.events.emit("env-purge-doc", env, docname)
        env.clear_doc(docname)
        app.builder.read_doc(docname)

    return pages_to_rerender


def _template_rubrics(
    app: Sphinx, doctree: nodes.document, complex_templates: set[str]
) -> list[nodes.Element]:
    """Return headings rendered inside marked Need templates.

    Sphinx-Needs parses Need content with ``match_titles=False``. Consequently,
    a normal section title inside a template cannot participate in Sphinx's
    document ToC. The templates use rubrics for these headings, so those nodes
    are the reliable, already-rendered representation to expose to the ToC.
    """
    needs = SphinxNeedsData(app.env).get_needs_mutable()
    rubrics: list[nodes.Element] = []

    for need_node in doctree.findall(Need):
        need_id = need_node.get("refid")
        if not isinstance(need_id, str):
            continue

        need = needs.get(need_id)
        if need is None or need["template"] not in complex_templates:
            continue

        # Only direct rubrics are report headings. Rubrics nested in dropdowns
        # are control labels and should not become navigation entries.
        rubrics.extend(
            child for child in need_node.children if isinstance(child, nodes.rubric)
        )

    return rubrics


def _add_template_rubrics_to_toc(app: Sphinx, doctree: nodes.document) -> None:
    """Expose headings inside marked Need templates in the local page ToC.

    The regular Sphinx ToC collector deliberately ignores sections nested in
    arbitrary container nodes such as a Sphinx-Needs Need. This handler runs
    after that collector, assigns IDs directly to the rendered rubrics, and
    adds matching local references to its already-built ToC. It therefore
    changes navigation only; the generated report content stays inside the
    Need node and does not have to be moved or rendered twice.
    """
    if app.builder.name != "html":
        return

    complex_templates = _complex_template_names(app)
    if not complex_templates:
        return

    rubrics = _template_rubrics(app, doctree, complex_templates)
    if not rubrics:
        return

    docname = app.env.current_document.docname
    toc = app.env.tocs.get(docname)
    if toc is None:
        return

    used_ids = {
        node_id
        for element in doctree.findall(nodes.Element)
        for node_id in element.get("ids", [])
    }

    for rubric in rubrics:
        rubric_ids = rubric.get("ids", [])
        if rubric_ids:
            rubric_id = rubric_ids[0]
        else:
            rubric_id = nodes.make_id(f"{docname}-{rubric.astext()}")
            if not rubric_id:
                rubric_id = f"{docname}-template-heading"

            candidate = rubric_id
            suffix = 2
            while candidate in used_ids:
                candidate = f"{rubric_id}-{suffix}"
                suffix += 1
            rubric_id = candidate
            rubric["ids"] = [rubric_id]
            used_ids.add(rubric_id)

        reference = nodes.reference(
            "",
            "",
            *(child.deepcopy() for child in rubric.children),
            internal=True,
            refuri=docname,
            anchorname=f"#{rubric_id}",
        )
        toc += nodes.list_item("", addnodes.compact_paragraph("", "", reference))

    app.env.toc_num_entries[docname] += len(rubrics)


def _capture_template_environment(app: Sphinx) -> None:
    """Give the link helper the environment in which it should resolve Needs.

    The helper is registered during ``setup()``, but Sphinx creates ``app.env``
    only after extension setup has completed. ``builder-inited`` is the first
    lifecycle event at which the final build environment is available.
    """
    global _template_environment
    _template_environment = app.env


def setup(app: Sphinx) -> dict[str, object]:
    """Install Sphinx-Needs template helpers and the marked-page second pass."""
    app.setup_extension("sphinx_needs")

    config_setdefault(
        app.config, "needs_template_folder", str(_needs_template_folder())
    )
    app.config.needs_render_context.setdefault("linked_needs", _linked_needs_callable)
    app.connect("builder-inited", _capture_template_environment)
    # The priority is intentionally after Sphinx's environment collectors
    # (default 500), so the handler can augment the collector-owned ToC.
    app.connect("doctree-read", _add_template_rubrics_to_toc, priority=600)
    app.connect("env-updated", _rerender_pages_with_complex_templates)

    return {
        "version": "1.0.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
