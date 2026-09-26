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
from fastmcp import Context, FastMCP
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
    create_research_prompt,
    ProgressLogHandler,
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


def _make_researcher(query: str, ctx: Context) -> GPTResearcher:
    """Build a GPTResearcher with MCP progress reporting wired for both of
    gpt_researcher's independent signal paths -- see ProgressLogHandler's
    docstring for why both log_handler= and websocket= are required. Both
    tools pass the same handler instance so the two paths share one
    monotonic progress counter instead of each emitting its own,
    interleaved and out of order.

    Note: only deep_research's conduct_research() actually exercises the
    websocket path -- quick_search's retriever path
    (gpt_researcher.actions.query_processing.get_search_results) never
    calls stream_output, so websocket= is inert during quick_search()
    itself. It's still wired here, for uniformity and so it works for free
    if that path ever grows streaming, and because the researcher this
    returns can later be reused by the standalone write_report tool (see
    _release_progress_websocket).
    """
    handler = ProgressLogHandler(ctx)
    return GPTResearcher(query, log_handler=handler, websocket=handler)


def _release_progress_websocket(researcher: GPTResearcher) -> None:
    """Clear `websocket` once conduct_research()/quick_search() is done,
    before the researcher is stored in mcp.researchers for reuse by a
    later call.

    A non-None `websocket` makes gpt_researcher's report-writing LLM call
    disable its normal 10-attempt retry budget (stream=True and websocket
    is not None -> 1 attempt instead of 10; see utils/llm.py) and
    re-stream the entire generated report back through it, paragraph by
    paragraph, as if it were progress -- neither wanted for report
    generation, only for search-loop progress.

    Must run before storage, not just before an inline write_report()
    call: deep_research(synthesize_report=False) and quick_search() both
    store their researcher in mcp.researchers, and the standalone
    write_report tool reuses it later via research_id/search_id -- that
    reuse needs the same clearing, or it hits the same regression.

    Depends on a companion fix in the gpt-researcher fork:
    ReportGenerator.write_report() must read researcher.websocket live at
    call time, not the value gpt_researcher/skills/writer.py currently
    freezes into research_params at GPTResearcher construction. Until that
    fix is installed, this clear does silence a few verbose progress
    messages gpt_researcher's write_report() reads live elsewhere (e.g.
    the "writing_report" ping), but the retry-budget and re-streaming
    problems above are not yet actually fixed -- see
    test_installed_gpt_researcher_reads_websocket_live_at_report_time.
    """
    researcher.websocket = None


@mcp.tool()
async def deep_research(
    query: str, ctx: Context, synthesize_report: bool = True
) -> Dict[str, Any]:
    """
    Conduct a web deep research on a given query using GPT Researcher.
    Use this tool when you need time-sensitive, real-time information like stock prices, news, people, specific knowledge, etc.

    Args:
        query: The research query or topic
        synthesize_report: If True (default), also synthesize and return a
            written report alongside the raw context. Set False to skip
            synthesis and get gather-only results faster/cheaper -- the
            write_report tool can still be called later with the returned
            research_id.

    Returns:
        Dict containing research status, ID, the actual research context and
        sources (for direct LLM context enrichment), and -- unless
        synthesize_report is False -- a synthesized "report".
    """
    logger.info(f"Conducting research on query: {query}...")

    # Generate a unique ID for this research session
    research_id = str(uuid.uuid4())

    researcher = _make_researcher(query, ctx)

    # Start research
    try:
        await researcher.conduct_research()
        _release_progress_websocket(researcher)
        mcp.researchers[research_id] = researcher
        logger.info(f"Research completed for ID: {research_id}")

        # Get the research context and sources
        context = researcher.get_research_context()
        sources = researcher.get_research_sources()
        source_urls = researcher.get_source_urls()

        # Store in the research store for the resource API
        store_research_results(query, context, sources, source_urls)

        response_data = {
            "research_id": research_id,
            "query": query,
            "source_count": len(sources),
            "context": context,
            "sources": format_sources_for_response(sources),
            "source_urls": source_urls
        }

        if synthesize_report:
            logger.info(f"Synthesizing report for research ID: {research_id}")
            response_data["report"] = await researcher.write_report()

        return create_success_response(response_data)
    except Exception as e:
        return handle_exception(e, "Research")


@mcp.tool()
async def quick_search(query: str, ctx: Context) -> Dict[str, Any]:
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

    researcher = _make_researcher(query, ctx)

    try:
        # Perform quick search
        search_results = await researcher.quick_search(query=query)
        _release_progress_websocket(researcher)
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

    # An explicit MCP_TRANSPORT always wins; Docker auto-detection only
    # supplies a default when it's unset (or blank).
    transport = (os.getenv("MCP_TRANSPORT") or "").strip().lower()
    if not transport:
        in_docker = os.path.exists("/.dockerenv") or bool(os.getenv("DOCKER_CONTAINER"))
        transport = "sse" if in_docker else "stdio"
        logger.info(f"MCP_TRANSPORT unset, defaulting to {transport} transport")

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
