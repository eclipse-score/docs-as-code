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
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest

from src.extensions.score_source_code_linker.need_source_links import (
    NeedSourceLinks,
    SourceCodeLinks,
)
from src.extensions.score_source_code_linker.needlinks import NeedLink
from src.extensions.score_source_code_linker.repo_source_links import (
    RepoInfo,
    RepoSourceLinks,
    RepoSourceLinks_JSON_Decoder,
    group_needs_by_repo,
    load_repo_source_links_json,
    store_repo_source_links_json,
)
from src.extensions.score_source_code_linker.testlink import DataForTestLink

"""
                        ────────────────INFORMATION───────────────

#              ╭──────────────────────────────────────────────────────────╮
#              │                  partially generated                     │
#              │                Human screened and adapted                │
#              │            though still be aware of mistakes             │
#              ╰──────────────────────────────────────────────────────────╯

"""


#              ╭──────────────────────────────────────────────────────────╮
#              │                    JSON ENCODER TEST                     │
#              ╰──────────────────────────────────────────────────────────╯


def encode_comment(s: str) -> str:
    return s.replace(" ", "-----", 1)


def decode_comment(s: str) -> str:
    return s.replace("-----", " ", 1)


def SourceCodeLinks_TEST_JSON_Decoder(
    d: dict[str, Any],
) -> SourceCodeLinks | dict[str, Any]:
    if "need" in d and "links" in d:
        links = d["links"]

        # Decode CodeLinks
        code_links = []
        for cl in links.get("CodeLinks", []):
            # Decode the tag and full_line fields
            if "tag" in cl:
                cl["tag"] = decode_comment(cl["tag"])
            if "full_line" in cl:
                cl["full_line"] = decode_comment(cl["full_line"])
            code_links.append(NeedLink(**cl))

        # Decode TestLinks
        return SourceCodeLinks(
            need=d["need"],
            links=NeedSourceLinks(
                CodeLinks=code_links,
                TestLinks=[DataForTestLink(**tl) for tl in links.get("TestLinks", [])],
            ),
        )
    return d


class repoSourceLinks_TEST_JSON_Encoder(json.JSONEncoder):
    def default(self, o: object) -> str | dict[str, Any]:
        if isinstance(o, Path):
            return str(o)
        # We do not want to save the metadata inside the codelink or testlink
        # As we save this already in a structure above it
        # (hash, repo_name, url)
        if isinstance(o, NeedLink | DataForTestLink):
            d = o.to_dict_without_metadata()
            tag = d.get("tag", "")
            full_line = d.get("full_line", "")
            assert isinstance(tag, str)
            assert isinstance(full_line, str)
            d["tag"] = encode_comment(tag)
            d["full_line"] = encode_comment(full_line)
            return d
        # We need to split this up, otherwise the nested
        # dictionaries won't get split up and we will not
        # run into the 'to_dict_without_metadata' as
        # everything will be converted to a normal dictionary
        if isinstance(o, RepoSourceLinks):
            return {
                "repo": asdict(o.repo),
                "needs": o.needs,  # Let the encoder handle the list
            }
        if isinstance(o, SourceCodeLinks):
            return {
                "need": o.need,
                "links": o.links,
            }
        if isinstance(o, NeedSourceLinks):
            return {
                "CodeLinks": o.CodeLinks,
                "TestLinks": o.TestLinks,
            }
        return super().default(o)


def repoSourceLinks_TEST_JSON_Decoder(
    d: dict[str, Any],
) -> RepoSourceLinks | dict[str, Any]:
    if "repo" in d and "needs" in d:
        repo = d["repo"]
        needs = d["needs"]
        return RepoSourceLinks(
            repo=RepoInfo(
                name=repo.get("name"),
                hash=repo.get("hash"),
                url=repo.get("url"),
            ),
            # We know this can only be list[SourceCodeLinks] and nothing else
            # Therefore => we ignore the type error here
            needs=[SourceCodeLinks_TEST_JSON_Decoder(need) for need in needs],  # type: ignore
        )
    return d


def test_json_encoder_removes_metadata_from_needlink():
    """Happy path: NeedLink metadata fields are excluded from JSON output"""
    encoder = repoSourceLinks_TEST_JSON_Encoder()
    needlink = NeedLink(
        file=Path("src/test.py"),
        line=10,
        tag="#" + " req-Id:",
        need="REQ_1",
        full_line="#" + " req-Id: REQ_1",
        repo_name="test_repo",
        url="https://github.com/test/repo",
        hash="abc123",
    )
    result = encoder.default(needlink)

    assert isinstance(result, dict)
    assert "repo_name" not in result
    assert "url" not in result
    assert "hash" not in result
    assert result["need"] == "REQ_1"
    assert result["line"] == 10


def test_json_encoder_removes_metadata_from_testlink():
    """Happy path: DataForTestLink metadata fields are excluded from JSON output"""
    encoder = repoSourceLinks_TEST_JSON_Encoder()
    testlink = DataForTestLink(
        name="test_something",
        file=Path("src/test_file.py"),
        need="REQ_1",
        line=20,
        verify_type="fully",
        result="passed",
        result_text="",
        repo_name="test_repo",
        url="https://github.com/test/repo",
        hash="abc123",
    )
    result = encoder.default(testlink)

    assert isinstance(result, dict)
    assert "repo_name" not in result
    assert "url" not in result
    assert "hash" not in result
    assert result["name"] == "test_something"
    assert result["need"] == "REQ_1"


def test_json_encoder_converts_path_to_string():
    """Happy path: Path objects are converted to strings"""
    encoder = repoSourceLinks_TEST_JSON_Encoder()
    result = encoder.default(Path("/test/path/file.py"))
    assert result == "/test/path/file.py"
    assert isinstance(result, str)


# ============================================================================
# JSON Decoder Tests
# ============================================================================


def test_json_decoder_reconstructs_repo_source_links():
    """Happy path: Valid JSON dict is decoded into repoSourceLinks"""
    json_data: dict[str, Any] = {
        "repo": {"name": "test_repo", "hash": "hash1", "url": "url1"},
        "needs": [
            {
                "need": "REQ_1",
                "links": {"CodeLinks": [], "TestLinks": []},
            }
        ],
    }
    result = RepoSourceLinks_JSON_Decoder(json_data)

    assert isinstance(result, RepoSourceLinks)
    assert result.repo.name == "test_repo"
    assert result.repo.hash == "hash1"
    assert result.repo.url == "url1"
    assert len(result.needs) == 1


def test_json_decoder_returns_unchanged_for_non_repo_dict():
    """Edge case: Non-repoSourceLinks dicts are returned unchanged"""
    json_data = {"some": "data", "other": "values"}
    result = RepoSourceLinks_JSON_Decoder(json_data)
    assert result == json_data


# ============================================================================
# Store/Load Tests
# ============================================================================


def test_store_and_load_roundtrip(tmp_path: Path):
    """Happy path: Store and load preserves data correctly"""
    repo = RepoInfo(name="test_repo", hash="hash1", url="url1")
    needlink = NeedLink(
        file=Path("src/test.py"),
        line=10,
        tag="#" + " req-Id:",
        need="REQ_1",
        full_line="#" + " req-Id: REQ_1",
        repo_name="test_repo",
        url="url1",
        hash="hash1",
    )
    scl = SourceCodeLinks(
        need="REQ_1",
        links=NeedSourceLinks(CodeLinks=[needlink], TestLinks=[]),
    )
    repo_links = RepoSourceLinks(repo=repo, needs=[scl])

    test_file = tmp_path / "test.json"
    store_repo_source_links_json(test_file, [repo_links])
    loaded = load_repo_source_links_json(test_file)

    assert len(loaded) == 1
    assert loaded[0].repo.name == "test_repo"
    assert loaded[0].needs[0].need == "REQ_1"


def test_store_creates_parent_directories(tmp_path: Path):
    """Edge case: Parent directories are created if they don't exist"""
    nested_path = tmp_path / "nested" / "deeply" / "test.json"
    repo = RepoInfo(name="test", hash="h", url="u")
    repo_links = RepoSourceLinks(repo=repo, needs=[])

    store_repo_source_links_json(nested_path, [repo_links])

    assert nested_path.exists()
    assert nested_path.parent.exists()


def test_load_empty_list(tmp_path: Path):
    """Edge case: Loading empty list returns empty list"""
    test_file = tmp_path / "empty.json"
    store_repo_source_links_json(test_file, [])

    loaded = load_repo_source_links_json(test_file)
    assert loaded == []


def test_load_validates_is_list(tmp_path: Path):
    """Bad path: Loading non-list JSON fails validation"""
    test_file = tmp_path / "not_list.json"
    test_file.write_text('{"repo": {}, "needs": []}')

    with pytest.raises(AssertionError, match="should be a list"):
        load_repo_source_links_json(test_file)


def test_load_validates_items_are_correct_type(tmp_path: Path):
    """Bad path: Loading list with invalid items fails validation"""
    test_file = tmp_path / "invalid_items.json"
    test_file.write_text('[{"invalid": "structure"}]')

    with pytest.raises(AssertionError, match="should be RepoSourceLink objects"):
        load_repo_source_links_json(test_file)


# ============================================================================
# group_needs_by_repo Tests
# ============================================================================


def test_group_needs_single_repo_with_codelinks():
    """Happy path: Multiple needs from same repo are grouped together"""
    needlink1 = NeedLink(
        file=Path("src/file1.py"),
        line=10,
        tag="#" + " req-Id:",
        need="REQ_1",
        full_line="#" + " req-Id: REQ_1",
        repo_name="shared_repo",
        url="https://github.com/test/repo",
        hash="hash1",
    )
    needlink2 = NeedLink(
        file=Path("src/file2.py"),
        line=20,
        tag="#" + " req-Id:",
        need="REQ_2",
        full_line="#" + " req-Id: REQ_2",
        repo_name="shared_repo",
        url="https://github.com/test/repo",
        hash="hash1",
    )

    scl1 = SourceCodeLinks(
        need="REQ_1", links=NeedSourceLinks(CodeLinks=[needlink1], TestLinks=[])
    )
    scl2 = SourceCodeLinks(
        need="REQ_2", links=NeedSourceLinks(CodeLinks=[needlink2], TestLinks=[])
    )

    result = group_needs_by_repo([scl1, scl2])

    assert len(result) == 1
    assert result[0].repo.name == "shared_repo"
    assert result[0].repo.hash == "hash1"
    assert len(result[0].needs) == 2
    assert len(result[0].needs[0].links.CodeLinks) == 1
    assert len(result[0].needs[1].links.CodeLinks) == 1


def test_group_needs_multiple_repos():
    """Happy path: Needs from different repos create separate groups"""
    needlink_a = NeedLink(
        file=Path("src/a.py"),
        line=10,
        tag="#" + " req-Id:",
        need="REQ_1",
        full_line="#" + " req-Id: REQ_1",
        repo_name="repo_a",
        url="https://github.com/a/repo",
        hash="hash_a",
    )
    needlink_b = NeedLink(
        file=Path("src/b.py"),
        line=20,
        tag="#" + " req-Id:",
        need="REQ_2",
        full_line="#" + " req-Id: REQ_2",
        repo_name="repo_b",
        url="https://github.com/b/repo",
        hash="hash_b",
    )

    scl1 = SourceCodeLinks(
        need="REQ_1", links=NeedSourceLinks(CodeLinks=[needlink_a], TestLinks=[])
    )
    scl2 = SourceCodeLinks(
        need="REQ_2", links=NeedSourceLinks(CodeLinks=[needlink_b], TestLinks=[])
    )

    result = group_needs_by_repo([scl1, scl2])

    assert len(result) == 2
    assert result[0].repo.name == "repo_a"
    assert result[0].repo.hash == "hash_a"
    assert result[0].repo.url == "https://github.com/a/repo"
    assert result[1].repo.name == "repo_b"
    assert result[1].repo.hash == "hash_b"
    assert result[1].repo.url == "https://github.com/b/repo"


def test_group_needs_with_testlinks_only():
    """Happy path: Needs with only test links (no code links) are grouped correctly"""
    testlink = DataForTestLink(
        name="test_feature",
        file=Path("tests/test.py"),
        need="REQ_1",
        line=15,
        verify_type="fully",
        result="passed",
        result_text="",
        repo_name="test_repo",
        url="https://github.com/test/repo",
        hash="hash1",
    )
    testlink2 = DataForTestLink(
        name="test_feature",
        file=Path("tests/test2.py"),
        need="REQ_10",
        line=153,
        verify_type="partially",
        result="passed",
        result_text="",
        repo_name="test_repo",
        url="https://github.com/test/repo",
        hash="hash1",
    )

    scl = SourceCodeLinks(
        need="REQ_1",
        links=NeedSourceLinks(CodeLinks=[], TestLinks=[testlink]),
    )
    scl2 = SourceCodeLinks(
        need="REQ_10",
        links=NeedSourceLinks(CodeLinks=[], TestLinks=[testlink2]),
    )

    result = group_needs_by_repo([scl, scl2])

    assert len(result) == 1
    assert result[0].repo.name == "test_repo"
    assert len(result[0].needs) == 2
    needs = [x.need for x in result[0].needs]
    assert "REQ_1" in needs
    assert "REQ_10" in needs
    assert len(result[0].needs[0].links.TestLinks) == 1
    assert len(result[0].needs[1].links.TestLinks) == 1


def test_group_needs_with_testlinks_different_repos():
    """Testing Testlinks grouping for different repos"""
    testlink = DataForTestLink(
        name="test_feature",
        file=Path("tests/test.py"),
        need="REQ_1",
        line=15,
        verify_type="fully",
        result="passed",
        result_text="",
        repo_name="repo_a",
        url="https://github.com/test_a/repo_a",
        hash="hash_a",
    )
    testlink2 = DataForTestLink(
        name="test_feature",
        file=Path("tests/test3.py"),
        need="REQ_10",
        line=153,
        verify_type="partially",
        result="passed",
        result_text="",
        repo_name="repo_b",
        url="https://github.com/test_b/repo_b",
        hash="hash_b",
    )

    scl = SourceCodeLinks(
        need="REQ_1",
        links=NeedSourceLinks(CodeLinks=[], TestLinks=[testlink]),
    )
    scl2 = SourceCodeLinks(
        need="REQ_10",
        links=NeedSourceLinks(CodeLinks=[], TestLinks=[testlink2]),
    )

    result = group_needs_by_repo([scl, scl2])

    assert len(result) == 2
    assert result[0].repo.name == "repo_a"
    assert result[0].repo.hash == "hash_a"
    assert result[0].repo.url == "https://github.com/test_a/repo_a"
    assert result[1].repo.name == "repo_b"
    assert result[1].repo.hash == "hash_b"
    assert result[1].repo.url == "https://github.com/test_b/repo_b"


def test_group_needs_empty_list():
    """Edge case: Empty list returns empty result"""
    result = group_needs_by_repo([])
    assert result == []


def test_group_needs_skips_needs_without_links():
    """
    Edge case: Needs with no code or test links are skipped
    This should normally never even be possible to get
    to this function. Though we should test what happens
    """
    scl_with_links = SourceCodeLinks(
        need="REQ_1",
        links=NeedSourceLinks(
            CodeLinks=[
                NeedLink(
                    file=Path("src/test.py"),
                    line=10,
                    tag="#" + " req-Id:",
                    need="REQ_1",
                    full_line="#" + " req-Id: REQ_1",
                    repo_name="repo_a",
                    url="url1",
                    hash="hash1",
                )
            ],
            TestLinks=[],
        ),
    )
    scl_without_links = SourceCodeLinks(
        need="REQ_2",
        links=NeedSourceLinks(CodeLinks=[], TestLinks=[]),
    )

    result = group_needs_by_repo([scl_with_links, scl_without_links])

    assert len(result) == 1
    assert result[0].needs[0].need == "REQ_1"
    assert result[0].needs[0].links.CodeLinks[0].full_line == "#" + " req-Id: REQ_1"


def test_group_needs_mixed_codelinks_and_testlinks():
    """Happy path: Needs with both code and test links are handled correctly"""
    needlink = NeedLink(
        file=Path("src/impl.py"),
        line=5,
        tag="#" + " req-Id:",
        need="REQ_1",
        full_line="#" + " req-Id: REQ_1",
        repo_name="repo_a",
        url="https://github.com/test/repo",
        hash="hash1",
    )
    testlink = DataForTestLink(
        name="test_impl",
        file=Path("tests/test_impl.py"),
        need="REQ_1",
        line=10,
        verify_type="fully",
        result="passed",
        result_text="",
        repo_name="repo_a",
        url="https://github.com/test/repo",
        hash="hash1",
    )

    scl = SourceCodeLinks(
        need="REQ_1",
        links=NeedSourceLinks(CodeLinks=[needlink], TestLinks=[testlink]),
    )

    result = group_needs_by_repo([scl])

    assert len(result) == 1
    assert len(result[0].needs[0].links.CodeLinks) == 1
    assert len(result[0].needs[0].links.TestLinks) == 1
