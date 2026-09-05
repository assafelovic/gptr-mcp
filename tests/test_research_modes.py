"""Unit tests for the deep_research mode arguments (report_type, tone, report_source).

Run with: python -m pytest tests/test_research_modes.py
No network or API keys are needed; the tests only exercise argument resolution and the
tool signature.
"""
import inspect
import os
import sys

os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("TAVILY_API_KEY", "test")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server  # noqa: E402


def test_defaults_resolve_to_research_report_web_objective():
    mode = server._resolve_research_mode("research_report", "objective", "web")
    assert mode["report_type"] == "research_report"
    assert mode["report_source"] == "web"
    assert mode["echo"]["tone"] == "objective"
    assert mode["echo"]["notes"] == []


def test_deep_mode_and_every_report_type_is_accepted():
    for rt in ("research_report", "detailed_report", "deep", "outline_report",
               "resource_report", "subtopic_report", "custom_report"):
        assert server._resolve_research_mode(rt, "objective", "web")["report_type"] == rt


def test_tone_is_matched_case_insensitively_by_enum_name():
    mode = server._resolve_research_mode("research_report", "Formal", "web")
    assert mode["echo"]["tone"] == "formal"
    assert mode["tone"] is not None


def test_unknown_values_fall_back_and_are_reported():
    mode = server._resolve_research_mode("banana", "sarcastic", "moon")
    assert mode["report_type"] == "research_report"
    assert mode["report_source"] == "web"
    assert mode["echo"]["tone"] == "objective"
    assert len(mode["echo"]["notes"]) == 3


def test_deep_research_tool_exposes_the_mode_arguments():
    fn = getattr(server.deep_research, "fn", server.deep_research)
    params = inspect.signature(fn).parameters
    assert list(params)[:4] == ["query", "report_type", "tone", "report_source"]
    assert params["report_type"].default == "research_report"
    assert params["tone"].default == "objective"
    assert params["report_source"].default == "web"
