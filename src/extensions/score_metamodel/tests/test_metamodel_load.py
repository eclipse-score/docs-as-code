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

import pytest
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
        },
        "link1": {
            "incoming": "incoming_link1",
            "outgoing": "outgoing_link1",
        },
        "link2": {
            "incoming": "incoming_link2",
            "outgoing": "outgoing_link2",
        },
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


# A minimal metamodel that is valid on its own. Individual tests below rewrite
# only the link sections, so the rest stays out of the way.
_MODEL_TEMPLATE = """
needs_types:
  type1:
    title: "Type 1"
    prefix: "T1"
{links_section}
needs_extra_links:
{declared_section}
"""


def _write_model(tmp_path: Path, links_section: str, declared_section: str) -> Path:
    model = tmp_path / "model.yaml"
    model.write_text(
        _MODEL_TEMPLATE.format(
            links_section=links_section, declared_section=declared_section
        ),
        encoding="utf-8",
    )
    return model


_DECLARED_KNOWN = """  known_link:
    incoming: "incoming"
    outgoing: "outgoing"
"""


def test_declared_link_is_accepted(tmp_path: Path):
    """A link declared in needs_extra_links may be used by a type."""
    model = _write_model(
        tmp_path,
        '    optional_links:\n      known_link: "ANY"\n',
        _DECLARED_KNOWN,
    )

    result = load_metamodel_data(yaml_path=model)

    assert result.needs_types[0]["optional_links_str"] == {"known_link": "ANY"}


@pytest.mark.parametrize("section", ["mandatory_links", "optional_links"])
def test_undeclared_link_is_rejected(tmp_path: Path, section: str):
    """Using a link that needs_extra_links does not declare must fail parsing.

    Regression guard for #737: dec_rec used 'affects' before it was declared,
    and nothing reported it until the link silently failed to render (#725).
    """
    model = _write_model(
        tmp_path,
        f'    {section}:\n      ghost_link: "ANY"\n',
        _DECLARED_KNOWN,
    )

    with pytest.raises(SystemExit) as excinfo:
        load_metamodel_data(yaml_path=model)

    message = str(excinfo.value)
    assert "ghost_link" in message
    assert "type1" in message
    assert section in message


def test_sphinx_needs_builtin_links_are_accepted(tmp_path: Path):
    """'links' and 'parent_needs' are provided by sphinx-needs itself.

    sphinx-needs registers them when a configuration does not, so the
    metamodel legitimately uses them without declaring them. Several types
    (tsf, tenet, assertion, std_req) rely on this.
    """
    model = _write_model(
        tmp_path,
        '    optional_links:\n      links: "ANY"\n      parent_needs: "ANY"\n',
        _DECLARED_KNOWN,
    )

    result = load_metamodel_data(yaml_path=model)

    assert set(result.needs_types[0]["optional_links_str"]) == {
        "links",
        "parent_needs",
    }


def test_all_undeclared_links_are_reported_at_once(tmp_path: Path):
    """Every offending link is listed, so one run shows all the work to do."""
    model = _write_model(
        tmp_path,
        '    mandatory_links:\n      ghost_one: "ANY"\n'
        '    optional_links:\n      ghost_two: "ANY"\n',
        _DECLARED_KNOWN,
    )

    with pytest.raises(SystemExit) as excinfo:
        load_metamodel_data(yaml_path=model)

    message = str(excinfo.value)
    assert "ghost_one" in message
    assert "ghost_two" in message


def test_shipped_metamodel_declares_every_link_it_uses():
    """The metamodel shipped with this extension must satisfy the check."""
    load_metamodel_data()
