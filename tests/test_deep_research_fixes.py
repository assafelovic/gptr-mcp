#!/usr/bin/env python3
"""
Regression test for three deep_research/quick_search fixes:

1. Progress notifications: long-running calls now report MCP progress via
   ProgressLogHandler, so a client doesn't sit with no signal until the call
   finishes or its idle timeout aborts the connection.
2. Report synthesis: deep_research now also calls write_report() and
   returns it as "report" by default (synthesize_report=True), instead of
   only ever returning raw context that the caller had to know to pass to
   the separate write_report tool.
3. content_length: format_sources_for_response() now reads the "raw_content"
   key GPTResearcher.get_research_sources() actually populates, instead of
   a "content" key that was never present -- content_length was 0 for every
   source regardless of how much text was actually scraped.

Does not require the real gpt_researcher package: patches server.GPTResearcher
with a lightweight fake so this runs fast and without network/LLM access.
Run directly:

    python3 tests/test_deep_research_fixes.py
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("OPENAI_API_KEY", "unused-dummy-value-for-tests")


class _FakeGPTResearcher:
    def __init__(self, query, log_handler=None, **kwargs):
        self.query = query
        self.log_handler = log_handler
        self._sources = [
            {"title": "Example", "url": "http://example.com", "raw_content": "x" * 250},
            {"title": "NoContent", "url": "http://example.com/2"},
        ]

    async def conduct_research(self):
        if self.log_handler:
            await self.log_handler.on_research_step("start", {})
            await self.log_handler.on_tool_start("web_search")
            await self.log_handler.on_research_step("research_completed", {})

    async def quick_search(self, query):
        if self.log_handler:
            await self.log_handler.on_research_step("quick_search_start", {})
        return [{"title": "quick", "url": "http://example.com", "snippet": "..."}]

    async def write_report(self, custom_prompt=None):
        return f"# Report for {self.query}\n\nSynthesized findings."

    def get_research_context(self):
        return f"context for {self.query}"

    def get_research_sources(self):
        return self._sources

    def get_source_urls(self):
        return [s["url"] for s in self._sources]

    def get_costs(self):
        return 0.0


async def _run() -> None:
    import server
    from fastmcp import Client

    with patch("server.GPTResearcher", _FakeGPTResearcher):
        progress_events = []

        async def on_progress(progress, total, message):
            progress_events.append((progress, message))

        async with Client(server.mcp, progress_handler=on_progress) as client:
            # Fix 1 + 2: progress reported, report synthesized by default.
            result = await client.call_tool("deep_research", {"query": "test query"})
            data = result.data
            assert data["status"] == "success", data
            assert "report" in data, "synthesize_report defaults True, report must be present"
            assert data["report"].startswith("# Report for test query"), data["report"]
            assert len(progress_events) >= 3, f"expected >=3 progress events, got {progress_events}"

            # Fix 3: content_length reflects raw_content, missing key doesn't crash.
            assert data["sources"][0]["content_length"] == 250, data["sources"]
            assert data["sources"][1]["content_length"] == 0, data["sources"]

            # synthesize_report=False must omit the report.
            progress_events.clear()
            result2 = await client.call_tool(
                "deep_research", {"query": "no report please", "synthesize_report": False}
            )
            assert "report" not in result2.data, "synthesize_report=False must omit report"

            # quick_search also reports progress.
            progress_events.clear()
            result3 = await client.call_tool("quick_search", {"query": "fast query"})
            assert result3.data["status"] == "success", result3.data
            assert len(progress_events) >= 1, "quick_search must report progress too"

    print("OK: deep_research/quick_search progress, report synthesis, and content_length fixes verified")


if __name__ == "__main__":
    asyncio.run(_run())
