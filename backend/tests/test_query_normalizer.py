"""Tests for query normalization (semanticAdditions.md §2)."""

import pytest

from app.services.retrieval.query_normalizer import normalize_query, compute_query_hash


class TestNormalizeQuery:
    def test_basic_normalization(self):
        """All these should canonicalize to the same form."""
        q1 = "How do I reset my password?"
        q2 = "how do i reset my password"
        q3 = " HOW DO I RESET MY PASSWORD? "

        n1 = normalize_query(q1)
        n2 = normalize_query(q2)
        n3 = normalize_query(q3)

        assert n1 == n2 == n3 == "how do i reset my password"

    def test_preserves_technical_terms(self):
        """C# and C++ should not be mangled."""
        q1 = "What's the difference between C# and C++?"
        normalized = normalize_query(q1)

        # Both # and . should be preserved
        assert "c#" in normalized
        assert "c++" in normalized

    def test_unicode_normalization(self):
        """NFKC normalization should normalize different Unicode forms."""
        # Curly quotes → straight quotes (stripped as punctuation)
        q1 = "'hello' world"
        n1 = normalize_query(q1)
        assert "'he" not in n1  # curly quotes removed

    def test_whitespace_collapse(self):
        """Multiple spaces, tabs, newlines should collapse to single space."""
        q1 = "hello   world\t\n  foo"
        n1 = normalize_query(q1)
        assert n1 == "hello world foo"

    def test_empty_query(self):
        assert normalize_query("") == ""
        assert normalize_query("   ") == ""
        assert normalize_query("???") == ""

    def test_punctuation_stripping(self):
        """Non-semantic punctuation should be removed."""
        q1 = "error: file not found!"
        n1 = normalize_query(q1)
        assert ":" not in n1
        assert "!" not in n1
        assert "error" in n1
        assert "file not found" in n1

    def test_api_names_preserved(self):
        """Dot-separated API names should keep their dots."""
        q1 = "How do I call JSON.parse?"
        n1 = normalize_query(q1)
        assert "json.parse" in n1

    def test_acronyms_preserved(self):
        """Acronyms should not be split or altered."""
        q1 = "What is CSRF and XSS protection?"
        n1 = normalize_query(q1)
        assert "csrf" in n1
        assert "xss" in n1
        assert "csrf and xss protection" in n1

    def test_version_numbers(self):
        """Version numbers with dots should be preserved."""
        q1 = "Python 3.11 features"
        n1 = normalize_query(q1)
        assert "python 3.11 features" in n1

    def test_compute_query_hash(self):
        """Hash should be deterministic and different for different queries."""
        h1 = compute_query_hash("hello world")
        h2 = compute_query_hash("hello world")
        h3 = compute_query_hash("goodbye world")

        assert h1 == h2  # Same input → same hash
        assert h1 != h3  # Different input → different hash
        assert len(h1) == 32  # Truncated to 32 chars
