"""Tests for markdown section parsing and pagination."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils import parse_report_sections, chunk_context


class TestParseReportSections:
    def test_splits_on_h2_headers(self):
        md = "# Title\nIntro text\n## Section A\nContent A\n## Section B\nContent B"
        sections = parse_report_sections(md)
        assert len(sections) == 3
        assert sections[0]["title"] == "Title"
        assert "Intro text" in sections[0]["content"]
        assert sections[1]["title"] == "Section A"
        assert "Content A" in sections[1]["content"]
        assert sections[2]["title"] == "Section B"

    def test_word_count(self):
        # word_count includes the ## header line in the content
        md = "## One\nfoo bar baz\n## Two\na b c d e"
        sections = parse_report_sections(md)
        # "## One\nfoo bar baz" = 5 words (## + One + foo + bar + baz)
        assert sections[0]["word_count"] == 5
        # "## Two\na b c d e" = 7 words (## + Two + a + b + c + d + e)
        assert sections[1]["word_count"] == 7

    def test_preserves_index(self):
        md = "## A\nx\n## B\ny\n## C\nz"
        sections = parse_report_sections(md)
        assert [s["index"] for s in sections] == [0, 1, 2]

    def test_no_headers(self):
        md = "Just plain text with no headers at all."
        sections = parse_report_sections(md)
        assert len(sections) == 1
        assert sections[0]["title"] == "Content"
        assert sections[0]["index"] == 0

    def test_h3_not_split(self):
        md = "## Main\ntext\n### Sub\nmore text"
        sections = parse_report_sections(md)
        assert len(sections) == 1
        assert "### Sub" in sections[0]["content"]


class TestChunkContext:
    def test_chunks_by_word_limit(self):
        snippets = [" ".join(["word"] * 500) for _ in range(5)]
        chunks = chunk_context(snippets, max_words=1000)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert chunk["word_count"] <= 1000

    def test_single_snippet_fits(self):
        snippets = ["hello world"]
        chunks = chunk_context(snippets, max_words=2000)
        assert len(chunks) == 1
        assert chunks[0]["word_count"] == 2

    def test_empty_input(self):
        chunks = chunk_context([], max_words=2000)
        assert len(chunks) == 0

    def test_preserves_index(self):
        snippets = [" ".join(["word"] * 500) for _ in range(4)]
        chunks = chunk_context(snippets, max_words=600)
        indices = [c["index"] for c in chunks]
        assert indices == list(range(len(chunks)))
