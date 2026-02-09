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
# pyright: reportPrivateUsage=false
import json
from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock, patch

from src.extensions.score_metamodel.metamodel_types import ScoreNeedType
from src.extensions.score_metamodel.sn_schemas import (
    IGNORE_FIELDS,
    SN_ARRAY_FIELDS,
    _build_local_validator,
    _build_need_type_schema,
    _classify_links,
    get_array_pattern_schema,
    get_field_pattern_schema,
    get_pattern_schema,
    write_sn_schemas,
)

# =============================================================================
# Tests for get_pattern_schema
# =============================================================================


class TestGetPatternSchema:
    def test_returns_string_type_with_pattern(self) -> None:
        result = get_pattern_schema("^[A-Z]+$")
        assert result == {"type": "string", "pattern": "^[A-Z]+$"}

    def test_preserves_complex_regex(self) -> None:
        pattern = r"^(feat|fix|chore)\/.+$"
        result = get_pattern_schema(pattern)
        assert result["type"] == "string"
        assert result["pattern"] == pattern


# =============================================================================
# Tests for get_array_pattern_schema
# =============================================================================


class TestGetArrayPatternSchema:
    def test_returns_array_type_with_items(self) -> None:
        result = get_array_pattern_schema("^tag_.*$")
        assert result == {
            "type": "array",
            "items": {"type": "string", "pattern": "^tag_.*$"},
        }

    def test_items_match_get_pattern_schema(self) -> None:
        pattern = "^[a-z]+$"
        result = get_array_pattern_schema(pattern)
        assert result["items"] == get_pattern_schema(pattern)


# =============================================================================
# Tests for get_field_pattern_schema
# =============================================================================


class TestGetFieldPatternSchema:
    def test_scalar_field_returns_string_schema(self) -> None:
        result = get_field_pattern_schema("title", "^.+$")
        assert result == {"type": "string", "pattern": "^.+$"}

    def test_array_field_returns_array_schema(self) -> None:
        for array_field in SN_ARRAY_FIELDS:
            result = get_field_pattern_schema(array_field, "^[a-z]+$")
            assert result["type"] == "array", f"Field '{array_field}' should be array"
            assert "items" in result

    def test_unknown_field_returns_string_schema(self) -> None:
        result = get_field_pattern_schema("some_custom_field", "^.*$")
        assert result["type"] == "string"


# =============================================================================
# Tests for _classify_links
# =============================================================================


class TestClassifyLinks:
    def test_regex_link_classified_as_regex(self) -> None:
        links = {"parent_need": "^logic_arc_int__.+$"}
        regexes, targets = _classify_links(links, "my_type", mandatory=True)
        assert regexes == {"parent_need": "^logic_arc_int__.+$"}
        assert targets == {}

    def test_plain_type_classified_as_target(self) -> None:
        links = {"satisfies": "comp"}
        regexes, targets = _classify_links(links, "my_type", mandatory=False)
        assert regexes == {}
        assert targets == {"satisfies": "comp"}

    def test_comma_separated_mixed_values(self) -> None:
        links = {"related": "^arc_.+$, comp"}
        regexes, targets = _classify_links(links, "my_type", mandatory=True)
        assert regexes == {"related": "^arc_.+$"}
        assert targets == {"related": "comp"}

    def test_empty_links(self) -> None:
        regexes, targets = _classify_links({}, "my_type", mandatory=True)
        assert regexes == {}
        assert targets == {}

    def test_multiple_fields(self) -> None:
        links = {
            "satisfies": "req",
            "parent": "^parent__.+$",
        }
        regexes, targets = _classify_links(links, "my_type", mandatory=False)
        assert regexes == {"parent": "^parent__.+$"}
        assert targets == {"satisfies": "req"}

    def test_multiple_regex_for_same_field_logs_error(self) -> None:
        links = {"field": "^regex1$, ^regex2$"}
        with patch("src.extensions.score_metamodel.sn_schemas.LOGGER") as mock_logger:
            regexes, _ = _classify_links(links, "my_type", mandatory=True)
            mock_logger.error.assert_called_once()
            # Last regex overwrites previous ones
            assert regexes == {"field": "^regex2$"}

    def test_multiple_plain_targets_last_wins(self) -> None:
        links = {"field": "comp, sw_unit"}
        regexes, targets = _classify_links(links, "my_type", mandatory=True)
        assert regexes == {}
        # Last target overwrites
        assert targets == {"field": "sw_unit"}


# =============================================================================
# Tests for _build_local_validator
# =============================================================================


class TestBuildLocalValidator:
    def test_mandatory_fields_are_required(self) -> None:
        mandatory = {"status": "^(valid|draft)$"}
        result = _build_local_validator(mandatory, {}, {}, {})
        assert "status" in result["required"]
        assert "status" in result["properties"]
        assert result["properties"]["status"]["pattern"] == "^(valid|draft)$"

    def test_optional_fields_not_required(self) -> None:
        optional = {"comment": "^.*$"}
        result = _build_local_validator({}, optional, {}, {})
        assert "comment" not in result["required"]
        assert "comment" in result["properties"]

    def test_ignored_fields_excluded(self) -> None:
        mandatory = {field: "^.*$" for field in IGNORE_FIELDS}
        optional = {field: "^.*$" for field in IGNORE_FIELDS}
        result = _build_local_validator(mandatory, optional, {}, {})
        for field in IGNORE_FIELDS:
            assert field not in result["properties"]
            assert field not in result["required"]

    def test_mandatory_link_regexes_required_with_min_items(self) -> None:
        mandatory_link_regexes = {"satisfies": "^req__.+$"}
        result = _build_local_validator({}, {}, mandatory_link_regexes, {})
        assert "satisfies" in result["required"]
        assert result["properties"]["satisfies"] == {"type": "array", "minItems": 1}

    def test_optional_link_regexes_not_required(self) -> None:
        optional_link_regexes = {"related": "^rel__.+$"}
        result = _build_local_validator({}, {}, {}, optional_link_regexes)
        assert "related" not in result["required"]
        assert result["properties"]["related"] == {"type": "array"}

    def test_combined_fields_and_links(self) -> None:
        mandatory = {"status": "^valid$"}
        optional = {"comment": "^.*$"}
        mandatory_link_re = {"satisfies": "^req__.+$"}
        optional_link_re = {"related": "^rel__.+$"}
        result = _build_local_validator(
            mandatory, optional, mandatory_link_re, optional_link_re
        )
        assert set(result["required"]) == {"status", "satisfies"}
        assert set(result["properties"].keys()) == {
            "status",
            "comment",
            "satisfies",
            "related",
        }

    def test_empty_inputs(self) -> None:
        result = _build_local_validator({}, {}, {}, {})
        assert result["properties"] == {}
        assert result["required"] == []

    def test_array_field_in_mandatory(self) -> None:
        mandatory = {"tags": "^(safety|security)$"}
        result = _build_local_validator(mandatory, {}, {}, {})
        assert result["properties"]["tags"]["type"] == "array"
        assert "items" in result["properties"]["tags"]


# =============================================================================
# Tests for _build_need_type_schema
# =============================================================================


def _make_need_type(**overrides: Any) -> ScoreNeedType:
    """Helper to create a ScoreNeedType-like dict."""
    base: dict[str, Any] = {
        "directive": "test_type",
        "title": "Test Type",
        "prefix": "TT_",
    }
    base.update(overrides)
    return cast(ScoreNeedType, base)


class TestBuildNeedTypeSchema:
    def test_returns_none_for_no_constraints(self) -> None:
        need_type = _make_need_type()
        assert _build_need_type_schema(need_type) is None

    def test_returns_none_for_empty_constraints(self) -> None:
        need_type = _make_need_type(
            mandatory_options={},
            optional_options={},
            mandatory_links={},
            optional_links={},
        )
        assert _build_need_type_schema(need_type) is None

    def test_schema_has_correct_structure(self) -> None:
        need_type = _make_need_type(
            mandatory_options={"status": "^valid$"},
        )
        schema = _build_need_type_schema(need_type)
        assert schema is not None
        assert schema["id"] == "need-type-test_type"
        assert schema["severity"] == "violation"
        assert "select" in schema
        assert schema["select"]["properties"]["type"]["const"] == "test_type"
        assert "validate" in schema
        assert "local" in schema["validate"]

    def test_mandatory_fields_in_local_validator(self) -> None:
        need_type = _make_need_type(
            mandatory_options={"status": "^(valid|draft)$"},
        )
        schema = _build_need_type_schema(need_type)
        assert schema is not None
        local = schema["validate"]["local"]
        assert "status" in local["required"]
        assert "status" in local["properties"]

    def test_optional_fields_in_local_validator(self) -> None:
        need_type = _make_need_type(
            optional_options={"comment": "^.*$"},
        )
        schema = _build_need_type_schema(need_type)
        assert schema is not None
        local = schema["validate"]["local"]
        assert "comment" not in local["required"]
        assert "comment" in local["properties"]

    def test_mandatory_links_with_regex(self) -> None:
        need_type = _make_need_type(
            mandatory_links={"satisfies": "^req__.+$"},
        )
        schema = _build_need_type_schema(need_type)
        assert schema is not None
        local = schema["validate"]["local"]
        assert "satisfies" in local["required"]
        assert local["properties"]["satisfies"] == {"type": "array", "minItems": 1}

    def test_mandatory_links_with_plain_target(self) -> None:
        need_type = _make_need_type(
            mandatory_links={"satisfies": "comp"},
        )
        schema = _build_need_type_schema(need_type)
        assert schema is not None
        local = schema["validate"]["local"]
        # Plain targets don't produce local validation entries
        assert "satisfies" not in local["properties"]

    def test_optional_links_with_regex(self) -> None:
        need_type = _make_need_type(
            optional_links={"related": "^rel__.+$"},
        )
        schema = _build_need_type_schema(need_type)
        assert schema is not None
        local = schema["validate"]["local"]
        assert "related" not in local["required"]
        assert local["properties"]["related"] == {"type": "array"}


# =============================================================================
# Tests for write_sn_schemas
# =============================================================================


class TestWriteSnSchemas:
    def test_writes_json_file(self, tmp_path: Path) -> None:
        app = MagicMock()
        app.confdir = str(tmp_path)
        app.config = MagicMock()

        need_type: dict[str, Any] = {
            "directive": "req",
            "title": "Requirement",
            "prefix": "REQ_",
            "mandatory_options": {"status": "^valid$"},
        }
        metamodel = MagicMock()
        metamodel.needs_types = [need_type]

        write_sn_schemas(app, metamodel)

        output_path: Path = tmp_path / "schemas.json"
        assert output_path.exists()
        data = json.loads(output_path.read_text(encoding="utf-8"))
        assert "schemas" in data
        assert len(data["schemas"]) == 1
        assert data["schemas"][0]["id"] == "need-type-req"

    def test_sets_config_value(self, tmp_path: Path) -> None:
        app = MagicMock()
        app.confdir = str(tmp_path)
        app.config = MagicMock()

        metamodel = MagicMock()
        metamodel.needs_types = []

        write_sn_schemas(app, metamodel)

        assert app.config.needs_schema_definitions_from_json == "schemas.json"

    def test_skips_need_types_without_constraints(self, tmp_path: Path) -> None:
        app = MagicMock()
        app.confdir = str(tmp_path)
        app.config = MagicMock()

        need_type_with: dict[str, Any] = {
            "directive": "req",
            "title": "Requirement",
            "prefix": "REQ_",
            "mandatory_options": {"status": "^valid$"},
        }
        need_type_without: dict[str, Any] = {
            "directive": "info",
            "title": "Info",
            "prefix": "INF_",
        }
        metamodel = MagicMock()
        metamodel.needs_types = [need_type_with, need_type_without]

        write_sn_schemas(app, metamodel)

        output_path: Path = tmp_path / "schemas.json"
        data = json.loads(output_path.read_text(encoding="utf-8"))
        assert len(data["schemas"]) == 1
        assert data["schemas"][0]["id"] == "need-type-req"

    def test_writes_valid_json_with_multiple_types(self, tmp_path: Path) -> None:
        app = MagicMock()
        app.confdir = str(tmp_path)
        app.config = MagicMock()

        need_types: list[dict[str, Any]] = [
            {
                "directive": "req",
                "title": "Requirement",
                "prefix": "REQ_",
                "mandatory_options": {"status": "^valid$"},
            },
            {
                "directive": "spec",
                "title": "Specification",
                "prefix": "SPEC_",
                "optional_options": {"comment": "^.*$"},
            },
        ]
        metamodel = MagicMock()
        metamodel.needs_types = need_types

        write_sn_schemas(app, metamodel)

        output_path: Path = tmp_path / "schemas.json"
        data = json.loads(output_path.read_text(encoding="utf-8"))
        assert len(data["schemas"]) == 2
        ids = {s["id"] for s in data["schemas"]}
        assert ids == {"need-type-req", "need-type-spec"}
