# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

"""Emit a TOML fragment containing [[mounts]] entries and register it with
needs-config-writer so the same content lands in docs/ubproject.toml."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from sphinx.config import Config


def _escape(value: str) -> str:
    """Escape a string for safe inclusion in a TOML basic string."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def write_fragment(
    resolved_mounts: list[dict[str, Any]],
    outdir: Path | None = None,
) -> Path:
    """Write a TOML fragment containing one ``[[mounts]]`` table per resolved entry.

    Keys are emitted only when non-default so that the rendered TOML mirrors
    what a user would write by hand. Returns the absolute path of the file
    written.
    """
    if outdir is None:
        outdir = Path(tempfile.mkdtemp(prefix="score_mounts_"))
    outdir.mkdir(parents=True, exist_ok=True)
    fragment = outdir / "score_mounts_fragment.toml"

    lines: list[str] = []
    for m in resolved_mounts:
        lines.append("[[mounts]]")
        lines.append(f'dir = "{_escape(m["dir"])}"')
        lines.append(f'mount_at = "{_escape(m["mount_at"])}"')
        if m.get("attach_to"):
            lines.append(f'attach_to = "{_escape(m["attach_to"])}"')
        if m.get("entry_doc") and m["entry_doc"] != "index":
            lines.append(f'entry_doc = "{_escape(m["entry_doc"])}"')
        lines.append("")

    fragment.write_text("\n".join(lines), encoding="utf-8")
    return fragment


_BUNDLE_BANNED_NEEDS_KEYS = frozenset(
    {
        "schema_definitions_from_json",
        "schema_debug_path",
        "build_needumls",
    }
)


def sanitize_bundle_toml_text(host_toml_text: str) -> str:
    """Strip path-bound entries from a copy of host ubproject.toml content.

    The result is suitable for placement at any in-repo bundle's source
    root: it preserves the type system (types, links, layouts, fields,
    parse extensions, server settings) but removes references to paths
    that exist only relative to the host project's confdir.

    Operates on the original text to preserve key order / comments;
    drops entries via TOML-aware parsing and re-emit only for the
    affected tables.
    """
    import tomllib
    try:
        import tomli_w
    except ImportError as exc:
        raise RuntimeError(
            "score_mounts: tomli-w is required to emit bundle ubproject.toml; "
            "add 'tomli-w' to src/requirements.in and regenerate."
        ) from exc

    data = tomllib.loads(host_toml_text)
    # Strip top-level path-bound entries.
    data.pop("mounts", None)
    needs = data.get("needs")
    if isinstance(needs, dict):
        needs.pop("external_needs", None)
        for key in _BUNDLE_BANNED_NEEDS_KEYS:
            needs.pop(key, None)
    return tomli_w.dumps(data)


def write_bundle_tomls(
    host_toml_path: Path,
    bundle_src_roots: list[Path],
) -> list[Path]:
    """Write a sanitized ubproject.toml at each bundle src_root.

    Returns the list of written file paths. Bundles whose src_root does
    not exist (e.g. a typo in mount()) are skipped with a logger.warning.
    Raises FileNotFoundError if host_toml_path does not exist — caller
    should handle by warn-and-skip during early builds.
    """
    text = host_toml_path.read_text(encoding="utf-8")
    sanitized = sanitize_bundle_toml_text(text)

    from sphinx.util import logging as sphinx_logging
    logger = sphinx_logging.getLogger(__name__)

    written: list[Path] = []
    for src_root in bundle_src_roots:
        if not src_root.is_dir():
            logger.warning(
                "score_mounts: bundle src_root does not exist, skipping: %s",
                src_root,
            )
            continue
        target = src_root / "ubproject.toml"
        target.write_text(sanitized, encoding="utf-8")
        written.append(target)
    return written


def hook_into_needs_config_writer(config: Config, fragment_path: Path) -> None:
    """Register the fragment with needs-config-writer so it lands in ubproject.toml."""
    merge_files = getattr(config, "needscfg_merge_toml_files", None)
    if isinstance(merge_files, list):
        merge_files.append(str(fragment_path))
