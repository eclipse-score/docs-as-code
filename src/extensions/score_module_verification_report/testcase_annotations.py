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
"""Post-processing hook that decorates ``testcase__…`` back-links inside a
rendered module verification report with a coloured
``(passed)`` / ``(failed)`` badge derived from each testcase need's
``result`` field.

The hook is a no-op unless the directive actually ran on the current
document — the directive registers its ``docname`` in
``env.module_verification_report_docnames`` so unrelated pages are left
untouched.
"""

from __future__ import annotations

from typing import Any

from docutils import nodes

# Colours match the pie-chart palette used by the report body.
RESULT_COLORS = {
    "passed": "#37a12d",
    "failed": "#ca2828",
    "skipped": "#f0a500",
    "disabled": "#888888",
}
_FALLBACK_COLOR = "#666666"


def _needs_view(env: Any):
    """Return the sphinx-needs ``NeedsView`` for ``env`` or ``None`` if
    sphinx-needs is not available / not initialised yet."""
    try:
        from sphinx_needs.data import SphinxNeedsData
    except ImportError:
        return None
    try:
        return SphinxNeedsData(env).get_needs_view()
    except Exception:
        return None


def annotate_testcase_results(app, doctree, docname):
    """``doctree-resolved`` handler: append a coloured ``(<result>)`` span
    to every reference whose visible text starts with ``testcase__`` on
    pages where the module-verification-report directive was rendered."""
    docnames = getattr(app.env, "module_verification_report_docnames", None)
    if not docnames or docname not in docnames:
        return

    needs = _needs_view(app.env)
    if needs is None:
        return

    for ref in list(doctree.findall(nodes.reference)):
        if not ref.children:
            continue
        first = ref.children[0]
        if not isinstance(first, nodes.Text):
            continue
        text = first.astext()
        if not text.startswith("testcase__"):
            continue
        need = needs.get(text)
        if not need:
            continue
        result = need.get("result") or ""
        if not result:
            continue
        color = RESULT_COLORS.get(result, _FALLBACK_COLOR)
        status_html = f'<span style="color:{color};font-weight:bold"> ({result})</span>'
        # Keep the id text, append the coloured status inline.
        ref.replace(first, nodes.Text(text))
        ref.append(nodes.raw("", status_html, format="html"))


def init_docnames(app, env, docnames):
    """``env-before-read-docs`` handler: make sure the tracking set
    exists on the shared env before parallel workers fork off."""
    if not hasattr(env, "module_verification_report_docnames"):
        env.module_verification_report_docnames = set()


def purge_docname(app, env, docname):
    """``env-purge-doc`` handler: drop stale entries on incremental
    rebuilds so re-reads re-register themselves."""
    docnames = getattr(env, "module_verification_report_docnames", None)
    if docnames is not None:
        docnames.discard(docname)


def merge_docnames(app, env, docnames, other):
    """``env-merge-info`` handler: union the per-worker sets back into
    the main env when Sphinx runs a parallel read."""
    main = getattr(env, "module_verification_report_docnames", set())
    extra = getattr(other, "module_verification_report_docnames", set())
    env.module_verification_report_docnames = main | extra
