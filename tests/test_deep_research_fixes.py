#!/usr/bin/env python3
"""
Regression test for deep_research/quick_search fixes:

1. Progress notifications: long-running calls now report MCP progress via
   ProgressLogHandler, so a client doesn't sit with no signal until the call
   finishes or its idle timeout aborts the connection. This covers both of
   gpt_researcher's independent progress paths -- log_handler (coarse
   macro-checkpoints) and websocket (the fine-grained per-sub-query/
   per-source progress emitted during the actual search/scrape loop) --
   sharing one handler instance so both paths keep one monotonic counter.
2. Report synthesis: deep_research now also calls write_report() and
   returns it as "report" by default (synthesize_report=True), instead of
   only ever returning raw context that the caller had to know to pass to
   the separate write_report tool.
3. content_length: format_sources_for_response() now reads the "raw_content"
   key GPTResearcher.get_research_sources() actually populates, instead of
   a "content" key that was never present -- content_length was 0 for every
   source regardless of how much text was actually scraped.
4. The progress websocket is released (set to None) right after
   conduct_research()/quick_search() completes and before the researcher is
   stored in mcp.researchers, not just before an inline write_report() call.
   gpt_researcher's report-generation LLM call disables its normal
   10-attempt retry budget whenever a websocket is set and re-streams the
   whole report back through it as fake progress -- neither is wanted for
   report generation, only for search-loop progress. Releasing it only
   inside the synthesize_report=True branch left it armed on any researcher
   later reused by the standalone write_report tool via
   synthesize_report=False's documented research_id/search_id flow --
   exactly the workflow this fix exists to protect, hit through a second,
   easy-to-miss door. See server.py's _release_progress_websocket.
5. ProgressLogHandler's failure-swallowing log call uses
   logger.opt(exception=True), not the stdlib-style exc_info=True kwarg --
   loguru silently discards exc_info= (it's absorbed as an unused
   str.format() argument), which would otherwise turn every swallowed
   failure into a traceback-free, undiagnosable log line.

Does not require the real gpt_researcher package: patches server.GPTResearcher
with a lightweight fake so this runs fast and without network/LLM access.
Collectible by pytest; also runnable directly:

    python3 tests/test_deep_research_fixes.py
"""

import asyncio
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("OPENAI_API_KEY", "unused-dummy-value-for-tests")


class _FakeGPTResearcher:
    # Every constructed instance, in order, so a test can inspect what
    # server.py actually passed in and to which object -- independent of
    # the fake's own simulated event counts. Reset at the start of each
    # test that constructs one.
    instances: list = []

    def __init__(self, query, log_handler=None, websocket=None, **kwargs):
        self.query = query
        self.log_handler = log_handler
        self.websocket = websocket
        # self.websocket gets mutated (cleared) by server.py after
        # conduct_research(); keep the original construction-time value so
        # a test can still check what was actually passed in.
        self.websocket_at_construction = websocket
        self.websocket_at_write_report = "not-called"
        _FakeGPTResearcher.instances.append(self)
        self._sources = [
            {"title": "Example", "url": "http://example.com", "raw_content": "x" * 250},
            {"title": "NoContent", "url": "http://example.com/2"},
        ]

    async def conduct_research(self):
        if self.log_handler:
            await self.log_handler.on_research_step("start", {})
            await self.log_handler.on_tool_start("web_search")
        # Mirrors gpt_researcher's real stream_output() calls
        # (gpt_researcher/actions/utils.py), made throughout the actual
        # sub-query search/scrape loop -- the real bottleneck. That's a
        # separate mechanism from log_handler, gated on `websocket` alone --
        # this path was never wired to MCP progress before this fix.
        if self.websocket:
            await self.websocket.send_json({"type": "logs", "output": "running sub-query 1"})
            await self.websocket.send_json({"type": "logs", "output": "running sub-query 2"})
        if self.log_handler:
            await self.log_handler.on_research_step("research_completed", {})

    async def quick_search(self, query):
        if self.log_handler:
            await self.log_handler.on_research_step("quick_search_start", {})
        return [{"title": "quick", "url": "http://example.com", "snippet": "..."}]

    async def write_report(self, custom_prompt=None):
        # server.py must have released the researcher's websocket before
        # this runs -- either inline (deep_research(synthesize_report=True))
        # or earlier, before the researcher was stored for reuse by the
        # standalone write_report tool. See _release_progress_websocket.
        self.websocket_at_write_report = self.websocket
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

    _FakeGPTResearcher.instances.clear()

    with patch("server.GPTResearcher", _FakeGPTResearcher):
        instances = _FakeGPTResearcher.instances

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
            # 2 log_handler checkpoints + 2 websocket-path sub-query events;
            # the websocket-path count catches the regression this fake
            # simulates: without websocket= wired, log_handler alone only
            # covers the coarse macro-checkpoints, not the actual
            # search/scrape loop where these events would really fire.
            assert len(progress_events) >= 4, f"expected >=4 progress events (log_handler + websocket path), got {progress_events}"

            first_researcher = instances[-1]

            # The construction itself: both paths must be wired, and to the
            # *same* handler instance -- two separate instances would each
            # keep their own step counter and emit colliding, non-monotonic
            # progress values.
            assert first_researcher.websocket_at_construction is not None, "websocket= must be wired for search-loop progress"
            assert first_researcher.websocket_at_construction is first_researcher.log_handler, "both progress paths must share one handler instance"

            # Fix 4: websocket must be cleared before the inline write_report() runs.
            assert first_researcher.websocket_at_write_report is None, (
                "write_report() must be called with the researcher's websocket "
                "cleared, or the report LLM call loses its retry budget and "
                "the whole report gets re-streamed back as progress"
            )

            # Fix 3: content_length reflects raw_content, missing key doesn't crash.
            assert data["sources"][0]["content_length"] == 250, data["sources"]
            assert data["sources"][1]["content_length"] == 0, data["sources"]

            # synthesize_report=False must omit the report.
            progress_events.clear()
            result2 = await client.call_tool(
                "deep_research", {"query": "no report please", "synthesize_report": False}
            )
            assert "report" not in result2.data, "synthesize_report=False must omit report"
            research_id = result2.data["research_id"]

            # Fix 4's second door: a later, standalone write_report call
            # against a researcher stored via synthesize_report=False must
            # ALSO see a cleared websocket, not just the inline call above.
            # The websocket must have been released before storage, not
            # only inside the synthesize_report=True branch.
            result4 = await client.call_tool("write_report", {"research_id": research_id})
            assert result4.data["status"] == "success", result4.data
            deferred_researcher = instances[-1]
            assert deferred_researcher.websocket_at_write_report is None, (
                "a researcher stored via synthesize_report=False and later handed to "
                "the standalone write_report tool must also see websocket=None -- "
                "the release must happen before storage, not only before an inline "
                "write_report() call"
            )

            # quick_search also reports progress, and its stored researcher
            # must be released the same way (it can also be reused via
            # write_report, through the same mcp.researchers dict).
            progress_events.clear()
            result3 = await client.call_tool("quick_search", {"query": "fast query"})
            assert result3.data["status"] == "success", result3.data
            assert len(progress_events) >= 1, "quick_search must report progress too"
            search_id = result3.data["search_id"]

            result5 = await client.call_tool("write_report", {"research_id": search_id})
            assert result5.data["status"] == "success", result5.data
            searched_researcher = instances[-1]
            assert searched_researcher.websocket_at_write_report is None


def test_deep_research_and_quick_search_progress_and_report_fixes() -> None:
    asyncio.run(_run())


async def _run_send_json_fallbacks() -> None:
    from utils import ProgressLogHandler

    events = []

    class _FakeCtx:
        async def report_progress(self, progress: int, message: str) -> None:
            events.append((progress, message))

    handler = ProgressLogHandler(_FakeCtx())

    # Each of send_json's fallback branches, in priority order.
    await handler.send_json({"output": "from output", "content": "ignored", "type": "ignored"})
    await handler.send_json({"content": "from content", "type": "ignored"})
    await handler.send_json({"type": "from type"})
    await handler.send_json({})

    assert [message for _, message in events] == [
        "from output",
        "from content",
        "from type",
        "progress",
    ], events


def test_progress_log_handler_send_json_covers_all_fallback_branches() -> None:
    asyncio.run(_run_send_json_fallbacks())


async def _run_report_progress_failure_does_not_abort() -> None:
    from utils import ProgressLogHandler

    class _FailingCtx:
        async def report_progress(self, progress: int, message: str) -> None:
            raise RuntimeError("client disconnected")

    handler = ProgressLogHandler(_FailingCtx())

    # gpt_researcher's websocket-shaped stream_output() awaits send_json()
    # unguarded (unlike the defensive log_handler path in agent.py's
    # _log_event), so a broken transport here must not propagate and abort
    # whatever research is still in progress.
    await handler.send_json({"output": "progress update"})
    await handler.on_research_step("some_step", {})


def test_progress_log_handler_swallows_report_progress_failures() -> None:
    asyncio.run(_run_report_progress_failure_does_not_abort())


class _StubResearcherForReportGenerator:
    """Minimal stand-in for GPTResearcher, covering every attribute
    ReportGenerator.write_report() touches on the non-subtopic path."""

    def __init__(self, websocket):
        self.query = "q"
        self.cfg = SimpleNamespace(agent_role="role prompt")
        self.role = "role"
        self.report_type = "research_report"
        self.report_source = "web"
        self.tone = "objective"
        self.websocket = websocket
        self.headers = {}
        self.verbose = False
        self.context = "some research context"
        self.kwargs = {}

    def add_costs(self, *args, **kwargs) -> None:
        pass

    def get_research_images(self):
        return []


async def _run_installed_gpt_researcher_live_websocket_check() -> None:
    """server.py's _release_progress_websocket() relies on
    ReportGenerator.write_report() re-reading researcher.websocket live
    rather than a value frozen into research_params at __init__ time (a
    separate fix in the gpt-researcher fork). Verify that behaviorally
    against whatever gpt_researcher is actually installed/pinned right
    now: construct a real ReportGenerator, mutate websocket after
    construction the way server.py does, and check what actually reaches
    generate_report(). This is deliberately behavioral rather than
    grepping write_report()'s source -- a source-text match breaks on any
    behavior-preserving refactor (renamed variable, reformatted line, an
    equally-correct alternative fix shaped differently); asserting on the
    real call's kwargs does not.
    """
    from gpt_researcher.skills import writer

    captured: Dict[str, Any] = {}

    async def _fake_generate_report(**kwargs: Any) -> str:
        captured.update(kwargs)
        return "report"

    researcher = _StubResearcherForReportGenerator(websocket=object())
    generator = writer.ReportGenerator(researcher)
    # Mutate after construction, exactly as _release_progress_websocket does.
    researcher.websocket = None

    with patch.object(writer, "generate_report", _fake_generate_report):
        await generator.write_report()

    assert captured.get("websocket") is None, (
        "installed gpt_researcher's ReportGenerator.write_report() does not "
        "re-read researcher.websocket live -- server.py's "
        "_release_progress_websocket() is a no-op against this pin. "
        "Re-pin requirements.txt to a gpt-researcher commit containing the "
        "live-read fix (MrSampson/gpt-researcher, "
        "fix/report-generator-live-websocket) before relying on this."
    )


def test_installed_gpt_researcher_reads_websocket_live_at_report_time() -> None:
    asyncio.run(_run_installed_gpt_researcher_live_websocket_check())


if __name__ == "__main__":
    test_deep_research_and_quick_search_progress_and_report_fixes()
    test_progress_log_handler_send_json_covers_all_fallback_branches()
    test_progress_log_handler_swallows_report_progress_failures()
    test_installed_gpt_researcher_reads_websocket_live_at_report_time()
    print("OK: deep_research/quick_search progress, report synthesis, retry-budget, and content_length fixes verified")
