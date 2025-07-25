import pytest

from ..external_needs import ExternalNeedsSource, parse_external_needs_sources


def test_empty_list():
    assert parse_external_needs_sources("[]") == []

def test_single_entry_with_path():
    result = parse_external_needs_sources('["@repo//foo/bar:baz"]')
    assert result == [ExternalNeedsSource(bazel_module="repo", path_to_target="foo/bar", target="baz")]

def test_single_entry_no_path():
    result = parse_external_needs_sources('["@repo//:target"]')
    assert result == [ExternalNeedsSource(bazel_module="repo", path_to_target="", target="target")]

def test_multiple_entries():
    result = parse_external_needs_sources('["@repo1//foo:bar", "@repo2//:baz"]')
    assert result == [
        ExternalNeedsSource(bazel_module="repo1", path_to_target="foo", target="bar"),
        ExternalNeedsSource(bazel_module="repo2", path_to_target="", target="baz")
    ]

def test_invalid_entry():
    with pytest.raises(ValueError):
        parse_external_needs_sources('["not_a_valid_string"]')


def test_parser():
    ...
