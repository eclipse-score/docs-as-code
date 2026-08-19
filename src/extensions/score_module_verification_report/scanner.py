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
"""Filesystem scanner for ``.. mod::`` / ``.. comp::`` needs.

We deliberately do **not** query ``SphinxNeedsData`` here: doing so would
require reading the report source strictly after every source registering
a ``.. comp::`` / ``.. document::`` need, which forces
``parallel_read_safe = False`` on the extension and produces two
Sphinx-level warnings per build (``the score_module_verification_report
extension is not safe for parallel reading`` / ``doing serial read``).
Those warnings are fatal under ``-W``.

The RST directive syntax used across baselibs is stable::

    .. comp:: <title>
       :id: comp__baselibs_<slug>
       :safety: ASIL_B
       :security: NO
       :status: valid
       ...

    .. document:: <title>
       :id: doc__<slug>_<suffix>
       :realizes: wp__<key>[version==<N>]
       ...

Documents are matched to a work product entirely on the sphinx-needs
side, at render time. This scan only needs to enumerate components and
their titles.

A shallow regex scan of the source tree at ``env-before-read-docs``
gives us everything the directive needs, and works in every process of
a parallel build.
"""
from __future__ import annotations

import os
import re
from typing import Any


_DIRECTIVE_HEADER_RE = re.compile(
    r"^\.\.[ \t]+(?P<name>[a-z_-]+)::[ \t]*(?P<title>.*?)\s*$"
)
_OPTION_LINE_RE = re.compile(r"^[ \t]+:(?P<key>[^:]+):[ \t]*(?P<value>.*?)\s*$")

# Options captured from ``:key: value`` lines. Everything else
# (safety, security, status, realizes, tags, ...) is intentionally
# dropped: the report delegates all attribute and link resolution to
# sphinx-needs at render time (``.. needtable::`` / ``.. needlist::``).
# ``includes`` is captured only for ``.. mod::`` needs (whitelist of
# components; see :func:`module_includes`); ``version`` is captured
# on ``.. comp::`` needs to honour ``[version==N]`` filters coming from
# that whitelist.
_SCANNED_OPTIONS = frozenset({"id", "includes", "version"})

_INCLUDE_ENTRY_RE = re.compile(
    r"^(?P<id>[^\[\s]+)(?:\[version==(?P<version>[^\]]+)\])?\s*$"
)


def scan_rst_needs(srcdir: str, directives: set[str]) -> list[dict]:
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


def module_includes(
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


def discover_components(
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


def scan_source_tree(app, env, docnames):
    """Cache a filesystem scan of all ``.. mod::`` and ``.. comp::``
    needs on ``env`` so the directive can enumerate its components in
    every process of a parallel build.
    """
    env.module_verification_report_needs = scan_rst_needs(
        env.srcdir, directives={"mod", "comp"}
    )
