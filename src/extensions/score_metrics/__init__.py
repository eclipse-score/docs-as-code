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
import json
from pathlib import Path
from typing import Any

from score_metrics.traceability_metrics import (
    CALCULATED_METRICS,
    calculate_full_need_metrics,
)
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx_needs import logging

logger = logging.get_logger(__name__)


def calculate_need_metrics(app: Sphinx, env: BuildEnvironment) -> None:
    """
    This is the single source of truth for traceability metrics. It runs
    inside the Sphinx build so it has access to all needs (local + external)
    and produces the same metrics the dashboard pie charts display.
    The traceability_gate reads this file to enforce CI thresholds.
    """
    include_external: bool = bool(
        getattr(app.config, "score_metamodel_include_external_needs", False)
    )
    calculate_full_need_metrics(app=app, include_external=include_external)


def _write_metrics_json(app: Sphinx, exception: Any | None) -> None:
    """
    Write a schema-v2 metrics.json alongside needs.json in the build output.
    """
    if exception:
        logger.error(f"Sphinx-Exception at end of build: {exception}")
    out_path = Path(app.outdir) / "metrics.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(CALCULATED_METRICS, indent=2), encoding="utf-8")
    print(f"Traceability metrics written to: {out_path}")


def setup(app: Sphinx) -> dict[str, str | bool]:
    app.add_config_value(
        "score_metrics_requirement_types",
        "",
        rebuild="env",
        description=(
            "Comma-separated list of need types treated as requirements for "
            "traceability metrics. If empty, requirement types are autodiscovered "
            "from needs_types tags (requirement)."
        ),
    )

    app.add_config_value(
        "score_metrics_include_external_needs",
        False,
        rebuild="env",
        description=(
            "When True, include external requirements in dashboard and CI metrics. "
            "Default is False so each repo gates only its own needs."
        ),
    )
    app.setup_extension("score_metamodel")

    # Calculates the metrics & sets global var for access
    _ = app.connect("env-updated", calculate_need_metrics, priority=600)

    # Writes the metrics to a json in '_build'
    _ = app.connect("build-finished", _write_metrics_json, priority=550)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
