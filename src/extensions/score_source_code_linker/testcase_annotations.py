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
"""Decorate rendered GitHub testcase links with their execution result.

Testcase needs are external needs. Their ``external_url`` is therefore also
the URL used by the ``testlink`` metadata rendered on requirements. The same
URL is used for incoming ``fully_verified_by``/``partially_verified_by`` links.
This hook handles both kinds of references: resolved need links can identify a
testcase by ``refid``, while GitHub ``testlink`` references can be matched by
their ``refuri``.

An ``external_url`` points to a repository, file, and source line. It is not
guaranteed to identify one testcase, because multiple testcases can share a
source location. ID-based references are therefore preferred; URL-only
references are annotated only when exactly one testcase matches.
"""

from __future__ import annotations

from html import escape
from typing import Any

from docutils import nodes
from sphinx_needs.data import SphinxNeedsData

# Known result values get semantic classes so the stylesheet can provide
# readable colours for both light and dark themes.
RESULT_CLASSES = {
    "passed": "score-testcase-result--passed",
    "failed": "score-testcase-result--failed",
    "skipped": "score-testcase-result--skipped",
    "disabled": "score-testcase-result--disabled",
}
# Keep an unknown result visible, but do not assign it the meaning of a known
# status such as ``passed`` or ``failed``.
_FALLBACK_CLASS = "score-testcase-result--unknown"
# The event handler is expected to be idempotent for a doctree. This marker
# prevents a second invocation from appending the same status again.
_ANNOTATED_ATTR = "score_source_code_linker_testcase_result_annotated"

# The styles are inserted into a document only when that document contains an
# annotation. Keeping them in one block avoids repeating inline style rules on
# every testcase link and lets the same classes handle theme changes.
_TESTCASE_STATUS_CSS = """
<style>
.score-testcase-result {
  font-weight: bold;
}
.score-testcase-result--passed {
  color: #146c2e;
}
.score-testcase-result--failed {
  color: #b42318;
}
.score-testcase-result--skipped {
  color: #8a5300;
}
.score-testcase-result--disabled,
.score-testcase-result--unknown {
  color: #5f6368;
}
html[data-theme="dark"] .score-testcase-result--passed {
  color: #7ee787;
}
html[data-theme="dark"] .score-testcase-result--failed {
  color: #ff7b72;
}
html[data-theme="dark"] .score-testcase-result--skipped {
  color: #d29922;
}
html[data-theme="dark"] .score-testcase-result--disabled,
html[data-theme="dark"] .score-testcase-result--unknown {
  color: #c4cad2;
}
@media (prefers-color-scheme: dark) {
  html:not([data-theme="light"]) .score-testcase-result--passed {
    color: #7ee787;
  }
  html:not([data-theme="light"]) .score-testcase-result--failed {
    color: #ff7b72;
  }
  html:not([data-theme="light"]) .score-testcase-result--skipped {
    color: #d29922;
  }
  html:not([data-theme="light"]) .score-testcase-result--disabled,
  html:not([data-theme="light"]) .score-testcase-result--unknown {
    color: #c4cad2;
  }
}
</style>
"""


def _resolved_target_need_id(ref: nodes.reference) -> str | None:
    """Return the need ID encoded in a resolved reference, if available.

    Depending on how sphinx-needs created the reference, the target is stored
    either as ``refid`` or as the fragment of a local ``refuri``. The caller
    can then perform an exact lookup before falling back to URL matching.
    """
    refid = ref.get("refid")
    if refid:
        return refid

    refuri = ref.get("refuri")
    if refuri and "#" in refuri:
        return refuri.rsplit("#", 1)[-1]

    return None


def _testcases_by_external_url(needs: Any) -> dict[str, list[dict[str, Any]]]:
    """Group testcase needs by their rendered GitHub URL without losing duplicates.

    The URL identifies a source location, not a testcase identity. Keeping a
    list is important because parameterized tests or multiple reported tests
    can point to the same file and line.
    """
    testcases_by_url: dict[str, list[dict[str, Any]]] = {}
    for need in needs.values():
        if need.get("type") != "testcase":
            continue
        external_url = need.get("external_url")
        if external_url:
            # Do not overwrite an earlier testcase with the same location.
            # _testcase_for_reference() uses the list to detect ambiguity.
            testcases_by_url.setdefault(external_url, []).append(need)
    return testcases_by_url


def _testcase_for_reference(
    ref: nodes.reference,
    needs: Any,
    testcases_by_url: dict[str, list[dict[str, Any]]],
) -> dict[str, Any] | None:
    """Resolve a reference by exact need ID or by an unambiguous external URL.

    A need ID identifies one testcase even when its source URL is shared. A
    URL-only reference is used only when it has exactly one testcase candidate;
    choosing one of several candidates could display the wrong result.
    """
    target_id = _resolved_target_need_id(ref)
    if target_id:
        target_need = needs.get(target_id)
        if target_need is not None and target_need.get("type") == "testcase":
            return target_need

    refuri = ref.get("refuri")
    if refuri:
        candidates = testcases_by_url.get(refuri, [])
        if len(candidates) == 1:
            return candidates[0]

    return None


def annotate_testcase_results(app, doctree, docname):
    """Append a coloured, theme-compatible result annotation to testcase refs.

    The handler runs after sphinx-needs' own ``doctree-resolved`` handlers.
    It therefore sees both regular resolved references and the external
    references generated for GitHub ``testlink`` metadata.

    References without a testcase match or without a result are left as they
    are. This keeps the post-processing safe when test reports are incomplete
    or when a source URL is shared by multiple testcases.
    """
    needs = SphinxNeedsData(app.env).get_needs_view()
    testcases_by_url = _testcases_by_external_url(needs)
    # CSS applies to the whole document, so one style block is enough even if
    # the document contains many annotated references.
    css_added = False

    for ref in list(doctree.findall(nodes.reference)):
        if ref.get(_ANNOTATED_ATTR):
            # A repeated event invocation must not append another badge.
            continue

        testneed = _testcase_for_reference(ref, needs, testcases_by_url)
        if testneed is None:
            continue

        result = testneed.get("result")
        if not result:
            # A missing result is not a status and must not render as ``()``.
            continue

        result_text = str(result)
        # Preserve unexpected report values as text, but use a neutral class
        # instead of presenting them as one of the known statuses.
        result_class = RESULT_CLASSES.get(result_text, _FALLBACK_CLASS)
        status_html = (
            f'<span class="score-testcase-result {result_class}"> '
            f"({escape(result_text, quote=True)})</span>"
        )
        if not css_added:
            doctree.insert(0, nodes.raw("", _TESTCASE_STATUS_CSS, format="html"))
            css_added = True
        # Preserve the existing link label and append the result annotation.
        ref.append(nodes.raw("", status_html, format="html"))
        ref[_ANNOTATED_ATTR] = True
