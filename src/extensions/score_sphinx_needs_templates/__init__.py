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

_template_environment: BuildEnvironment | None = None
# Post-templates containing this marker need a second read after parallel Need
# collection has been merged.
_RENDER_AFTER_NEEDS_COLLECTION_MARKER = "score: render-after-needs-collection"


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
        source = _find_need(needs, need_id)
        if source is None:
            return []

        linked: list[NeedItem] = []
        for link in source.get_links(link_name, as_str=False):
            target = _find_need(needs, link.id)
            if target is not None:
                linked.append(target)
        return linked


_linked_needs_callable = _LinkedNeeds()


def _complex_post_template_names(app: Sphinx) -> set[str]:
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


def _rerender_pages_with_complex_post_templates(
    app: Sphinx, env: BuildEnvironment
) -> list[str]:
    """Re-read marked post-template pages after Need environments are merged.

    Post-templates are expanded while source documents are read. A parallel
    worker cannot see Needs collected by other workers at that point. Marked
    pages are therefore purged and read once more from the main environment
    before Sphinx-Needs post-processing begins.
    """
    if app.builder.name != "html":
        return []

    complex_post_templates = _complex_post_template_names(app)
    if not complex_post_templates:
        return []

    needs_data = SphinxNeedsData(env)
    if needs_data.needs_is_post_processed:
        return []

    complex_post_template_docs: set[str] = set()
    for need in needs_data.get_needs_mutable().values():
        post_template = need.get("post_template")
        if (
            not isinstance(post_template, str)
            or post_template not in complex_post_templates
        ):
            continue
        docname = need["docname"]
        if isinstance(docname, str) and docname:
            complex_post_template_docs.add(docname)

    pages_to_rerender = sorted(complex_post_template_docs)
    for docname in pages_to_rerender:
        app.events.emit("env-purge-doc", env, docname)
        env.clear_doc(docname)
        app.builder.read_doc(docname)

    return pages_to_rerender


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
    app.connect("env-updated", _rerender_pages_with_complex_post_templates)

    return {
        "version": "1.0.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
