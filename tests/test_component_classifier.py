"""Tests for the component classifier module."""

import pytest

pytestmark = pytest.mark.unit

from tf.component_classifier import (
    ClassificationResult,
    classify_components,
    format_tags_for_tk,
    get_keyword_map_documentation,
    DEFAULT_KEYWORD_MAP,
)


class TestClassificationResult:
    """Test the ClassificationResult dataclass."""

    def test_empty_result_is_falsy(self):
        result = ClassificationResult()
        assert not result
        assert result.tags == []
        assert result.rationale == {}

    def test_result_with_tags_is_truthy(self):
        result = ClassificationResult(tags=["component:cli"])
        assert result
        assert result.tags == ["component:cli"]


class TestClassifyComponents:
    """Test the classify_components function."""

    def test_cli_keywords(self):
        """Test that CLI-related keywords are matched."""
        result = classify_components("Add --version flag to CLI")
        assert "component:cli" in result.tags
        assert "component:cli" in result.rationale
        assert "flag" in result.matched_keywords["component:cli"]
        assert "cli" in result.matched_keywords["component:cli"]

    def test_test_keywords(self):
        """Test that test-related keywords are matched."""
        result = classify_components("Add unit tests for login module")
        assert "component:tests" in result.tags
        assert "test" in result.matched_keywords["component:tests"]

    def test_docs_keywords(self):
        """Test that documentation keywords are matched."""
        result = classify_components("Update README with new examples")
        assert "component:docs" in result.tags
        assert "readme" in result.matched_keywords["component:docs"]

    def test_config_keywords(self):
        """Test that configuration keywords are matched."""
        result = classify_components("Add setting to config file")
        assert "component:config" in result.tags
        assert "config" in result.matched_keywords["component:config"]

    def test_api_keywords(self):
        """Test that API-related keywords are matched."""
        result = classify_components("Add REST API endpoint for users")
        assert "component:api" in result.tags
        assert "api" in result.matched_keywords["component:api"]
        assert "rest" in result.matched_keywords["component:api"]

    def test_multiple_components(self):
        """Test that multiple components can be detected."""
        result = classify_components(
            "Add CLI command with tests and docs",
        )
        assert "component:cli" in result.tags
        assert "component:tests" in result.tags
        assert "component:docs" in result.tags

    def test_description_is_used(self):
        """Test that description contributes to matching."""
        result = classify_components(
            "User authentication",
            "Add pytest coverage for login module",
        )
        assert "component:tests" in result.tags

    def test_no_match_returns_empty(self):
        """Test that no keywords match returns empty result."""
        result = classify_components("Something completely unrelated")
        assert not result.tags
        assert not result

    def test_custom_keywords(self):
        """Test that custom keywords can be added."""
        custom = {"component:ml": ["machine learning", "model", "training"]}
        result = classify_components(
            "Update ML model training",
            custom_keywords=custom,
        )
        assert "component:ml" in result.tags
        assert "model" in result.matched_keywords["component:ml"]

    def test_custom_keywords_merge_with_defaults(self):
        """Test that custom keywords merge with defaults."""
        custom = {"component:cli": ["custom-cli-keyword"]}
        result = classify_components(
            "Add custom-cli-keyword feature",
            custom_keywords=custom,
        )
        assert "component:cli" in result.tags
        assert "custom-cli-keyword" in result.matched_keywords["component:cli"]

    def test_custom_keyword_map_replaces_defaults(self):
        """Test that keyword_map completely replaces defaults."""
        custom_map = {"component:custom": ["custom"]}
        result = classify_components(
            "Add CLI feature",  # Would normally match component:cli
            keyword_map=custom_map,
        )
        # Should NOT have component:cli since we replaced the map
        assert "component:cli" not in result.tags
        assert not result.tags  # "cli" is not in custom_map

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        result = classify_components("Add CLI FLAG to Terminal")
        assert "component:cli" in result.tags

    def test_multi_word_keywords(self):
        """Test that multi-word keywords are matched correctly."""
        result = classify_components("Add unit test for feature")
        assert "component:tests" in result.tags
        assert "unit test" in result.matched_keywords["component:tests"]

    def test_tags_are_sorted(self):
        """Test that output tags are sorted alphabetically."""
        result = classify_components(
            "Add CLI with tests and API",
        )
        # Should be sorted: api, cli, tests
        assert result.tags == sorted(result.tags)


class TestFormatTagsForTk:
    """Test the format_tags_for_tk function."""

    def test_single_tag(self):
        assert format_tags_for_tk(["component:cli"]) == "component:cli"

    def test_multiple_tags(self):
        result = format_tags_for_tk(["component:cli", "component:tests"])
        assert result == "component:cli,component:tests"

    def test_empty_list(self):
        assert format_tags_for_tk([]) == ""


class TestGetKeywordMapDocumentation:
    """Test the get_keyword_map_documentation function."""

    def test_contains_component_headers(self):
        docs = get_keyword_map_documentation()
        assert "# Component Keyword Mapping" in docs
        for tag in DEFAULT_KEYWORD_MAP.keys():
            assert f"## {tag}" in docs

    def test_contains_keywords(self):
        docs = get_keyword_map_documentation()
        for keywords in DEFAULT_KEYWORD_MAP.values():
            for kw in list(keywords)[:3]:  # Check first 3 of each
                assert f"`{kw}`" in docs


class TestDefaultKeywordMap:
    """Test the default keyword map structure."""

    def test_all_tags_have_component_prefix(self):
        for tag in DEFAULT_KEYWORD_MAP.keys():
            assert tag.startswith("component:"), f"Tag {tag} missing component: prefix"

    def test_all_keywords_are_lowercase(self):
        for keywords in DEFAULT_KEYWORD_MAP.values():
            for kw in keywords:
                assert kw == kw.lower(), f"Keyword {kw} should be lowercase"

    def test_no_duplicate_keywords_per_component(self):
        for tag, keywords in DEFAULT_KEYWORD_MAP.items():
            assert len(keywords) == len(set(keywords)), f"Duplicates in {tag}"
