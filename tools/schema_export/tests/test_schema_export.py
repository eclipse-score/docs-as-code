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
"""Tests for metamodel data export functionality."""

import json

# Import the modules to test
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from export_data import build_metamodel_data, load_metamodel_yaml


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
def metamodel_data(metamodel_path: Path) -> Any:
    """Load actual metamodel data."""
    assert metamodel_path.is_file(), f"metamodel.yaml not found at {metamodel_path}"
    return load_metamodel_yaml(metamodel_path)


def test_load_metamodel_yaml(metamodel_path: Path):
    """Test that we can load the metamodel YAML."""
    data = load_metamodel_yaml(metamodel_path)

    # Check basic structure
    assert isinstance(data, dict)
    assert "needs_types" in data
    assert "needs_extra_links" in data
    assert len(data["needs_types"]) > 0


def test_build_metamodel_data(metamodel_data: Any):
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


def test_deterministic_output(metamodel_data: Any):
    """Test that generation is deterministic."""
    test_digest = "sha256:" + "a" * 64

    data1 = build_metamodel_data(metamodel_data, test_digest)
    data2 = build_metamodel_data(metamodel_data, test_digest)

    assert json.dumps(data1, sort_keys=True) == json.dumps(data2, sort_keys=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
