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
"""Rendering helpers for the module verification report.

Everything here is a string transformation.  No function in this module
receives, reads or resolves a Need.  That is the governing design rule:

    The extension emits RST.  It never reads the Need model to compute an
    answer.

The report body lives in ``src/needs_templates/mod_ver_report.need`` -- a
Sphinx-Needs template file, resolved through ``needs_template_folder``.  The
template owns the report's content *and* its section structure; this module
only builds the context and safely quotes the need ids that end up inside
filter strings.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

#: Sphinx-Needs templates end in ``.need`` and live in ``needs_template_folder``.
TEMPLATE_NAME = "mod_ver_report.need"

# Conservative allow-list for anything interpolated into a sphinx-needs filter
# string.  Filters are evaluated as Python, so a need id is never pasted in
# unchecked.
NEED_ID_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")

# ``comp__foo[version==1]``. sphinx-needs strips these itself on real link
# fields; we must not silently drop them while building sections, or the
# section is built for something the author did not write.
VERSION_QUALIFIER_RE = re.compile(r"\[[^\]]*\]$")

_SPLIT_RE = re.compile(r"[,\s]+")


def quote_for_filter(need_id: str) -> str:
    """Return *need_id* as a safely quoted literal for a needs filter string.

    Raises ``ValueError`` for anything that is not a plain need id; callers
    turn that into a Sphinx warning.
    """
    if not NEED_ID_RE.match(need_id):
        raise ValueError(f"{need_id!r} is not a valid need id")
    return json.dumps(need_id)


def parse_ids(raw: str | None) -> tuple[list[str], list[str]]:
    """Parse a link option into an ordered, de-duplicated list of ids.

    Returns ``(ids, warnings)``.  Accepts comma and/or whitespace separated ids
    across lines.  Version qualifiers are reported rather than silently
    ignored, and duplicates are dropped deterministically.
    """
    ids: list[str] = []
    warnings: list[str] = []
    for token in _SPLIT_RE.split((raw or "").strip()):
        if not token:
            continue
        need_id = VERSION_QUALIFIER_RE.sub("", token)
        if need_id != token:
            warnings.append(
                f"ignoring version qualifier on {token!r}; the report section "
                f"is built for {need_id!r}"
            )
        if not NEED_ID_RE.match(need_id):
            warnings.append(f"{need_id!r} is not a valid need id and is skipped")
        elif need_id in ids:
            warnings.append(f"duplicate entry {need_id!r} is listed once")
        else:
            ids.append(need_id)
    return ids, warnings


def parse_titles(raw: str | None) -> tuple[dict[str, str], list[str]]:
    """Parse the ``:titles:`` option: one ``<need id> = <heading>`` per line."""
    titles: dict[str, str] = {}
    warnings: list[str] = []
    for line in (raw or "").splitlines():
        need_id, sep, title = line.partition("=")
        need_id, title = need_id.strip(), title.strip()
        if not line.strip():
            continue
        if not sep or not need_id or not title:
            warnings.append(
                f"cannot parse title {line.strip()!r}; expected 'id = Title'"
            )
        else:
            titles[need_id] = title
    return titles, warnings


def derive_title(need_id: str) -> str:
    """Last-resort heading for a component without an explicit ``:titles:``.

    Intentionally dumb.  The real title lives on the Need and is rendered by
    the component table inside the section, resolved by sphinx-needs.
    ``comp__baselibs_json`` becoming "Baselibs Json" is an accepted fallback.
    """
    slug = need_id.partition("__")[2] or need_id
    return slug.replace("_", " ").strip().title() or need_id


def derive_feature_id(module_id: str) -> str:
    """``mod__baselibs`` -> ``feat__baselibs``, as the upstream template does.

    An exact, total rewrite of one id into another, feeding an ``id == ...``
    filter -- so the worst case is an empty feature table, never a wrong match.
    """
    return (
        "feat__" + module_id.removeprefix("mod__")
        if module_id.startswith("mod__")
        else ""
    )


def derive_slug(need_id: str, module_id: str) -> str:
    """Matching key for the work-product documents of *need_id*.

    Mirrors the upstream template: drop the type prefix and the module name,
    then remove underscores and lowercase.  This is substring matching and can
    produce false positives; see the README's "Known gaps".
    """
    tail = need_id.partition("__")[2] or need_id
    module_short = module_id.removeprefix("mod__")
    if module_short:
        tail = tail.removeprefix(f"{module_short}_")
    return tail.replace("_", "").lower()


def render_need(
    directive_name: str,
    title: str,
    options: dict[str, str | None],
    content: list[str],
) -> str:
    """Render the ``mod_ver_report`` Need itself.

    Options are passed through verbatim: the metamodel -- not this extension --
    decides which are mandatory, which are links and what they may point at.
    """
    lines = [f".. {directive_name}:: {title}"]
    lines += [f"   :{k}: {'' if v is None else v}" for k, v in options.items()]
    if content:
        lines.append("")
        lines += [f"   {line}" if line else "" for line in content]
    return "\n".join(lines) + "\n"


def shipped_template_folder() -> Path:
    """The Sphinx-Needs template folder shipped with docs-as-code.

    Derived from this file's location so it resolves in the workspace, in Bazel
    runfiles and in the sandbox alike -- the same approach
    ``score_sphinx_bundle`` uses for the very same directory.
    """
    folder = Path(__file__).parents[2] / "needs_templates"
    if not folder.is_dir():
        raise FileNotFoundError(f"Needs template folder does not exist: {folder}")
    return folder


@lru_cache(maxsize=4)
def _environment(folders: tuple[str, ...]) -> Environment:
    env = Environment(
        loader=FileSystemLoader(list(folders)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        autoescape=False,  # noqa: S701 - RST output, not HTML
    )
    env.filters["q"] = quote_for_filter
    return env


def render_report(context: dict[str, Any], template_folder: str | None) -> str:
    """Render the report body.

    *template_folder* is the project's ``needs_template_folder``.  It is
    searched first, so a project overrides the report by dropping its own
    ``mod_ver_report.need`` in there; the shipped folder is the fallback.
    """
    shipped = str(shipped_template_folder())
    folders = dict.fromkeys(
        [template_folder, shipped] if template_folder else [shipped]
    )
    return _environment(tuple(folders)).get_template(TEMPLATE_NAME).render(**context)
