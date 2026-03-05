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
"""Sphinx extension that creates symlinks from arbitrary locations into the
documentation source directory, allowing sphinx-build to include source
files that live outside ``docs/``.

Configuration in ``conf.py``::

    score_any_folder_mapping = {
        "../src/my_module/docs": "my_module",
    }

Each entry is a ``source: target`` pair where:

* ``source`` – path to the directory to expose, relative to ``confdir``
  (the directory containing ``conf.py``).
* ``target`` – path of the symlink to create, relative to ``confdir``.

The extension creates the symlinks on ``builder-inited``,
before Sphinx starts reading any documents.
Existing correct symlinks are left in place(idempotent);
a symlink pointing to the wrong target is replaced.

Symlinks created by this extension are removed again on ``build-finished``.
Misconfigured pairs (absolute paths, non-symlink path at the target location)
are logged as errors and skipped.
"""

from pathlib import Path

from sphinx.application import Sphinx
from sphinx.util.logging import getLogger

logger = getLogger(__name__)

_APP_ATTRIBUTE = "_score_any_folder_created_links"

def setup(app: Sphinx) -> dict[str, str | bool]:
    app.add_config_value("score_any_folder_mapping", default={}, rebuild="env")
    app.connect("builder-inited", _create_symlinks)
    app.connect("build-finished", _cleanup_symlinks)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def _symlink_pairs(app: Sphinx) -> list[tuple[Path, Path]]:
    """Return ``(resolved_source, link_path)`` pairs from the mapping."""
    confdir = Path(app.confdir)
    pairs = []
    for source_rel, target_rel in app.config.score_any_folder_mapping.items():
        if Path(source_rel).is_absolute():
            logger.error(
                "score_any_folder: source path must be relative, got: %r; skipping",
                source_rel,
            )
            continue
        if Path(target_rel).is_absolute():
            logger.error(
                "score_any_folder: target path must be relative, got: %r; skipping",
                target_rel,
            )
            continue
        source = (confdir / source_rel).resolve()
        link = confdir / target_rel
        pairs.append((source, link))
    return pairs


def _create_symlinks(app: Sphinx) -> None:
    created_links: set[Path] = set()

    for source, link in _symlink_pairs(app):
        if link.is_symlink():
            if link.resolve() == source:
                logger.debug("score_any_folder: symlink already correct: %s", link)
                continue
            logger.info(
                "score_any_folder: replacing stale symlink %s -> %s", link, source
            )
            link.unlink()
        elif link.exists():
            logger.error(
                "score_any_folder: target path already exists and is not a symlink: "
                "%s; skipping",
                link,
            )
            continue

        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(source)
        created_links.add(link)
        logger.debug("score_any_folder: created symlink %s -> %s", link, source)

    setattr(app, _APP_ATTRIBUTE, created_links)


def _cleanup_symlinks(app: Sphinx, exception: Exception | None) -> None:
    del exception

    created_links: set[Path] = getattr(app, _APP_ATTRIBUTE, set())
    for link in created_links:
        if not link.is_symlink():
            continue
        link.unlink()
        logger.debug("score_any_folder: removed temporary symlink %s", link)
