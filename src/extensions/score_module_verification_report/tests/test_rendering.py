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
"""Unit tests for the pure rendering helpers."""

import pytest
from score_module_verification_report import rendering


class TestQuoteForFilter:
    """Acceptance test 10: filter expressions with user-supplied IDs."""

    def test_plain_id_is_quoted(self) -> None:
        assert rendering.quote_for_filter("comp__a") == '"comp__a"'

    @pytest.mark.parametrize(
        "hostile",
        [
            'a" or True or "',
            "a' or True or 'b",
            "__import__('os')",
            "a\nb",
            "a; b",
            "a b",
            "",
        ],
    )
    def test_hostile_input_is_rejected(self, hostile: str) -> None:
        with pytest.raises(ValueError):
            rendering.quote_for_filter(hostile)

    def test_rejected_ids_never_reach_a_rendered_filter(self) -> None:
        parsed = rendering.parse_component_list('comp__a, x"or(True)')
        assert parsed.ids == ["comp__a"]
        assert any("not a valid need id" in w for w in parsed.warnings)

    def test_bare_words_survive_but_stay_quoted(self) -> None:
        # Whitespace is a separator, so a hostile value degenerates into
        # separate tokens. Each is still quoted, so the worst case is a filter
        # that matches nothing -- never one that evaluates injected code.
        parsed = rendering.parse_component_list("comp__a or True")
        assert parsed.ids == ["comp__a", "or", "True"]
        assert (
            rendering.render_scope_section("mod_vrep__x", parsed.ids, "id").count('"')
            == 6
        )


class TestParseComponentList:
    def test_comma_and_whitespace_separated(self) -> None:
        parsed = rendering.parse_component_list("comp__a, comp__b\n   comp__c")
        assert parsed.ids == ["comp__a", "comp__b", "comp__c"]
        assert parsed.warnings == []

    def test_empty(self) -> None:
        assert rendering.parse_component_list(None).ids == []
        assert rendering.parse_component_list("  ").ids == []

    def test_version_qualifier_warns_instead_of_being_ignored(self) -> None:
        parsed = rendering.parse_component_list("comp__a[version==2]")
        assert parsed.ids == ["comp__a"]
        assert any("version qualifier" in w for w in parsed.warnings)

    def test_duplicates_are_deterministic(self) -> None:
        """Acceptance test 9: duplicate component ids."""
        parsed = rendering.parse_component_list("comp__b, comp__a, comp__b")
        assert parsed.ids == ["comp__b", "comp__a"]
        assert any("duplicate" in w for w in parsed.warnings)


class TestTitles:
    def test_overrides_are_parsed(self) -> None:
        overrides, warnings = rendering.parse_title_overrides(
            "comp__a = JSON Utilities\ncomp__b = Bit Manipulation\n"
        )
        assert overrides == {
            "comp__a": "JSON Utilities",
            "comp__b": "Bit Manipulation",
        }
        assert warnings == []

    def test_malformed_override_warns(self) -> None:
        overrides, warnings = rendering.parse_title_overrides("comp__a JSON")
        assert overrides == {}
        assert len(warnings) == 1

    def test_derive_title_is_the_documented_fallback(self) -> None:
        assert rendering.derive_title("comp__baselibs_json") == "Baselibs Json"
        assert rendering.derive_title("nounderscores") == "Nounderscores"


class TestAnchors:
    def test_anchor_is_namespaced_by_report(self) -> None:
        """Acceptance test 3: no collisions between two reports on one page."""
        a = rendering.anchor("mod_vrep__one", "comp__shared")
        b = rendering.anchor("mod_vrep__two", "comp__shared")
        assert a != b
        assert a == "mod_vrep__one__comp__shared"

    def test_anchor_is_stable(self) -> None:
        assert rendering.anchor("mod_vrep__x", "comp__y") == rendering.anchor(
            "mod_vrep__x", "comp__y"
        )


class TestRenderedRst:
    def test_need_options_are_passed_through_verbatim(self) -> None:
        text = rendering.render_need(
            "mod_ver_report_need",
            "Baselibs Verification Report",
            {"id": "mod_vrep__baselibs", "covers": "comp__a, comp__b", "flag": None},
            ["Intro.", "", "More."],
        )
        assert ".. mod_ver_report_need:: Baselibs Verification Report" in text
        assert "   :covers: comp__a, comp__b" in text
        assert "   :flag: " in text
        assert "   Intro." in text

    def test_component_section_has_target_heading_ref_and_table(self) -> None:
        text = rendering.render_component_section(
            "mod_vrep__baselibs",
            "comp__a",
            "JSON Utilities",
            "id == {component_id} or {component_id} in belongs_to",
            "id;title",
        )
        assert ".. _mod_vrep__baselibs__comp__a:" in text
        assert "JSON Utilities\n++++++++++++++" in text
        assert ":need:`comp__a`" in text
        assert ':filter: id == "comp__a" or "comp__a" in belongs_to' in text

    def test_all_generated_headings_use_one_underline_char(self) -> None:
        """Flat by construction: same style -> siblings, whatever the placement."""
        text = "\n".join(
            [
                rendering.render_metadata_section("mod_vrep__x", "id"),
                rendering.render_scope_section("mod_vrep__x", ["comp__a"], "id"),
                rendering.render_component_section(
                    "mod_vrep__x", "comp__a", "A", "id == {component_id}", "id"
                ),
                rendering.render_evidence_section("mod_vrep__x", ["contains"], "id"),
            ]
        )
        underlines = {
            line[0] for line in text.splitlines() if set(line) and set(line) == {"+"}
        }
        assert underlines == {rendering.UNDERLINE}

    def test_empty_scope_renders_a_sentence_not_a_broken_filter(self) -> None:
        text = rendering.render_scope_section("mod_vrep__x", [], "id")
        assert "needtable" not in text
        assert "does not declare any covered components" in text

    def test_evidence_section_uses_backlinks(self) -> None:
        text = rendering.render_evidence_section(
            "mod_vrep__x", ["contains", "evidence"], "id"
        )
        assert (
            ':filter: "mod_vrep__x" in contains_back or "mod_vrep__x" in evidence_back'
            in text
        )
