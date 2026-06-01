import json
import os
from pathlib import Path
from typing import Any

from sphinx.application import Sphinx
from sphinx_needs import logging
from sphinx_needs.data import NeedsView, SphinxNeedsData
from sphinx_needs.need_item import NeedItem
from score_metrics.traceability_metrics import (
    compute_traceability_summary,
)

logger = logging.get_logger(__name__)


def _configure_traceability_dashboard(app: Sphinx, config: object) -> None:
    """Propagate repo-level traceability settings to dashboard filters."""
    from src.extensions.score_metrics.traceability_dashboard import (
        set_default_include_external,
    )

    include_external = bool(
        getattr(config, "score_metamodel_include_external_needs", False)
    )
    set_default_include_external(include_external)


def get_need_types_by_tags(needs_types: list[NeedItem], tags: set[str]) -> list[str]:
    found_need_types: list[str] = []
    for need_type in needs_types:
        found_tag_set = set(need_type["tags"])
        if tags.intersection(found_tag_set):
            found_need_types.append(need_type["type"])
    return found_need_types


def _discover_requirement_types(
    app: Sphinx, all_needs: list[NeedItem]
) -> set[NeedItem]:
    """Discover requirement directives that are both tagged and present."""
    tagged_requirements_types = get_need_types_by_tags(
        all_needs, {"requirement", "requirement_excl_process"}
    )
    all_tagged_requirements = (
        SphinxNeedsData(app.env)
        .get_needs_view()
        .filter_types(tagged_requirements_types)
        .values()
    )
    if not all_tagged_requirements:
        logger.warning(
            "No requirement types discovered in current build for tagged "
            "needs_types requirement directives."
        )

    return set(all_tagged_requirements)


def _write_metrics_json(app: Sphinx, exception: Exception | None) -> None:
    """Write a schema-v1 metrics.json alongside needs.json in the build output.

    This is the single source of truth for traceability metrics. It runs
    inside the Sphinx build so it has access to all needs (local + external)
    and produces the same metrics the dashboard pie charts display.
    The traceability_gate reads this file to enforce CI thresholds.
    """
    print("WE ARE IN WRITE METRICS JSON")
    if exception:
        logger.error("===================================")
        logger.error("===================================")
        logger.error("===================================")
        logger.error(f"EXCEPTION RAISED: {exception}")
        return

    include_external: bool = bool(
        getattr(app.config, "score_metamodel_include_external_needs", False)
    )
    all_needs: NeedsView = SphinxNeedsData(app.env).get_needs_view()

    raw = getattr(app.config, "score_metamodel_requirement_types", "").strip()
    requirement_types = [t.strip() for t in raw.split(",") if t.strip()]
    if requirement_types:
        requirement_types = all_needs.filter_types(requirement_types)

    metrics_by_type: dict[str, Any] = {}
    if not requirement_types:
        logger.info(
            "No requirement types configured or discovered; writing empty metrics.json."
        )
    else:
        for req_type in sorted(requirement_types):
            type_summary = compute_traceability_summary(
                all_needs=all_needs,
                filtered_test_types=set(),
                include_external=include_external,
            )
            metrics_by_type[req_type] = {
                "include_not_implemented": type_summary["include_not_implemented"],
                "include_external": type_summary["include_external"],
                "requirements": type_summary["requirements"],
                "tests": type_summary["tests"],
            }

    output: dict[str, Any] = {
        "schema_version": "1",
        "generated_by": "sphinx_build",
        "metrics_by_type": metrics_by_type,
    }
    print("===================================")
    print("===================================")
    print("===================================")
    print(f"writing metrics.json to {Path(app.outdir) / 'metrics.json'}")
    print("===================================")
    print("===================================")
    print("===================================")
    out_path = Path(app.outdir) / "metrics.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Traceability metrics written to: {out_path}")


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

    _ = app.connect("config-inited", _configure_traceability_dashboard, priority=498)
    _ = app.connect("build-finished", _write_metrics_json, priority=499)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
