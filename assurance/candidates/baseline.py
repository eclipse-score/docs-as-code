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
"""Task-scoped, deterministic context; documentation stays inert JSON string data."""

import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any


def read_file(path: Path) -> bytes:
    """Open each path component without following symbolic links."""
    path = path.absolute()
    descriptor = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in path.parts[1:-1]:
            child = os.open(
                component,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = child
        file_descriptor = os.open(
            path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor
        )
        try:
            if not stat.S_ISREG(os.fstat(file_descriptor).st_mode):
                raise ValueError("Context input must be a regular file")
            with os.fdopen(file_descriptor, "rb", closefd=False) as stream:
                data = stream.read(1024 * 1024 + 1)
            if len(data) > 1024 * 1024:
                raise ValueError(
                    "Context input exceeds the documented 1 MiB file limit"
                )
            return data
        finally:
            os.close(file_descriptor)
    finally:
        os.close(descriptor)


class AssuranceHarness:
    def get_context(self, task_spec: dict[str, Any]) -> str:
        root = Path(task_spec["input_path"]).absolute()
        files = task_spec.get("input_files")
        if files is None:
            if not root.is_file():
                raise ValueError(
                    "Directory inputs require an explicit input_files allowlist"
                )
            files = [root.name]
            root = root.parent
        documents = []
        for relative in sorted(set(files)):
            path = Path(relative)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("Input files must be relative to input_path")
            data = read_file(root / path)
            documents.append(
                {
                    "filename": path.as_posix(),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "content": data.decode("utf-8"),
                }
            )
        rules = []
        for rule in sorted(
            task_spec.get("consistency_rules", []), key=lambda item: item["id"]
        ):
            data = read_file(Path(rule["path"]))
            rules.append(
                {
                    "rule_id": rule["id"],
                    "filename": Path(rule["path"]).name,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "content": data.decode("utf-8"),
                }
            )
        return json.dumps(
            {
                "task_id": task_spec["task_id"],
                "documents": documents,
                "consistency_rules": rules,
            },
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
        )

    def post_process(
        self, agent_output: str, task_spec: dict[str, Any]
    ) -> dict[str, Any]:
        # Output is inert data. It grants no command, path or gate capability.
        return {"task_id": task_spec["task_id"], "agent_output": agent_output}
