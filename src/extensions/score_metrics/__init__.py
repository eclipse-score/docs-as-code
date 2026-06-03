import json
import os
from pathlib import Path
from typing import Any

from sphinx.application import Sphinx
from sphinx_needs import logging
from score_metrics.traceability_metrics import calculate_full_need_metrics
from sphinx.environment import BuildEnvironment

logger = logging.get_logger(__name__)


# def _configure_traceability_dashboard(app: Sphinx, config: object) -> None:
#     """Propagate repo-level traceability settings to dashboard filters."""
#     from src.extensions.score_metrics.traceability_dashboard import (
#         set_default_include_external,
#     )
#
#     include_external = bool(
#         getattr(config, "score_metamodel_include_external_needs", False)
#     )
#     set_default_include_external(include_external)


def _write_metrics_json(app: Sphinx, env: BuildEnvironment) -> None:
    """Write a schema-v1 metrics.json alongside needs.json in the build output.

    This is the single source of truth for traceability metrics. It runs
    inside the Sphinx build so it has access to all needs (local + external)
    and produces the same metrics the dashboard pie charts display.
    The traceability_gate reads this file to enforce CI thresholds.
    """
    include_external: bool = bool(
        getattr(app.config, "score_metamodel_include_external_needs", False)
    )
    calculate_full_need_metrics(app=app, include_external=include_external)
    # all_needs: NeedsView = SphinxNeedsData(app.env).get_needs_view()
    #
    # raw_metamodel_path = app.config.score_metamodel_yaml
    # override_path = Path(raw_metamodel_path) if raw_metamodel_path else None
    # metamodel = load_metamodel_data(override_path)
    #
    # raw = getattr(app.config, "score_metamodel_requirement_types", "").strip()
    # filter_reqs = [t.strip() for t in raw.split(",") if t.strip()]
    # if not filter_reqs:
    #     filter_reqs = get_need_types_by_tags(
    #         metamodel.needs_types, {"reqiurement", "requirement_excl_process"}
    #     )
    # metrics_by_type: dict[str, Any] = {}
    # test_stats
    #
    # test_needs = list(all_needs.filter_types(["testcase"]).values())
    # test_metrics = calculate_test_metrics(test_needs, current_reqtype_needs)
    # for req_type in sorted(filter_reqs):
    #     needs_of_req_type = all_needs.filter_types([req_type]).filter_is_external(False)
    #     if not list(needs_of_req_type.values()):
    #         continue
    #     type_summary = compute_traceability_summary(
    #         all_needs=all_needs,
    #         current_reqtype=req_type,
    #         current_reqtype_needs=needs_of_req_type,
    #         include_external=include_external,
    #     )
    #     metrics_by_type[req_type] = {
    #         "include_external": type_summary["include_external"],
    #         "requirements": type_summary["requirements"],
    #         "tests": type_summary["tests"],
    #     }
    #
    # output: dict[str, Any] = {
    #     "schema_version": "1",
    #     "generated_by": "sphinx_build",
    #     "metrics_by_type": metrics_by_type,
    # }
    # out_path = Path(app.outdir) / "metrics.json"
    # out_path.parent.mkdir(parents=True, exist_ok=True)
    # out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    # print(f"Traceability metrics written to: {out_path}")


def setup(app: Sphinx) -> dict[str, str | bool]:
    app.add_config_value(
        "score_metamodel_requirement_types",
        "",
        rebuild="env",
        description=(
            "Comma-separated list of need types treated as requirements for "
            "traceability metrics. If empty, requirement types are autodiscovered "
            "from needs_types tags (requirement, requirement_excl_process)."
        ),
    )

    app.add_config_value(
        "score_metamodel_include_external_needs",
        False,
        rebuild="env",
        description=(
            "When True, include external requirements in dashboard and CI metrics. "
            "Default is False so each repo gates only its own needs."
        ),
    )

    # _ = app.connect("config-inited", _configure_traceability_dashboard, priority=498)
    _ = app.connect("env-updated", _write_metrics_json, priority=550)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
