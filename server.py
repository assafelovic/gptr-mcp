"""
GPT Researcher MCP Server

This script implements an MCP server for GPT Researcher, allowing AI assistants
to conduct web research and generate reports via the MCP protocol.
"""

import os
import sys
import uuid
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from fastmcp import FastMCP
from gpt_researcher import GPTResearcher

# Load environment variables
load_dotenv()

from utils import (
    research_store,
    create_success_response, 
    handle_exception,
    get_researcher_by_id, 
    format_sources_for_response,
    format_context_with_sources, 
    store_research_results,
    create_research_prompt
)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(levelname)s] - %(message)s',
)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    name="GPT Researcher"
)

# Initialize researchers dictionary
if not hasattr(mcp, "researchers"):
    mcp.researchers = {}


@mcp.resource("research://{topic}")
async def research_resource(topic: str) -> str:
    """
    Provide research context for a given topic directly as a resource.
    
    This allows LLMs to access web-sourced information without explicit function calls.
    
    Args:
        topic: The research topic or query
        
    Returns:
        String containing the research context with source information
    """
    # Check if we've already researched this topic
    if topic in research_store:
        logger.info(f"Returning cached research for topic: {topic}")
        return research_store[topic]["context"]
    
    # If not, conduct the research
    logger.info(f"Conducting new research for resource on topic: {topic}")
    
    # Initialize GPT Researcher
    researcher = GPTResearcher(topic)
    
    try:
        # Conduct the research
        await researcher.conduct_research()
        
        # Get the context and sources
        context = researcher.get_research_context()
        sources = researcher.get_research_sources()
        source_urls = researcher.get_source_urls()
        
        # Format with sources included
        formatted_context = format_context_with_sources(topic, context, sources)
        
        # Store for future use
        store_research_results(topic, context, sources, source_urls, formatted_context)
        
        return formatted_context
    except Exception as e:
        return f"Error conducting research on '{topic}': {str(e)}"


# --- research mode resolution ---------------------------------------------------------------
_REPORT_TYPES = {"research_report", "detailed_report", "deep", "outline_report", "resource_report",
                 "subtopic_report", "custom_report"}
_REPORT_SOURCES = {"web", "local", "hybrid"}


def _resolve_research_mode(report_type: str, tone: str, report_source: str) -> Dict[str, Any]:
    """Map loosely typed agent inputs onto GPT Researcher's enums; fall back to defaults and say so."""
    notes = []
    rt = (report_type or "research_report").strip().lower()
    if rt not in _REPORT_TYPES:
        notes.append(f"unknown report_type '{report_type}', used research_report")
        rt = "research_report"
    rs = (report_source or "web").strip().lower()
    if rs not in _REPORT_SOURCES:
        notes.append(f"unknown report_source '{report_source}', used web")
        rs = "web"
    tone_value = None
    try:
        from gpt_researcher.utils.enum import Tone  # type: ignore
        wanted = (tone or "objective").strip().lower()
        for member in Tone:
            if member.name.lower() == wanted or str(member.value).split(" ")[0].lower() == wanted:
                tone_value = member
                break
        if tone_value is None:
            notes.append(f"unknown tone '{tone}', used objective")
            tone_value = Tone.Objective
    except Exception as exc:  # pragma: no cover - library layout changed
        notes.append(f"tone unavailable ({exc}); library default used")
        tone_value = None
    return {
        "report_type": rt,
        "report_source": rs,
        "tone": tone_value,
        "echo": {"report_type": rt, "report_source": rs,
                 "tone": getattr(tone_value, "name", "default").lower(), "notes": notes},
    }


@mcp.tool()
async def deep_research(
    query: str,
    report_type: str = "research_report",
    tone: str = "objective",
    report_source: str = "web",
) -> Dict[str, Any]:
    """
    Conduct web research on a given query using GPT Researcher, in any of its modes.
    Use this tool when you need time-sensitive, real-time information like stock prices, news, people, specific knowledge, etc.

    Args:
        query: The research query or topic. Put scope, time window and exclusions in here.
        report_type: research_report (default, ~1-3 min), detailed_report (longer, subtopics),
            deep (recursive multi-level deep research, slowest and most expensive),
            outline_report, resource_report, subtopic_report, custom_report.
        tone: objective (default), formal, analytical, informative, persuasive, explanatory,
            descriptive, critical, comparative, speculative, reflective, narrative, humorous,
            optimistic, pessimistic.
        report_source: web (default), local, hybrid.

    Returns:
        Dict containing research status, ID, and the actual research context and sources
        that can be used directly by LLMs for context enrichment
    """
    logger.info(f"Conducting research on query: {query}...")
    
    # Generate a unique ID for this research session
    research_id = str(uuid.uuid4())
    
    # Initialize GPT Researcher with validated mode arguments. Everything GPTResearcher
    # supports (report_type incl. "deep", tone, report_source) is reachable from the tool.
    mode = _resolve_research_mode(report_type, tone, report_source)
    researcher = GPTResearcher(
        query=query,
        report_type=mode["report_type"],
        report_source=mode["report_source"],
        tone=mode["tone"],
    )

    # Start research
    try:
        await researcher.conduct_research()
        mcp.researchers[research_id] = researcher
        logger.info(f"Research completed for ID: {research_id}")
        
        # Get the research context and sources
        context = researcher.get_research_context()
        sources = researcher.get_research_sources()
        source_urls = researcher.get_source_urls()
        
        # Store in the research store for the resource API
        store_research_results(query, context, sources, source_urls)
        
        return create_success_response({
            "research_id": research_id,
            "query": query,
            "mode": mode["echo"],
            "source_count": len(sources),
            "context": context,
            "sources": format_sources_for_response(sources),
            "source_urls": source_urls
        })
    except Exception as e:
        return handle_exception(e, "Research")


@mcp.tool()
async def quick_search(query: str) -> Dict[str, Any]:
    """
    Perform a quick web search on a given query and return search results with snippets.
    This optimizes for speed over quality and is useful when an LLM doesn't need in-depth
    information on a topic.
    
    Args:
        query: The search query
        
    Returns:
        Dict containing search results and snippets
    """
    logger.info(f"Performing quick search on query: {query}...")
    
    # Generate a unique ID for this search session
    search_id = str(uuid.uuid4())
    
    # Initialize GPT Researcher
    researcher = GPTResearcher(query)
    
    try:
        # Perform quick search
        search_results = await researcher.quick_search(query=query)
        mcp.researchers[search_id] = researcher
        logger.info(f"Quick search completed for ID: {search_id}")
        
        return create_success_response({
            "search_id": search_id,
            "query": query,
            "result_count": len(search_results) if search_results else 0,
            "search_results": search_results
        })
    except Exception as e:
        return handle_exception(e, "Quick search")


@mcp.tool()
async def write_report(research_id: str, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a report based on previously conducted research.
    
    Args:
        research_id: The ID of the research session from deep_research
        custom_prompt: Optional custom prompt for report generation
        
    Returns:
        Dict containing the report content and metadata
    """
    success, researcher, error = get_researcher_by_id(mcp.researchers, research_id)
    if not success:
        return error
    
    logger.info(f"Generating report for research ID: {research_id}")
    
    try:
        # Generate report
        report = await researcher.write_report(custom_prompt=custom_prompt)
        
        # Get additional information
        sources = researcher.get_research_sources()
        costs = researcher.get_costs()
        
        return create_success_response({
            "report": report,
            "source_count": len(sources),
            "costs": costs
        })
    except Exception as e:
        return handle_exception(e, "Report generation")


@mcp.tool()
async def get_research_sources(research_id: str) -> Dict[str, Any]:
    """
    Get the sources used in the research.
    
    Args:
        research_id: The ID of the research session
        
    Returns:
        Dict containing the research sources
    """
    success, researcher, error = get_researcher_by_id(mcp.researchers, research_id)
    if not success:
        return error
    
    sources = researcher.get_research_sources()
    source_urls = researcher.get_source_urls()
    
    return create_success_response({
        "sources": format_sources_for_response(sources),
        "source_urls": source_urls
    })


@mcp.tool()
async def get_research_context(research_id: str) -> Dict[str, Any]:
    """
    Get the full context of the research.
    
    Args:
        research_id: The ID of the research session
        
    Returns:
        Dict containing the research context
    """
    success, researcher, error = get_researcher_by_id(mcp.researchers, research_id)
    if not success:
        return error
    
    context = researcher.get_research_context()
    
    return create_success_response({
        "context": context
    })


@mcp.prompt()
def research_query(topic: str, goal: str, report_format: str = "research_report") -> str:
    """
    Create a research query prompt for GPT Researcher.
    
    Args:
        topic: The topic to research
        goal: The goal or specific question to answer
        report_format: The format of the report to generate
        
    Returns:
        A formatted prompt for research
    """
    return create_research_prompt(topic, goal, report_format)

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "healthy", "service": "mcp-server"})

def run_server():
    """Run the MCP server using FastMCP's built-in event loop handling."""
    # Check if API keys are set
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY not found. Please set it in your .env file.")
        return

    # Determine transport based on environment
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    
    # Auto-detect Docker environment
    if os.getenv("MCP_TRANSPORT") is None and (os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER")):
        transport = "sse"
        logger.info("Docker environment detected, using SSE transport")
    
    # Add startup message
    logger.info(f"Starting GPT Researcher MCP Server with {transport} transport...")
    print(f"🚀 GPT Researcher MCP Server starting with {transport} transport...")
    print("   Check researcher_mcp_server.log for details")

    # Let FastMCP handle the event loop
    try:
        if transport == "stdio":
            logger.info("Using STDIO transport (Claude Desktop compatible)")
            mcp.run(transport="stdio")
        elif transport == "sse":
            mcp.run(transport="sse", host="0.0.0.0", port=8000)
        elif transport == "streamable-http":
            mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
        else:
            raise ValueError(f"Unsupported transport: {transport}")
            
        # Note: If we reach here, the server has stopped
        logger.info("MCP Server is running...")
        while True:
            pass  # Keep the process alive
    except Exception as e:
        logger.error(f"Error running MCP server: {str(e)}")
        print(f"❌ MCP Server error: {str(e)}")
        return
        
    print("✅ MCP Server stopped")


if __name__ == "__main__":
    # Use the non-async approach to avoid asyncio nesting issues
    run_server()
