"""
GPT Researcher MCP Server Utilities

This module provides utility functions and helpers for the GPT Researcher MCP Server.
"""

import re
import sys
from typing import Dict, List, Optional, Tuple, Any
from loguru import logger

# Configure logging for console only (no file logging)
logger.configure(handlers=[{"sink": sys.stderr, "level": "INFO"}])

# Research store to track ongoing research topics and contexts
research_store = {}

# API Response Utilities
def create_error_response(message: str) -> Dict[str, Any]:
    """Create a standardized error response"""
    return {"status": "error", "message": message}


def create_success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a standardized success response"""
    return {"status": "success", **data}


def handle_exception(e: Exception, operation: str) -> Dict[str, Any]:
    """Handle exceptions in a consistent way"""
    error_message = str(e)
    logger.error(f"{operation} failed: {error_message}")
    return create_error_response(error_message)


def get_researcher_by_id(researchers_dict: Dict, research_id: str) -> Tuple[bool, Any, Dict[str, Any]]:
    """
    Helper function to retrieve a researcher by ID.
    
    Args:
        researchers_dict: Dictionary of research objects
        research_id: The ID of the research session
        
    Returns:
        Tuple containing (success, researcher_object, error_response)
    """
    if not researchers_dict or research_id not in researchers_dict:
        return False, None, create_error_response("Research ID not found. Please conduct research first.")
    return True, researchers_dict[research_id], {}


def format_sources_for_response(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format source information for API responses.
    
    Args:
        sources: List of source dictionaries
        
    Returns:
        Formatted source list for API responses
    """
    return [
        {
            "title": source.get("title", "Unknown"),
            "url": source.get("url", ""),
            "content_length": len(source.get("content", ""))
        }
        for source in sources
    ]


def format_context_with_sources(topic: str, context: str, sources: List[Dict[str, Any]]) -> str:
    """
    Format research context with sources for display.
    
    Args:
        topic: Research topic
        context: Research context
        sources: List of sources
        
    Returns:
        Formatted context string with sources
    """
    formatted_context = f"## Research: {topic}\n\n{context}\n\n"
    formatted_context += "## Sources:\n"
    for i, source in enumerate(sources):
        formatted_context += f"{i+1}. {source.get('title', 'Unknown')}: {source.get('url', '')}\n"
    return formatted_context


def store_research_results(topic: str, context: str, sources: List[Dict[str, Any]], 
                           source_urls: List[str], formatted_context: Optional[str] = None):
    """
    Store research results in the research store.
    
    Args:
        topic: Research topic
        context: Research context
        sources: List of sources
        source_urls: List of source URLs
        formatted_context: Optional pre-formatted context
    """
    research_store[topic] = {
        "context": formatted_context or context,
        "sources": sources,
        "source_urls": source_urls
    }


def create_research_prompt(topic: str, goal: str, report_format: str = "research_report") -> str:
    """Create a research query prompt that teaches the LLM about output types."""
    return f"""You have access to a web research system. Research the following:

Topic: {topic}
Goal: {goal}

OUTPUT TYPES (choose based on your needs):

  summary     (~300-500 tokens)  — Bullet-point key facts.
              Use for: factual lookups, quick answers, "what is X?"

  briefing    (~800-1500 tokens) — Executive prose synthesis.
              Use for: providing context to the user, explaining a topic

  report      (~2000-4000 tokens, paginated) — Full structured report.
              Use for: in-depth analysis the user explicitly asked for

  deep_report (~4000-8000 tokens, paginated) — Comprehensive multi-section.
              Use for: "write me a detailed report on X"

  raw_context (variable, paginated) — Unprocessed research snippets.
              Use for: when you want to reason over sources yourself

DECISION GUIDE:
- Default to "briefing" unless you have a reason to choose otherwise
- If the user just needs a fact -> "summary"
- If the user asked for a report/analysis -> "report" or "deep_report"
- If you need to cross-reference or verify claims -> "raw_context"
- For paginated types, you receive a table of contents first --
  request only the sections you need via get_report_section()

WORKFLOW:
1. Call deep_research(query, output_type="...") or quick_search(query)
2. For summary/briefing: use the result directly
3. For report/deep_report: review the TOC, fetch sections as needed
4. For raw_context: review chunks, synthesize your own answer
5. Optionally call write_report(research_id, output_type="...") to
   generate a different format from the same research data
"""


def parse_report_sections(markdown: str) -> list[dict]:
    """Split a markdown report into sections by ## headers.

    Returns list of dicts: {"index": int, "title": str, "content": str, "word_count": int}
    Content before the first ## becomes section 0 (titled from # header or "Content").
    h3 (###) headers are NOT split -- they stay within their parent section.
    """
    parts = re.split(r'^(## .+)$', markdown, flags=re.MULTILINE)

    sections = []

    preamble = parts[0].strip()
    if preamble:
        h1_match = re.match(r'^# (.+)$', preamble, re.MULTILINE)
        title = h1_match.group(1).strip() if h1_match else "Content"
        sections.append({
            "index": 0,
            "title": title,
            "content": preamble,
            "word_count": len(preamble.split()),
        })

    i = 1
    while i < len(parts):
        header = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        title = header.replace("## ", "", 1).strip()
        full_content = f"{header}\n{content}" if content else header
        sections.append({
            "index": len(sections),
            "title": title,
            "content": full_content,
            "word_count": len(full_content.split()),
        })
        i += 2

    if not sections:
        sections.append({
            "index": 0,
            "title": "Content",
            "content": markdown.strip(),
            "word_count": len(markdown.split()),
        })

    return sections


def chunk_context(snippets: list[str], max_words: int = 2000) -> list[dict]:
    """Group research context snippets into chunks of approximately max_words.

    Returns list of dicts: {"index": int, "content": str, "word_count": int}
    """
    if not snippets:
        return []

    chunks = []
    current_content = []
    current_words = 0

    for snippet in snippets:
        snippet_words = len(snippet.split())
        if current_words + snippet_words > max_words and current_content:
            content = "\n\n---\n\n".join(current_content)
            chunks.append({
                "index": len(chunks),
                "content": content,
                "word_count": current_words,
            })
            current_content = []
            current_words = 0
        current_content.append(snippet)
        current_words += snippet_words

    if current_content:
        content = "\n\n---\n\n".join(current_content)
        chunks.append({
            "index": len(chunks),
            "content": content,
            "word_count": current_words,
        })

    return chunks 