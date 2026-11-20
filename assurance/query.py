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

# Portions generated with OpenAI Codex; see the retained verification records.
"""Navigate evolution summaries before reading task traces."""

import argparse
import json
from pathlib import Path
from typing import Any


def query(store: Path, failed: bool = False) -> list[dict[str, Any]]:
    store = store.resolve()
    summary = store / "evolution_summary.jsonl"
    rows = [
        json.loads(line) for line in summary.read_text().splitlines() if line.strip()
    ]
    if not failed:
        return sorted(rows, key=lambda row: (-row["matches_expectation"], row["run"]))
    failures: list[dict[str, Any]] = []
    for row in rows:
        run = (store / row["run"]).resolve()
        if not run.is_relative_to(store.resolve()):
            raise ValueError("Run index path escapes trace store")
        for path in sorted((run / "traces").glob("*/score.json")):
            task = json.loads(path.read_text())
            if not task["matches_expectation"] or task["gate_verdict"] == "fail":
                failures.append(
                    {
                        "run": row["run"],
                        "task": task["task_id"],
                        "gate_verdict": task["gate_verdict"],
                        "matches_expectation": task["matches_expectation"],
                        "trace": path.relative_to(store.resolve()).as_posix(),
                    }
                )
    return failures


def compare(store: Path, left: str, right: str) -> dict[str, Any]:
    rows = {row["run"]: row for row in query(store)}
    first, second = rows[left], rows[right]

    def task_scores(run: str) -> dict[str, Any]:
        path = (store.resolve() / run).resolve()
        if not path.is_relative_to(store.resolve()):
            raise ValueError("Run index path escapes trace store")
        return {
            value["task_id"]: value
            for trace in sorted((path / "traces").glob("*/score.json"))
            if (value := json.loads(trace.read_text()))
        }

    old, new = task_scores(left), task_scores(right)
    changes = [
        identifier
        for identifier in sorted(old.keys() | new.keys())
        if old.get(identifier, {}).get("matches_expectation")
        != new.get(identifier, {}).get("matches_expectation")
        or old.get(identifier, {}).get("observed_impacted_ids")
        != new.get(identifier, {}).get("observed_impacted_ids")
    ]
    return {
        "left": left,
        "right": right,
        "match_delta": second["matches_expectation"] - first["matches_expectation"],
        "gate_pass_delta": second["gate_passes"] - first["gate_passes"],
        "changed_tasks": changes,
        "same_split": first["split"] == second["split"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--failed", action="store_true")
    parser.add_argument("--compare", nargs=2, metavar=("LEFT", "RIGHT"))
    args = parser.parse_args()
    result = (
        compare(args.store, *args.compare)
        if args.compare
        else query(args.store, args.failed)
    )
    print(json.dumps(result, indent=2))
