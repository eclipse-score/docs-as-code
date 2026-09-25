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
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

from generate_agent_context import (
    build_projection,
    load_metamodel_yaml,
    render_projection,
    resolve_metamodel_path,
)


def _runfiles_data_path(relative: Path) -> Path:
    for variable in ("TEST_SRCDIR", "RUNFILES_DIR"):
        runfiles_dir = os.environ.get(variable)
        if runfiles_dir:
            candidate = Path(runfiles_dir) / "_main" / relative
            if candidate.exists():
                return candidate
    for ancestor in Path(__file__).absolute().parents:
        if (ancestor / "MODULE.bazel").is_file():
            return ancestor / relative
    return relative


MODEL_DIR = _runfiles_data_path(
    Path("src/extensions/score_metamodel/agent_context/tests/model")
)
SIMPLE_MODEL_PATH = MODEL_DIR / "simple_model.yaml"
METAMODEL_PATH = _runfiles_data_path(
    Path("src/extensions/score_metamodel/metamodel.yaml")
)


def _projection(path: Path) -> dict[str, Any]:
    raw_bytes = path.read_bytes()
    return build_projection(
        load_metamodel_yaml(path), hashlib.sha256(raw_bytes).hexdigest()
    )


def test_relative_argument_resolves_against_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    argument = Path("__agent_context_workspace_fixture__/metamodel.yaml")

    assert not argument.is_file()
    assert resolve_metamodel_path(argument, workspace=str(workspace)) == (
        workspace / argument
    )


def test_absolute_argument_is_returned_unchanged(tmp_path: Path) -> None:
    argument = tmp_path / "metamodel.yaml"

    assert resolve_metamodel_path(argument, workspace=str(tmp_path / "workspace")) == (
        argument
    )


def test_existing_relative_argument_is_returned_unchanged() -> None:
    argument = Path("src/extensions/score_metamodel/metamodel.yaml")

    assert argument.is_file()
    assert resolve_metamodel_path(argument, workspace="/not-used") == argument


def test_relative_argument_without_workspace_is_returned_unchanged() -> None:
    argument = Path("missing/metamodel.yaml")

    assert resolve_metamodel_path(argument, workspace=None) == argument


def test_default_path_is_packaged_metamodel() -> None:
    path = resolve_metamodel_path(None)

    assert path.is_file()
    assert path.name == "metamodel.yaml"
    assert path.parent.name == "score_metamodel"
    assert path.parent.parent.name == "extensions"
    assert path.parent.parent.parent.name == "src"


def test_small_fixture_matches_complete_golden_json() -> None:
    fixture = SIMPLE_MODEL_PATH
    expected = (MODEL_DIR / "simple_expected.json").read_text(encoding="utf-8")

    assert render_projection(_projection(fixture)) == expected


def test_real_metamodel_has_complete_structural_projection() -> None:
    source = load_metamodel_yaml(METAMODEL_PATH)
    projection = _projection(METAMODEL_PATH)
    source_types = set(source["needs_types"])
    generated_types = projection["need_types"]

    assert len(generated_types) == len(source_types)
    assert [item["name"] for item in generated_types] == sorted(source_types)

    for need_type in generated_types:
        options = {option["name"]: option for option in need_type["options"]}
        assert options["version"] == {
            "name": "version",
            "pattern": "^[0-9]+$",
            "required": True,
            "inherited": True,
        }
        for option_name in ("source_code_link", "testlink"):
            assert options[option_name]["required"] is False
            assert options[option_name]["inherited"] is True

    by_name = {item["name"]: item for item in generated_types}
    comp_links = {link["name"]: link for link in by_name["comp_req"]["links"]}
    assert comp_links["satisfied_by"] == {
        "name": "satisfied_by",
        "targets": ["comp"],
        "any_target": False,
        "required": True,
    }
    dec_links = {link["name"]: link for link in by_name["dec_rec"]["links"]}
    assert dec_links["affects"]["any_target"] is True
    testcase_links = {link["name"]: link for link in by_name["testcase"]["links"]}
    assert testcase_links["fully_verifies"]["required"] is False
    assert testcase_links["partially_verifies"]["required"] is False

    undeclared_link_names = {
        link["name"] for link in projection["link_types"] if not link["declared"]
    }
    assert undeclared_link_names == {"links"}
    for link in projection["link_types"]:
        if link["declared"]:
            assert link["outgoing"] is not None
            assert link["incoming"] is not None

    known_types = {item["name"] for item in generated_types}
    graph_rules = projection["graph_rules"]
    assert len(graph_rules) == 5
    assert {rule["name"] for rule in graph_rules} == set(source["graph_checks"])
    assert all(rule["applies_to"] for rule in graph_rules)
    for rule in graph_rules:
        assert set(rule["applies_to"]) <= known_types


def test_projection_is_deterministic() -> None:
    fixture = MODEL_DIR / "nested_model.yaml"
    first = render_projection(_projection(fixture)).encode()
    second = render_projection(_projection(fixture)).encode()

    assert first == second


def test_digest_changes_with_input_bytes_and_repeats_for_identical_input(
    tmp_path: Path,
) -> None:
    source = SIMPLE_MODEL_PATH
    original = source.read_bytes()
    first_path = tmp_path / "first.yaml"
    second_path = tmp_path / "second.yaml"
    first_path.write_bytes(original)
    second_path.write_bytes(original)

    first = _projection(first_path)["metamodel_digest"]
    second = _projection(second_path)["metamodel_digest"]
    changed_path = tmp_path / "changed.yaml"
    changed_path.write_bytes(original + b"\n")
    changed = _projection(changed_path)["metamodel_digest"]

    assert first == second
    assert changed != first


def test_nested_graph_rules_round_trip_without_interpretation() -> None:
    projection = _projection(MODEL_DIR / "nested_model.yaml")
    rule = projection["graph_rules"][0]

    assert rule["condition_raw"] == {
        "and": [
            "status == valid",
            {"or": ["safety == QM", "safety == ASIL_B"]},
        ]
    }
    assert rule["check_raw"] == {
        "required_link": {
            "or": ["status == valid", "status == draft"],
        }
    }


def test_type_options_override_inherited_base_options() -> None:
    projection = _projection(MODEL_DIR / "precedence_model.yaml")
    options = {
        option["name"]: option for option in projection["need_types"][0]["options"]
    }

    assert options["shared"] == {
        "name": "shared",
        "pattern": "^type$",
        "required": False,
        "inherited": False,
    }
