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
"""Color execution results in rendered GitHub testcase links.

The ``testlink`` string-link configuration renders each link as
``<testcase name> (<result>)``. This hook replaces the plain result suffix with
the corresponding colored HTML span after sphinx-needs has created the link.
"""

from __future__ import annotations

from html import escape

from docutils import nodes
from sphinx.application import Sphinx

# Known result values get semantic classes so the stylesheet can provide
# readable colours for the current S-CORE light and dark themes.
RESULT_CLASSES = {
    "passed": "score-testcase-result--passed",
    "failed": "score-testcase-result--failed",
    "skipped": "score-testcase-result--skipped",
    "disabled": "score-testcase-result--disabled",
}
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
.score-testcase-result--disabled {
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
html[data-theme="dark"] .score-testcase-result--disabled {
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
  html:not([data-theme="light"]) .score-testcase-result--disabled {
    color: #c4cad2;
  }
}
</style>
"""


def _result_node(result_text: str, result_class: str) -> nodes.raw:
    escaped_result = escape(result_text, quote=True)
    status_html = (
        f'<span class="score-testcase-result {result_class}"> ({escaped_result})</span>'
    )
    return nodes.raw("", status_html, format="html")


def _color_existing_result_suffix(ref: nodes.reference) -> bool:
    """Replace a recognized ``(result)`` suffix with a colored node."""
    if not ref.children or not isinstance(ref.children[-1], nodes.Text):
        return False

    last_text = ref.children[-1]
    text = last_text.astext()
    for result_text, result_class in RESULT_CLASSES.items():
        suffix = f" ({result_text})"
        if text.endswith(suffix):
            prefix = text[: -len(suffix)]
            ref.replace(last_text, nodes.Text(prefix))
            ref.append(_result_node(result_text, result_class))
            return True
    return False


def annotate_testcase_results(
    app: Sphinx, doctree: nodes.document, docname: str
) -> None:
    """Color rendered testcase result suffixes using the S-CORE theme palette.

    The handler runs after sphinx-needs' own ``doctree-resolved`` handlers.
    It therefore sees the external references generated for GitHub ``testlink``
    metadata, whose labels already contain the result.
    """
    del app, docname  # Required by Sphinx's event callback signature.

    # CSS applies to the whole document, so one style block is enough even if
    # the document contains many annotated references.
    css_added = False

    for ref in list(doctree.findall(nodes.reference)):
        if ref.get(_ANNOTATED_ATTR):
            # A repeated event invocation must not append another badge.
            continue

        if not _color_existing_result_suffix(ref):
            continue

        if not css_added:
            doctree.insert(0, nodes.raw("", _TESTCASE_STATUS_CSS, format="html"))
            css_added = True
        ref[_ANNOTATED_ATTR] = True
