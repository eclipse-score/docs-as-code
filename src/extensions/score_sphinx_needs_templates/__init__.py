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

from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx_needs.data import SphinxNeedsData
from sphinx_needs.need_item import NeedItem

from src.helper_lib import config_setdefault

_build_environment: BuildEnvironment | None = None
# Post-templates containing this marker need a second read after parallel Need
# collection has been merged.
_RENDER_AFTER_NEEDS_COLLECTION_MARKER = "score: render-after-needs-collection"
# During that second read, ``env.clear_doc()`` temporarily removes all Needs
# belonging to the document from Sphinx's collection. Keep those temporarily
# removed Needs available so templates can resolve links while the document is
# reread.
_temporarily_removed_needs: dict[str, NeedItem] = {}


def _base_need_id(need_id: str) -> str:
    """Strip link conditions from an ID used to look up a merged Need."""
    return need_id.split("[", 1)[0]


def _find_need(needs: dict[str, NeedItem], need_id: str) -> NeedItem | None:
    """Find a Need by its address, tolerating version-qualified collection keys."""
    base_id = _base_need_id(need_id)
    for candidate_id in (need_id, base_id):
        candidate = needs.get(candidate_id)
        if candidate is not None:
            return candidate

    # Some imported collections use a qualified dictionary key even though the
    # NeedItem itself keeps the canonical, unqualified ID.
    for candidate_id, candidate in needs.items():
        if _base_need_id(candidate_id) == base_id or candidate["id"] == base_id:
            return candidate
    return None


def _get_available_needs() -> dict[str, NeedItem]:
    """Return the current Needs, including temporarily removed Needs."""
    if _build_environment is None:
        return {}

    needs = SphinxNeedsData(_build_environment).get_needs_mutable()
    if _temporarily_removed_needs:
        needs = dict(needs)
        needs.update(_temporarily_removed_needs)
    return needs


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
    ``NeedItem`` objects in the order declared by the source Need. Backlink
    fields ending in ``_back`` are also supported. This lets a template derive
    sections from the Need graph instead of embedding IDs.

    The object is deliberately a top-level class instance because Sphinx puts
    the render context into its parallel-reader configuration. A plain
    function would make that configuration unpickleable. The build environment
    is kept process-local and captured once Sphinx has created ``app.env``.
    """

    def __call__(self, need_id: str, link_name: str) -> list[NeedItem]:
        needs = _get_available_needs()
        if not needs:
            return []

        source = _find_need(needs, need_id)
        if link_name.endswith("_back"):
            link_type = link_name.removesuffix("_back")
            if source is not None:
                links = source.get_backlinks(link_type, as_str=False)
                if links:
                    return [
                        target
                        for link in links
                        if (target := _find_need(needs, link.to_link_string()))
                        is not None
                    ]

            # During a post-template reread, Sphinx-Needs may not have rebuilt
            # backlink caches yet. The current Need is also not registered in
            # the environment while its own post-template is being rendered.
            # Derive the reverse relation from outgoing links so both cases
            # remain usable by graph-driven templates.
            source_id = _base_need_id(need_id)
            return [
                candidate
                for candidate in needs.values()
                if any(
                    _base_need_id(link.to_link_string()) == source_id
                    for link in candidate.get_links(link_type, as_str=False)
                )
            ]
        else:
            if source is None:
                return []
            links = source.get_links(link_name, as_str=False)

        linked: list[NeedItem] = []
        for link in links:
            target = _find_need(needs, link.to_link_string())
            if target is not None:
                linked.append(target)
        return linked


_linked_needs_callable = _LinkedNeeds()


class _NeedsOfType:
    """Provide all Needs of a given type to graph-driven templates."""

    def __call__(self, need_type: str) -> list[NeedItem]:
        return [
            need
            for need in _get_available_needs().values()
            if need["type"] == need_type
        ]


_needs_of_type_callable = _NeedsOfType()


def _post_templates_requiring_reread(app: Sphinx) -> set[str]:
    """Return post-template names opting into the post-merge rendering pass."""
    template_folder = _needs_template_folder()
    return {
        template.stem
        for template in template_folder.glob("*.need")
        if (
            _RENDER_AFTER_NEEDS_COLLECTION_MARKER
            in template.read_text(encoding="utf-8")
        )
    }


def _reread_post_template_pages(app: Sphinx, env: BuildEnvironment) -> list[str]:
    """Re-read marked post-template pages after Need environments are merged.

    Post-templates are expanded while source documents are read. A parallel
    worker cannot see Needs collected by other workers at that point. Marked
    pages are therefore purged and read once more from the main environment
    before Sphinx-Needs post-processing begins.
    """
    if app.builder.name != "html":
        return []

    post_templates_requiring_reread = _post_templates_requiring_reread(app)
    if not post_templates_requiring_reread:
        return []

    needs_data = SphinxNeedsData(env)
    if needs_data.needs_is_post_processed:
        return []

    post_template_docs: set[str] = set()
    for need in needs_data.get_needs_mutable().values():
        post_template = need.get("post_template")
        if (
            not isinstance(post_template, str)
            or post_template not in post_templates_requiring_reread
        ):
            continue
        docname = need["docname"]
        if isinstance(docname, str) and docname:
            post_template_docs.add(docname)

    pages_to_reread = sorted(post_template_docs)
    global _temporarily_removed_needs
    _temporarily_removed_needs = {
        need["id"]: need
        for need in needs_data.get_needs_mutable().values()
        if need.get("docname") in pages_to_reread
    }
    try:
        for docname in pages_to_reread:
            app.emit("env-purge-doc", env, docname)
            env.clear_doc(docname)
            app.builder.read_doc(docname)
    finally:
        _temporarily_removed_needs = {}

    return pages_to_reread


def _capture_build_environment(app: Sphinx) -> None:
    """Give the link helper the environment in which it should resolve Needs.

    The helper is registered during ``setup()``, but Sphinx creates ``app.env``
    only after extension setup has completed. ``builder-inited`` is the first
    lifecycle event at which the final build environment is available.
    """
    global _build_environment
    _build_environment = app.env


def setup(app: Sphinx) -> dict[str, object]:
    """Install Sphinx-Needs template helpers and the marked-page second pass."""
    app.setup_extension("sphinx_needs")

    config_setdefault(
        app.config, "needs_template_folder", str(_needs_template_folder())
    )
    app.config.needs_render_context.setdefault("linked_needs", _linked_needs_callable)
    app.config.needs_render_context.setdefault("needs_of_type", _needs_of_type_callable)
    app.connect("builder-inited", _capture_build_environment)
    # Run after the source-code linker has injected generated testcase Needs and
    # their verification backlinks (priority 525), so report templates can
    # include those testcases in their traceability tables.
    app.connect("env-updated", _reread_post_template_pages, priority=600)

    return {
        "version": "1.0.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
