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

"""
Validate an inspection record against the build output it was reviewed against.

A ``mod_insp`` sphinx-needs element pins the state of one or more build
outputs (e.g. the extracted component requirements) via a ``sha256`` attribute.
This script:

1. Reads ``needs.json`` and looks up the inspection record by its id.
2. Computes the SHA256 over the validated build output.
3. Compares the computed hash with the ``sha256`` attribute of the record.

There are two hashing modes:

* **Flat** (no ``--link-field`` given): the SHA256 is computed over the
  concatenated input files (sorted by path, so the result is independent of the
  order in which Bazel passes them). This pins exactly the elements contained in
  the input files.
* **Transitive** (one or more ``--link-field`` given): the input files only
  define the *root* elements (e.g. the extracted feature requirements). Starting
  from those roots, the given link fields (e.g. ``derived_from``, ``satisfies``)
  are followed recursively through the full ``needs.json``, collecting every
  reachable element (e.g. the stakeholder requirements a feature requirement is
  derived from, and their parents in turn). The SHA256 is computed over the
  canonical serialization of the whole closure. As a result the checklist also
  goes out of date when an *upstream* dependency (such as a linked stakeholder
  requirement) changes, not just when a root element changes.

  Reachable elements whose full content does not live in ``--needs-json`` (e.g.
  requirements or architecture imported from another repository) must be
  supplied via ``--extra-needs-json``; otherwise they are hashed as ``<MISSING>``
  and changes to them are not detected.

On match it writes the verified hash to ``--output`` and exits ``0``. On mismatch
(or when the need / attribute is missing) it logs the expected and actual hashes
and exits ``1``, which fails the Bazel build.
"""

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def find_need(data: dict[str, Any], need_id: str) -> dict[str, Any] | None:
    """Return the need with id ``need_id`` from a needs.json structure."""
    for version in data.get("versions", {}).values():
        needs = version.get("needs", {})
        if need_id in needs:
            return needs[need_id]
    return None


def collect_needs(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return a flat ``{id: need}`` mapping of every need in a needs.json structure."""
    all_needs: dict[str, dict[str, Any]] = {}
    for version in data.get("versions", {}).values():
        for need_id, need in version.get("needs", {}).items():
            all_needs[need_id] = need
    return all_needs


def _link_targets(need: dict[str, Any], field: str) -> list[str]:
    """Return the link targets stored under ``field`` of ``need`` as a list.

    sphinx-needs may store link targets with a version constraint suffix such as
    ``stkh_req__foo[version==1]``. The constraint is stripped so the target
    matches the plain need id used as the key in ``needs.json``.
    """
    value = need.get(field)
    if value is None:
        return []
    raw = value if isinstance(value, list) else [value]
    return [_normalize_id(str(v)) for v in raw if str(v).strip()]  # pyright: ignore[reportUnknownArgumentType]


def _normalize_id(need_id: str) -> str:
    """Strip a trailing ``[...]`` version constraint and whitespace from ``need_id``."""
    return need_id.split("[", 1)[0].strip()


def compute_closure(
    all_needs: dict[str, dict[str, Any]],
    roots: set[str],
    link_fields: list[str],
) -> set[str]:
    """Return the transitive closure of ``roots`` following ``link_fields``.

    Starting from ``roots`` every link target reachable via one of the
    ``link_fields`` is collected recursively. Missing link targets (ids that are
    not present in ``all_needs``) are kept in the result so that a dangling link
    still influences the hash deterministically.
    """
    seen: set[str] = set()
    stack: list[str] = list(roots)
    while stack:
        need_id = stack.pop()
        if need_id in seen:
            continue
        seen.add(need_id)
        need = all_needs.get(need_id)
        if need is None:
            continue
        for field in link_fields:
            for target in _link_targets(need, field):
                if target not in seen:
                    stack.append(target)
    return seen


def compute_sha256(paths: list[Path]) -> str:
    """Return the SHA256 over the concatenated contents of ``paths`` (sorted)."""
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda p: p.name):
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _canonicalize_need(need: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``need`` with sphinx-needs back-link lists order-normalized.

    sphinx-needs auto-populates the reverse-link fields (every link field has a
    corresponding ``<field>_back``) in document-processing order, which is *not*
    stable with respect to unrelated changes: editing an unrelated ``.rst`` file
    can reorder the entries of a ``*_back`` list without changing its contents.
    Because the full need dict is hashed, that spurious reordering would
    invalidate the checklist even though nothing semantically relevant changed.

    Sorting the (string) entries of every ``*_back`` list makes the serialization
    order-independent so only genuine changes to the set of back-links affect the
    hash. Forward link fields are author-specified and deterministic, so they are
    left untouched.
    """
    normalized = dict(need)
    for key, value in normalized.items():
        if key.endswith("_back") and isinstance(value, list):
            normalized[key] = sorted(  # pyright: ignore[reportUnknownArgumentType]
                value,
                key=lambda item: str(item),  # pyright: ignore[reportUnknownLambdaType]
            )
    return normalized


def compute_closure_sha256(
    all_needs: dict[str, dict[str, Any]],
    ids: set[str],
) -> str:
    """Return the SHA256 over the canonical serialization of ``ids`` in ``all_needs``.

    Needs are serialized sorted by id, each as a deterministic JSON object
    (``sort_keys=True``). The full need dict is hashed, so any change to a
    reachable element - including its content, attributes or links - changes the
    result. The auto-generated ``*_back`` link lists are order-normalized first
    (see ``_canonicalize_need``) so that unrelated edits which only reshuffle
    those reverse links do not invalidate the hash. Ids without a matching need
    are still mixed into the digest so that a dangling link is detected too.
    """
    digest = hashlib.sha256()
    for need_id in sorted(ids):
        digest.update(need_id.encode("utf-8"))
        digest.update(b"\x00")
        need = all_needs.get(need_id)
        if need is None:
            digest.update(b"<MISSING>")
        else:
            payload = json.dumps(
                _canonicalize_need(need), sort_keys=True, ensure_ascii=False
            )
            digest.update(payload.encode("utf-8"))
        digest.update(b"\x00")
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate an inspection record (mod_insp) against the SHA256 of "
            "the build output it was reviewed against."
        )
    )
    _ = parser.add_argument(
        "--needs-json",
        required=True,
        type=Path,
        help="Path of the needs.json file containing the checklist need.",
    )
    _ = parser.add_argument(
        "--checklist-id",
        required=True,
        help="Id of the mod_insp need to validate (e.g. 'mod_insp__foo').",
    )
    _ = parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path of the stamp file to write with the verified hash on success.",
    )
    _ = parser.add_argument(
        "--link-field",
        dest="link_fields",
        action="append",
        default=[],
        metavar="FIELD",
        help=(
            "Link field to follow recursively from the input (root) elements when "
            "computing the hash (e.g. 'derived_from'). May be given multiple "
            "times. If omitted, only the input files themselves are hashed "
            "(no transitive dependencies)."
        ),
    )
    _ = parser.add_argument(
        "--extra-needs-json",
        dest="extra_needs_json",
        action="append",
        default=[],
        type=Path,
        metavar="PATH",
        help=(
            "Additional needs.json file providing the full content of needs that "
            "are referenced from the validated elements but are not contained in "
            "the main --needs-json (e.g. requirements/architecture imported from "
            "an upstream repository). Used in transitive mode to resolve and hash "
            "such external needs; without it they are hashed as <MISSING> and "
            "changes to them go undetected. May be given multiple times."
        ),
    )
    _ = parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Build output files whose combined SHA256 is validated.",
    )

    args = parser.parse_args()

    with open(args.needs_json) as f:
        data = json.load(f)

    need = find_need(data, args.checklist_id)
    if need is None:
        logger.error(
            "Checklist need '%s' not found in '%s'.",
            args.checklist_id,
            args.needs_json,
        )
        return 1

    expected = need.get("sha256")

    if args.link_fields:
        # Transitive mode: the input files define the root elements; follow the
        # given link fields recursively through the full needs.json and hash the
        # whole closure (roots + all reachable dependencies).
        root_needs: dict[str, dict[str, Any]] = {}
        for path in args.inputs:
            with open(path) as f:
                root_needs.update(collect_needs(json.load(f)))
        roots = set(root_needs.keys())

        # Build the authoritative content/link graph. Extra needs.json sources
        # (e.g. an upstream repository) only fill in needs that are missing
        # locally, so the main --needs-json keeps precedence for local content,
        # and the extracted root elements keep precedence over both. Without the
        # extra sources, external needs referenced by the validated elements are
        # absent from the graph and get hashed as <MISSING>, so changes to them
        # are invisible to the checklist.
        all_needs: dict[str, dict[str, Any]] = {}
        for extra_path in args.extra_needs_json:
            with open(extra_path) as f:
                all_needs.update(collect_needs(json.load(f)))
        all_needs.update(collect_needs(data))
        all_needs.update(root_needs)

        closure = compute_closure(all_needs, roots, args.link_fields)
        dependencies = closure - roots
        logger.info(
            "Checklist '%s': hashing %d element(s) (%d root(s) + %d "
            "transitive dependency/ies via %s).",
            args.checklist_id,
            len(closure),
            len(roots),
            len(dependencies),
            ", ".join(args.link_fields),
        )
        if dependencies:
            logger.info(
                "  transitive dependencies: %s",
                ", ".join(sorted(dependencies)),
            )
        actual = compute_closure_sha256(all_needs, closure)
    else:
        actual = compute_sha256(args.inputs)

    if not expected:
        logger.error(
            "Checklist '%s' has an EMPTY 'sha256' attribute.\n"
            "Review the target output and, if correct, pin it by setting the "
            "checklist's 'sha256' attribute to:\n"
            "\n"
            "  %s\n",
            args.checklist_id,
            actual,
        )
        return 1

    if expected != actual:
        logger.error(
            "Checklist '%s' is OUT OF DATE.\n"
            "  expected (sha256 in need): %s\n"
            "  actual   (build output):  %s\n"
            "The validated target output has changed since the checklist was "
            "last reviewed. Re-review the checklist and update its 'sha256' "
            "attribute to '%s'.",
            args.checklist_id,
            expected,
            actual,
            actual,
        )
        return 1

    logger.info("Checklist '%s' is up to date (sha256=%s).", args.checklist_id, actual)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    _ = args.output.write_text(actual + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
