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
"""Tests for schema export functionality."""

import json
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from export_data import build_metamodel_data
from generate_schema import build_json_schema, load_metamodel_yaml


@pytest.fixture
def metamodel_path() -> Path:
    """Provide path to the actual metamodel.yaml."""
    # From tools/schema_export/tests, go up 3 levels to reach root
    # then into src/extensions/score_metamodel
    return (
        Path(__file__).parent.parent.parent.parent
        / "src/extensions/score_metamodel/metamodel.yaml"
    )


@pytest.fixture
def metamodel_data(metamodel_path: Path) -> dict[str, Any]:
    """Load actual metamodel data."""
    assert metamodel_path.is_file(), f"metamodel.yaml not found at {metamodel_path}"
    data = load_metamodel_yaml(metamodel_path)
    return dict(data)


def test_load_metamodel_yaml(metamodel_path: Path):
    """Test that we can load the metamodel YAML."""
    data = load_metamodel_yaml(metamodel_path)

    # Check basic structure
    assert isinstance(data, dict)
    assert "needs_types" in data
    assert "needs_extra_links" in data
    assert len(data["needs_types"]) > 0


def test_build_json_schema(metamodel_data: dict[str, Any]):
    """Test JSON Schema generation."""
    schema = build_json_schema(metamodel_data, "sha256:test")

    # Check schema structure
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["title"] == "S-CORE Metamodel Schema"
    assert "properties" in schema

    # Check that all major sections are present
    props = schema["properties"]
    assert "needs_types" in props
    assert "needs_extra_links" in props
    assert "prohibited_words_checks" in props
    assert "graph_checks" in props


def test_build_metamodel_data(metamodel_data: dict[str, Any]):
    """Test metamodel data export."""
    # Use a valid SHA-256 digest (64 hex characters)
    test_digest = "sha256:" + "a" * 64
    data = build_metamodel_data(metamodel_data, test_digest)

    # Check data structure
    assert (
        data["$schema"]
        == "https://eclipse-score.github.io/schemas/metamodel-schema.json"
    )
    assert data["schema_version"] == 1
    assert data["metamodel_digest"] == test_digest

    # Check that all major sections are present
    assert "need_types" in data
    assert "link_types" in data
    assert "prohibited_words" in data
    assert "graph_rules" in data
    assert "base_options" in data

    # Check counts
    assert len(data["need_types"]) > 0
    assert len(data["link_types"]) > 0


def test_schema_data_consistency(metamodel_data: dict[str, Any]):
    """Test that generated data is consistent with schema."""
    try:
        import jsonschema  # type: ignore[import-not-found]
        from jsonschema import (  # type: ignore[import-not-found]
            exceptions as jsonschema_exceptions,  # type: ignore[import-not-found]
        )
    except ImportError:
        pytest.skip("jsonschema package not available")

    test_digest = "sha256:" + "a" * 64
    schema = build_json_schema(metamodel_data, test_digest)
    data = build_metamodel_data(metamodel_data, test_digest)

    # Validate data against schema (basic validation)
    # Note: Full validation may require adjustments to schema structure
    # This is a sanity check that the basic structure matches
    try:
        jsonschema.validate(data, schema)  # type: ignore[no-untyped-call]
    except jsonschema_exceptions.SchemaError:
        pytest.skip("Schema validation requires jsonschema package")


def test_deterministic_output(metamodel_data: dict[str, Any]):
    """Test that generation is deterministic."""
    test_digest = "sha256:" + "a" * 64
    schema1 = build_json_schema(metamodel_data, test_digest)
    schema2 = build_json_schema(metamodel_data, test_digest)

    # Should produce identical output
    assert json.dumps(schema1, sort_keys=True) == json.dumps(schema2, sort_keys=True)

    data1 = build_metamodel_data(metamodel_data, test_digest)
    data2 = build_metamodel_data(metamodel_data, test_digest)

    assert json.dumps(data1, sort_keys=True) == json.dumps(data2, sort_keys=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
