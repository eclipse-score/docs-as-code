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
from pathlib import Path
from unittest.mock import mock_open, patch

from score_metamodel import ProhibitedWordCheck, load_metamodel_data

MODEL_DIR = Path(__file__).absolute().parent / "model"


def load_model_data(model_file: str) -> str:
    print(f"Loading model data from {model_file}")
    model_path = Path(MODEL_DIR) / model_file
    with open(model_path) as f:
        return f.read()


def test_load_metamodel_data():
    model_data: str = load_model_data("simple_model.yaml")

    with patch("builtins.open", mock_open(read_data=model_data)):
        # Call the function
        result = load_metamodel_data()

    # Assertions
    assert "needs_types" in result
    assert len(result["needs_types"]) == 1
    assert result["needs_types"][0]["directive"] == "type1"
    assert result["needs_types"][0]["title"] == "Type 1"
    assert result["needs_types"][0]["prefix"] == "T1"
    assert result["needs_types"][0]["color"] == "blue"
    assert result["needs_types"][0]["style"] == "bold"
    assert result["needs_types"][0]["mandatory_options"] == {"opt1": "value1"}
    assert result["needs_types"][0]["opt_opt"] == {
        "opt2": "value2",
        "opt3": "value3",
        "global_opt": "global_value",
    }
    assert result["needs_types"][0]["req_link"] == [("link1", "value1")]
    assert result["needs_types"][0]["opt_link"] == [("link2", "value2")]

    assert "needs_extra_links" in result
    assert len(result["needs_extra_links"]) == 1
    assert result["needs_extra_links"][0] == {
        "option": "link_option1",
        "incoming": "incoming1",
        "outgoing": "outgoing1",
    }

    assert "needs_extra_options" in result
    assert result["needs_extra_options"] == ["global_opt", "opt1", "opt2", "opt3"]

    assert "prohibited_words_checks" in result
    assert result["prohibited_words_checks"][0] == ProhibitedWordCheck(
        name="title_check", option_check={"title": ["stop_word1"]}
    )

    assert result["prohibited_words_checks"][1] == ProhibitedWordCheck(
        name="content_check",
        option_check={"content": ["weak_word1"]},
        types=["req_type"],
    )

    assert "needs_graph_check" in result
    assert result["needs_graph_check"]["needs_graph_check"]["needs"] == {
        "include": "type1",
        "condition": "opt1 == test",
    }
    assert result["needs_graph_check"]["needs_graph_check"]["check"] == {
        "link1": "opt1 == test",
    }
