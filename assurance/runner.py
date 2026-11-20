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
"""Evaluate authorized public change scenarios using the unchanged native gate."""

import argparse
import ast
import datetime
import difflib
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Protocol

from jsonschema_rs import Draft202012Validator

from assurance.blocks import check_blocks
from assurance.candidates.baseline import AssuranceHarness as TrustedReader
from assurance.coverage import validate
from assurance.impact import classify

ROOT = Path(
    os.environ.get(
        "BUILD_WORKSPACE_DIRECTORY", str(Path(__file__).resolve().parents[1])
    )
)
GATE = ROOT / "scripts_bazel/traceability_gate.py"
CATALOG = (ROOT / "assurance/rules.json").resolve()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Candidate(Protocol):
    def get_context(self, task_spec: dict[str, Any]) -> str: ...
    def post_process(
        self, agent_output: str, task_spec: dict[str, Any]
    ) -> dict[str, Any]: ...


def load_candidate(path: Path) -> Candidate:
    """Reject obvious contract violations before importing an authorized candidate.

    Candidates are reviewed program code, never code extracted from documents.
    This static screen is lightweight validation, not an arbitrary-code sandbox.
    """
    tree = ast.parse(path.read_text())
    allowed = {"hashlib", "json", "os", "pathlib", "stat", "collections", "typing"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import | ast.ImportFrom):
            modules = (
                [item.name for item in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
            )
            if any(module.split(".")[0] not in allowed for module in modules):
                raise ValueError(
                    "Candidate imports outside the supported read-only stdlib boundary"
                )
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in ("eval", "exec", "compile", "__import__")
        ):
            raise ValueError("Candidate uses dynamic execution")
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr
            in (
                "system",
                "popen",
                "spawn",
                "write_text",
                "write_bytes",
                "unlink",
                "mkdir",
                "remove",
                "rename",
                "execv",
                "execve",
            )
        ):
            raise ValueError("Candidate requests a write or execution capability")
    spec = importlib.util.spec_from_file_location("assurance_candidate", path)
    if spec is None or spec.loader is None:
        raise ValueError("Candidate cannot be imported")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    harness = module.AssuranceHarness()
    if not callable(harness.get_context) or not callable(harness.post_process):
        raise ValueError("Candidate does not implement AssuranceHarness")
    return harness


def task_paths(task: dict[str, Any], corpus: Path) -> dict[str, Any]:
    task = dict(task)
    if not re.fullmatch(r"[A-Za-z0-9_-]+", task["task_id"]):
        raise ValueError("Unsafe task ID")
    relative = Path(task["input_path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Corpus task input_path escapes the public corpus")
    folder = corpus / relative
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("Corpus task input_path must be a real directory")
    for field in ("before", "after", "metrics"):
        name = task[field]
        if (
            name not in task["input_files"]
            or Path(name).is_absolute()
            or ".." in Path(name).parts
        ):
            raise ValueError("Task check inputs must be listed in input_files")
    task["input_path"] = str(folder.absolute())
    task["consistency_rules"] = [
        {"id": rule, "path": str(CATALOG)} for rule in task["rule_ids"]
    ]
    return task


TRACE_FILENAMES = (
    "gate_output.json",
    "impacted_elements.json",
    "score.json",
    "agent_diff.patch",
)


def validate_candidate(candidate: Path, corpus: Path, split: str) -> dict[str, Any]:
    harness = load_candidate(candidate)
    tasks = json.loads((corpus / "index.json").read_text())["tasks"]
    selected = [task_paths(task, corpus) for task in tasks if task["split"] == split]
    if not selected:
        raise ValueError("Selected corpus split is empty")
    task = selected[0]
    context = harness.get_context(task)
    if not isinstance(context, str) or context != harness.get_context(task):
        raise ValueError("Candidate context must be a deterministic string")
    processed = harness.post_process("", task)
    if not isinstance(processed, dict):
        raise ValueError("Candidate post_process must return a dictionary")
    json.dumps(processed)
    return {
        "candidate_sha256": sha(candidate),
        "task_id": task["task_id"],
        "trace_filenames": list(TRACE_FILENAMES),
        "validated": True,
    }


def check_gate_exit(
    process: subprocess.CompletedProcess[bytes], identifier: str
) -> None:
    if process.returncode not in (0, 2):
        raise RuntimeError(
            f"Native gate execution error for {identifier}; raw output retained"
        )


def evaluate_task(
    harness: Candidate,
    task: dict[str, Any],
    target: Path,
    raw: Path,
    provenance: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, Any]:
    identifier = task["task_id"]
    provenance = {
        **provenance,
        "execution_timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
    }
    target.mkdir()
    context = harness.get_context(task)
    if context != harness.get_context(task):
        raise ValueError(f"Nondeterministic context for {identifier}")
    # Use the same secure reader as context retrieval; no extra corpus reads.
    documents = json.loads(TrustedReader().get_context(task))["documents"]
    by_name = {entry["filename"]: entry for entry in documents}
    before = json.loads(by_name[task["before"]]["content"])
    after = json.loads(by_name[task["after"]]["content"])
    metrics = json.loads(by_name[task["metrics"]]["content"])
    validate(metrics)
    supplied = target / "supplied-metrics.json"
    supplied.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n")
    normalized = target / "metrics.json"
    coverage_command = [
        sys.executable,
        "-m",
        "scripts_bazel.traceability_coverage",
        "--metrics-json",
        str(supplied),
        "--json-output",
        str(normalized),
    ]
    if task.get("metrics_mode") == "snapshot":
        snapshot_path = target / "needs-after.json"
        snapshot_path.write_text(json.dumps(after, sort_keys=True) + "\n")
        coverage_command = [
            sys.executable,
            "-m",
            "scripts_bazel.traceability_coverage",
            "--needs-json",
            str(snapshot_path),
            "--json-output",
            str(normalized),
        ]
        for kind in task.get("coverage_types", []):
            coverage_command += ["--need-type", kind]
    coverage_process = subprocess.run(
        coverage_command,
        cwd=ROOT,
        capture_output=True,
        timeout=60,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [str(ROOT), *sys.path, os.environ.get("PYTHONPATH", "")]
            ),
        },
    )
    (raw / f"{identifier}.coverage.stdout").write_bytes(coverage_process.stdout)
    (raw / f"{identifier}.coverage.stderr").write_bytes(coverage_process.stderr)
    if coverage_process.returncode:
        raise RuntimeError(
            f"Native coverage execution error for {identifier}; raw output retained: {coverage_process.stderr.decode(errors='replace')}"
        )
    command: list[str] = [
        sys.executable,
        "-m",
        "scripts_bazel.traceability_gate",
        "--metrics-json",
        str(normalized),
        *task["gate_args"],
    ]
    allowed_args = {
        "--need-type",
        "--min-req-code",
        "--min-req-test",
        "--min-req-fully-linked",
        "--min-tests-linked",
        "--require-all-links",
        "--fail-on-broken-test-refs",
    }
    if any(
        value.startswith("--") and value not in allowed_args
        for value in task["gate_args"]
    ):
        raise ValueError("Task requests a non-contract gate option")
    process = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        timeout=60,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [str(ROOT), *sys.path, os.environ.get("PYTHONPATH", "")]
            ),
        },
    )
    (raw / f"{identifier}.stdout").write_bytes(process.stdout)
    (raw / f"{identifier}.stderr").write_bytes(process.stderr)
    check_gate_exit(process, identifier)
    metrics = json.loads(normalized.read_text())
    impacts = classify(before, after)
    block_results = check_blocks(after, metrics, task.get("blocks", []))
    (target / "block_results.json").write_text(
        json.dumps(block_results, indent=2) + "\n"
    )
    verdict = "pass" if process.returncode == 0 else "fail"
    # CR-005 is the native gate's threshold/broken-reference disposition.
    if verdict == "fail" and "CR-005" in task["rule_ids"]:
        impacts.append(
            {
                "need_id": "coverage",
                "impact_class": "direct_recheck",
                "rule_id": "CR-005",
                "changed_artifact": task["metrics"],
            }
        )
    observed = sorted({item["need_id"] for item in impacts})
    before_metrics = json.loads(by_name["metrics-before.json"]["content"])
    validate(before_metrics)
    coverage_delta = {
        kind: {
            field: metrics["metrics_by_type"].get(kind, {}).get(field, 0)
            - values[field]
            for field in (
                "with_code_link_pct",
                "with_test_link_pct",
                "fully_linked_pct",
            )
        }
        for kind, values in before_metrics["metrics_by_type"].items()
    }
    row: dict[str, Any] = {
        "task_id": identifier,
        "coverage_delta": coverage_delta,
        "metrics_source": task.get("metrics_mode", "native_gate_fixture"),
        "gate_verdict": verdict,
        "expected_gate_verdict": task["expected_gate_verdict"],
        "expected_impacted_ids": sorted(task["expected_impacted_ids"]),
        "observed_impacted_ids": observed,
        "matches_expectation": verdict == task["expected_gate_verdict"]
        and observed == sorted(task["expected_impacted_ids"]),
        "provenance": provenance,
        "input_hashes": {entry["filename"]: entry["sha256"] for entry in documents},
        "context_sha256": hashlib.sha256(context.encode()).hexdigest(),
    }
    Draft202012Validator(schema, validate_formats=True).validate(row)
    Draft202012Validator(schema["$defs"]["impacted_elements"]).validate(impacts)
    (target / "score.json").write_text(json.dumps(row, indent=2, sort_keys=True) + "\n")
    gate_output: dict[str, Any] = {
        "status": verdict,
        "exit_code": process.returncode,
        "command": command,
        "stdout_sha256": hashlib.sha256(process.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(process.stderr).hexdigest(),
    }
    Draft202012Validator(schema["$defs"]["gate_output"]).validate(gate_output)
    (target / "gate_output.json").write_text(json.dumps(gate_output, indent=2) + "\n")
    (target / "impacted_elements.json").write_text(json.dumps(impacts, indent=2) + "\n")
    difference = difflib.unified_diff(
        json.dumps(before, indent=2, sort_keys=True).splitlines(True),
        json.dumps(after, indent=2, sort_keys=True).splitlines(True),
        fromfile="before.json",
        tofile="after.json",
    )
    patch_text = "".join(difference)
    (target / "agent_diff.patch").write_text(patch_text)
    json.dumps(harness.post_process(patch_text, task))
    return row


def evaluate(
    candidate: Path, corpus: Path, output: Path, split: str = "search"
) -> dict[str, Any]:
    output = output.resolve()
    validate_candidate(candidate, corpus, split)
    harness = load_candidate(candidate)
    catalog = json.loads(CATALOG.read_text())
    tasks = json.loads((corpus / "index.json").read_text())["tasks"]
    selected = [task_paths(task, corpus) for task in tasks if task["split"] == split]
    if not selected:
        raise ValueError("Selected corpus split is empty")
    if len({task["task_id"] for task in tasks}) != len(tasks):
        raise ValueError("Duplicate task IDs")
    known = {rule["id"] for rule in catalog["rules"]}
    if any(set(task["rule_ids"]) - known for task in selected):
        raise ValueError("Task references an unknown rule")
    # Smoke validation precedes output creation and the full task set.
    context = harness.get_context(selected[0])
    if not isinstance(context, str) or context != harness.get_context(selected[0]):
        raise ValueError("Candidate context must be a deterministic string")
    json.dumps(harness.post_process("", selected[0]))
    output.mkdir(parents=True, exist_ok=False)
    traces, raw = output / "traces", output / "raw"
    traces.mkdir()
    raw.mkdir()
    provenance = {
        "execution_timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "python_version": platform.python_version(),
        "environment_hash": hashlib.sha256(
            json.dumps(
                {
                    "python": sys.version,
                    "platform": platform.platform(),
                    "packages": sorted(
                        (distribution.metadata["Name"], distribution.version)
                        for distribution in importlib.metadata.distributions()
                    ),
                },
                sort_keys=True,
            ).encode()
        ).hexdigest(),
        "gate_script_version": sha(GATE),
        "candidate_sha256": sha(candidate),
        "rule_catalog_sha256": sha(CATALOG),
        "corpus_index_sha256": sha(corpus / "index.json"),
        "coverage_script_sha256": sha(ROOT / "scripts_bazel/traceability_coverage.py"),
        "responsible_role": "pr_creator",
        "escalation_role": "harness_maintainer",
        "waiver_authority": "release_approver",
    }
    rows: list[dict[str, Any]] = []
    schema = json.loads((ROOT / "assurance/trace-schema.json").read_text())
    for task in selected:
        rows.append(
            evaluate_task(
                harness, task, traces / task["task_id"], raw, provenance, schema
            )
        )
    summary: dict[str, Any] = {
        "candidate_sha256": sha(candidate),
        "split": split,
        "tasks": len(rows),
        "matches_expectation": sum(row["matches_expectation"] for row in rows),
        "gate_passes": sum(row["gate_verdict"] == "pass" for row in rows),
        "provenance": provenance,
    }
    (output / "score.json").write_text(json.dumps(summary, indent=2) + "\n")
    (output / "meta.json").write_text(
        json.dumps(
            {
                "candidate": candidate.name,
                "split": split,
                "hypothesis": "Deterministic task-scoped retrieval preserves native gate outcomes and identifies argument impacts",
                "task_ids": [row["task_id"] for row in rows],
                "provenance": provenance,
            },
            indent=2,
        )
        + "\n"
    )
    with (output.parent.parent / "evolution_summary.jsonl").open("a") as stream:
        stream.write(
            json.dumps(
                {"run": output.relative_to(output.parent.parent).as_posix(), **summary},
                sort_keys=True,
            )
            + "\n"
        )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate", type=Path, default=ROOT / "assurance/candidates/baseline.py"
    )
    parser.add_argument("--corpus", type=Path, default=ROOT / "assurance/corpus")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--split", choices=["search", "heldout"], default="search")
    args = parser.parse_args()
    if args.validate_only:
        print(
            json.dumps(
                validate_candidate(args.candidate, args.corpus, args.split), indent=2
            )
        )
        return 0
    if args.output is None:
        parser.error("--output is required for evaluation")
    summary = evaluate(args.candidate, args.corpus, args.output, args.split)
    print(json.dumps(summary, indent=2))
    return 0 if summary["tasks"] == summary["matches_expectation"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
