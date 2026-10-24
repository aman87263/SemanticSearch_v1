"""Query normalization utilities for canonicalizing user search queries.

Implements the canonical-query cache strategy from semanticAdditions.md §2.
The goal is to map semantically-equivalent queries (differing only in case,
whitespace, punctuation, Unicode normalization form) into a single canonical
string so that cache hits are maximized without changing query semantics.
"""

import hashlib
import unicodedata


# Characters we preserve because they carry meaning inside technical
# identifiers. Stripping them would change semantics — e.g. "C#" vs "C",
# "C++" vs "C", "JSON.parse" vs "JSON parse", "gpt-4" vs "gpt 4".
# Everything else that is not alphanumeric or whitespace is treated as a
# separator and collapsed to a space.
_IDENTIFIER_CHARS = frozenset({"#", ".", "+", "-", "_"})


def normalize_query(query: str) -> str:
    """Normalize a raw user query into a canonical form.

    Steps:
      1. Unicode NFKC normalization (compatibility composition).
      2. Lowercasing.
      3. Replace non-semantic punctuation with spaces, preserving characters
         that matter inside technical identifiers (see ``_IDENTIFIER_CHARS``).
      4. Whitespace collapse (trim, internal runs -> single space).

    We deliberately do **not** perform stemming or stop-word removal, because
    those alter recall characteristics for technical documentation.
    """
    if not query:
        return ""

    # Unicode normalization
    text = unicodedata.normalize("NFKC", query)

    # Lowercase
    text = text.lower()

    # Replace separators, preserving technical identifier characters.
    text = "".join(
        ch if (ch.isalnum() or ch.isspace() or ch in _IDENTIFIER_CHARS) else " "
        for ch in text
    )

    # Collapse whitespace
    text = " ".join(text.split())

    return text


def compute_query_hash(canonical_query: str) -> str:
    """Deterministic SHA-256 hash of the canonical query (truncated for key length)."""
    return hashlib.sha256(canonical_query.encode("utf-8")).hexdigest()[:32]
