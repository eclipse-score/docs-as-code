# *******************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
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
from unittest.mock import mock_open, patch

from score_metamodel import ProhibitedWordCheck, load_metamodel_data

MODEL_DIR = Path(__file__).absolute().parent / "model"


def load_model_data(model_file: str) -> str:
    print(f"Loading model data from {model_file}")
    model_path = Path(MODEL_DIR) / model_file
    with open(model_path) as f:
        return f.read()


def test_load_metamodel_data_explicit_path():
    """When an explicit path is given, load_metamodel_data reads that file."""
    explicit_path = MODEL_DIR / "simple_model.yaml"
    result = load_metamodel_data(yaml_path=explicit_path)

    assert len(result.needs_types) == 1
    assert result.needs_types[0]["directive"] == "type1"


def test_load_metamodel_data():
    model_data: str = load_model_data("simple_model.yaml")

    with patch("builtins.open", mock_open(read_data=model_data)):
        # Call the function
        result = load_metamodel_data()

    # Assertions
    assert len(result.needs_types) == 1
    assert result.needs_types[0]["directive"] == "type1"
    assert result.needs_types[0]["title"] == "Type 1"
    assert result.needs_types[0]["prefix"] == "T1"
    assert result.needs_types[0].get("color") == "blue"
    assert result.needs_types[0].get("style") == "bold"
    assert result.needs_types[0]["mandatory_options"] == {
        # default id pattern: prefix + digits, lowercase letters and underscores
        "id": "^T1[0-9a-z_]+$",
        "opt1": "value1",
    }
    assert result.needs_types[0]["optional_options"] == {
        "opt2": "value2",
        "opt3": "value3",
        "global_opt": "global_value",
    }
    assert result.needs_types[0]["mandatory_links_str"] == {"link1": "value1"}
    assert result.needs_types[0]["optional_links_str"] == {"link2": "value2"}

    assert result.needs_links == {
        "link_option1": {
            "incoming": "incoming1",
            "outgoing": "outgoing1",
        }
    }

    assert result.needs_fields == {
        name: {"schema": {"type": "string"}, "default": ""}
        for name in ["global_opt", "opt1", "opt2", "opt3"]
    }

    assert result.prohibited_words_checks[0] == ProhibitedWordCheck(
        name="title_check", option_check={"title": ["stop_word1"]}
    )

    assert result.prohibited_words_checks[1] == ProhibitedWordCheck(
        name="content_check",
        option_check={"content": ["weak_word1"]},
        types=["req_type"],
    )

    defined_graph_check = result.needs_graph_check["needs_graph_check"]
    assert isinstance(defined_graph_check, dict)
    assert defined_graph_check["needs"] == {
        "include": "type1",
        "condition": "opt1 == test",
    }
    assert defined_graph_check["check"] == {
        "link1": "opt1 == test",
    }


def test_default_metamodel_contains_generic_verification_and_inspection_types():
    """Default metamodel contains generic module verification and inspection types."""
    result = load_metamodel_data()

    needs_types = {
        need_type["directive"]: need_type for need_type in result.needs_types
    }

    assert "mod_ver_report" in needs_types
    assert "mod_insp" in needs_types

    mod_ver_report = needs_types["mod_ver_report"]
    assert mod_ver_report["mandatory_links_str"]["belongs_to"] == "mod"
    assert mod_ver_report["optional_links_str"]["contains"] == "ANY"
    assert mod_ver_report["optional_links_str"]["evidence"] == "ANY"
    assert mod_ver_report["optional_links_str"]["covers"] == "ANY"

    mod_insp = needs_types["mod_insp"]
    assert mod_insp["mandatory_links_str"]["inspects"] == "ANY"
    assert mod_insp["optional_links_str"]["contains"] == "ANY"
    assert mod_insp["optional_links_str"]["evidence"] == "ANY"

    assert "evidence" in result.needs_links
    assert "inspects" in result.needs_links


def test_metamodel_schema_json_is_valid():
    """The metamodel JSON schema file must be syntactically valid JSON."""
    schema_path = Path(__file__).resolve().parent.parent / "metamodel-schema.json"
    with open(schema_path, encoding="utf-8") as schema_file:
        parsed = json.load(schema_file)

    assert isinstance(parsed, dict)
    assert "$schema" in parsed
