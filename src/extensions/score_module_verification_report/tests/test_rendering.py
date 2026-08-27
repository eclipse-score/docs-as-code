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
"""Unit tests for the rendering helpers and the report template."""

import pytest
from score_module_verification_report import rendering

CONTEXT = {
    "report_id": "mod_vrep__x",
    "module_id": "mod__x",
    "module_slug": "x",
    "feature_id": "feat__x",
    "components": [{"id": "comp__x_json", "title": "JSON", "slug": "json"}],
}


@pytest.fixture(scope="module")
def rendered() -> str:
    return rendering.render_report(CONTEXT, None)


class TestQuoteForFilter:
    """Acceptance test 10: filter expressions with user-supplied IDs."""

    def test_plain_id_is_quoted(self) -> None:
        assert rendering.quote_for_filter("comp__a") == '"comp__a"'

    @pytest.mark.parametrize(
        "hostile",
        ['a" or True or "', "a' or 'b", "__import__('os')", "a\nb", "a; b", "a b", ""],
    )
    def test_hostile_input_is_rejected(self, hostile: str) -> None:
        with pytest.raises(ValueError):
            rendering.quote_for_filter(hostile)

    def test_rejected_ids_never_reach_a_rendered_filter(self) -> None:
        ids, warnings = rendering.parse_ids('comp__a, x"or(True)')
        assert ids == ["comp__a"]
        assert any("not a valid need id" in w for w in warnings)


class TestParseIds:
    def test_comma_and_whitespace_separated(self) -> None:
        ids, warnings = rendering.parse_ids("comp__a, comp__b\n   comp__c")
        assert ids == ["comp__a", "comp__b", "comp__c"]
        assert warnings == []

    def test_empty(self) -> None:
        assert rendering.parse_ids(None) == ([], [])
        assert rendering.parse_ids("  ") == ([], [])

    def test_version_qualifier_warns_instead_of_being_ignored(self) -> None:
        ids, warnings = rendering.parse_ids("comp__a[version==2]")
        assert ids == ["comp__a"]
        assert any("version qualifier" in w for w in warnings)

    def test_duplicates_are_deterministic(self) -> None:
        """Acceptance test 9: duplicate component ids."""
        ids, warnings = rendering.parse_ids("comp__b, comp__a, comp__b")
        assert ids == ["comp__b", "comp__a"]
        assert any("duplicate" in w for w in warnings)


class TestParseTitles:
    def test_titles_are_parsed(self) -> None:
        titles, warnings = rendering.parse_titles("comp__a = JSON\ncomp__b = Bits\n")
        assert titles == {"comp__a": "JSON", "comp__b": "Bits"}
        assert warnings == []

    def test_malformed_line_warns(self) -> None:
        titles, warnings = rendering.parse_titles("comp__a JSON")
        assert titles == {}
        assert len(warnings) == 1


class TestDerivations:
    def test_title_fallback(self) -> None:
        assert rendering.derive_title("comp__baselibs_json") == "Baselibs Json"
        assert rendering.derive_title("nounderscores") == "Nounderscores"

    def test_feature_is_derived_from_the_module(self) -> None:
        assert rendering.derive_feature_id("mod__baselibs") == "feat__baselibs"

    def test_feature_derivation_gives_up_rather_than_guessing(self) -> None:
        assert rendering.derive_feature_id("") == ""
        assert rendering.derive_feature_id("something_else") == ""

    def test_component_slug_drops_the_module_name(self) -> None:
        assert (
            rendering.derive_slug("comp__baselibs_bit_manipulation", "mod__baselibs")
            == "bitmanipulation"
        )
        assert rendering.derive_slug("mod__baselibs", "") == "baselibs"


class TestTemplateLocation:
    def test_template_is_a_need_file_in_the_needs_template_folder(self) -> None:
        """Sphinx-Needs templates end in ``.need`` and live in that one folder."""
        folder = rendering.shipped_template_folder()
        assert folder.name == "needs_templates"
        assert rendering.TEMPLATE_NAME.endswith(".need")
        assert (folder / rendering.TEMPLATE_NAME).is_file()


class TestTemplate:
    """The template owns the report's content and its section structure."""

    @pytest.mark.parametrize(
        "heading",
        [
            "Feature",
            "Feature Requirements Statistics",
            "Feature Architecture Statistics",
            "Feature Inspection Statistics",
            "Component Overview",
            "JSON",
        ],
    )
    def test_section_is_present(self, rendered: str, heading: str) -> None:
        assert f"\n{heading}\n{'+' * len(heading)}\n" in rendered

    def test_every_section_carries_a_namespaced_target(self, rendered: str) -> None:
        """Acceptance test 3: no collisions between two reports on one page."""
        targets = [line for line in rendered.splitlines() if line.startswith(".. _")]
        assert targets, "no section targets emitted"
        assert all(t.startswith(".. _mod_vrep__x__") for t in targets)
        assert ".. _mod_vrep__x__comp__x_json:" in targets

    def test_all_headings_use_one_underline_char(self, rendered: str) -> None:
        """Flat by construction: same style -> siblings, whatever the placement."""
        assert {line[0] for line in rendered.splitlines() if set(line) == {"+"}} == {
            "+"
        }

    @pytest.mark.parametrize(
        "rubric",
        [
            "Component Requirements Statistics",
            "Component Architecture Statistics",
            "Requirements Traceability",
            "Test Coverage",
            "Architectural Elements",
            "Verification & Safety Analysis Documents",
        ],
    )
    def test_component_internals_stay_rubrics(self, rendered: str, rubric: str) -> None:
        """No navigation is needed below a component, so no nesting is emitted."""
        assert f".. rubric:: {rubric}" in rendered
        assert f"\n{rubric}\n{'+' * len(rubric)}\n" not in rendered

    def test_statistics_are_needpie_filters(self, rendered: str) -> None:
        assert ".. needpie:: Feature Requirements Status" in rendered
        assert (
            'type == "feat_req" and "feat__x" in satisfied_by and status == "valid"'
            in rendered
        )
        assert (
            'type == "comp_req" and "comp__x_json" in satisfied_by '
            "and len(fully_verifies_back) > 0" in rendered
        )

    def test_work_product_rows_are_generated(self, rendered: str) -> None:
        assert ":need:`wp__sw_component_fmea`" in rendered
        assert (
            'type == "document" and "wp__sw_component_dfa" in realizes '
            'and "json" in id.replace("_", "").lower()' in rendered
        )

    def test_no_feature_renders_a_sentence_not_a_broken_filter(self) -> None:
        text = rendering.render_report({**CONTEXT, "feature_id": ""}, None)
        assert "feature sections\nstay empty" in text
        assert "needpie:: Feature" not in text

    def test_no_components_renders_a_sentence(self) -> None:
        text = rendering.render_report({**CONTEXT, "components": []}, None)
        assert "does not declare any covered components" in text


class TestRenderNeed:
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
