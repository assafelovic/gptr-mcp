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
    create_research_prompt,
    parse_report_sections,
    chunk_context,
)
from presets import (
    apply_preset,
    validate_output_type,
    is_paginated_type,
    is_raw_context,
    VALID_OUTPUT_TYPES,
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

if not hasattr(mcp, "reports"):
    mcp.reports = {}


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


@mcp.tool()
async def deep_research(
    query: str,
    output_type: str = "briefing",
    breadth: int = 4,
    depth: int = 2,
    concurrency: int = 4,
) -> Dict[str, Any]:
    """
    Conduct deep recursive web research and return results in the requested format.

    Choose output_type based on your needs:
    - "summary" (~300-500 tokens): Bullet-point key facts. Use for factual lookups.
    - "briefing" (~800-1500 tokens): Executive synthesis. Default, good for most queries.
    - "report" (~2000-4000 tokens, paginated): Full structured report. Use when user asks for analysis.
    - "deep_report" (~4000-8000 tokens, paginated): Comprehensive report. Use for "write me a detailed report".
    - "raw_context" (variable, paginated): Raw research snippets. Use when you want to reason over sources yourself.

    For paginated types (report, deep_report, raw_context), you receive a table_of_contents
    and the first section. Use get_report_section(research_id, section) to fetch more sections.

    Args:
        query: The research query or topic
        output_type: Output format — summary, briefing, report, deep_report, or raw_context
        breadth: Number of search queries per research level (default 4)
        depth: Number of recursive research levels (default 2)
        concurrency: Max concurrent research tasks (default 4)
    """
    try:
        validate_output_type(output_type)
    except ValueError as e:
        return {"status": "error", "message": str(e)}

    logger.info(f"Deep research: query={query!r}, output_type={output_type}, breadth={breadth}, depth={depth}")

    os.environ["DEEP_RESEARCH_BREADTH"] = str(breadth)
    os.environ["DEEP_RESEARCH_DEPTH"] = str(depth)
    os.environ["DEEP_RESEARCH_CONCURRENCY"] = str(concurrency)

    saved_scraper = os.environ.get("SCRAPER")
    os.environ["SCRAPER"] = "bs"

    research_id = str(uuid.uuid4())
    researcher = GPTResearcher(query, report_type="deep")

    try:
        await researcher.conduct_research()
        mcp.researchers[research_id] = researcher
        logger.info(f"Research completed: {research_id}")

        context = researcher.get_research_context()
        sources = researcher.get_research_sources()
        source_urls = researcher.get_source_urls()
        store_research_results(query, context, sources, source_urls)
        formatted_sources = format_sources_for_response(sources)

        # Raw context: skip report generation, paginate context directly
        if is_raw_context(output_type):
            snippets = context if isinstance(context, list) else [context]
            chunks = chunk_context(snippets)
            mcp.reports[research_id] = {
                "chunks": chunks,
                "output_type": "raw_context",
                "total_word_count": sum(c["word_count"] for c in chunks),
            }
            return create_success_response({
                "research_id": research_id,
                "output_type": "raw_context",
                "context_chunks": len(chunks),
                "total_word_count": mcp.reports[research_id]["total_word_count"],
                "first_chunk": chunks[0]["content"] if chunks else "",
                "source_count": len(sources),
                "sources": formatted_sources,
            })

        # Generate report with preset
        custom_prompt = apply_preset(output_type)
        report = await researcher.write_report(custom_prompt=custom_prompt or "")

        # Compact types: return full report inline
        if not is_paginated_type(output_type):
            return create_success_response({
                "research_id": research_id,
                "output_type": output_type,
                "report": report,
                "source_count": len(sources),
                "sources": formatted_sources,
                "has_full_report": False,
            })

        # Paginated types: split into sections, return TOC + first section
        sections = parse_report_sections(report)
        mcp.reports[research_id] = {
            "sections": sections,
            "output_type": output_type,
            "total_word_count": sum(s["word_count"] for s in sections),
            "raw_markdown": report,
        }
        toc = [{"index": s["index"], "title": s["title"], "word_count": s["word_count"]} for s in sections]

        return create_success_response({
            "research_id": research_id,
            "output_type": output_type,
            "table_of_contents": toc,
            "total_word_count": mcp.reports[research_id]["total_word_count"],
            "first_section": sections[0]["content"] if sections else "",
            "source_count": len(sources),
        })
    except Exception as e:
        return handle_exception(e, "Research")
    finally:
        if saved_scraper is not None:
            os.environ["SCRAPER"] = saved_scraper
        else:
            os.environ.pop("SCRAPER", None)


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
async def write_report(
    research_id: str,
    output_type: str = "report",
    custom_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a report from an existing research session in the requested format.
    Reuses already-gathered research data — no new web searches.

    Useful workflow: get a "summary" first from deep_research, then call
    write_report with "report" for full analysis if needed.

    If custom_prompt is provided, it overrides the output_type preset.

    Args:
        research_id: The ID from deep_research or quick_search
        output_type: Output format — summary, briefing, report, deep_report, raw_context
        custom_prompt: Optional custom prompt (overrides output_type preset)
    """
    success, researcher, error = get_researcher_by_id(mcp.researchers, research_id)
    if not success:
        return error

    try:
        validate_output_type(output_type)
    except ValueError as e:
        return {"status": "error", "message": str(e)}

    logger.info(f"Writing report: research_id={research_id}, output_type={output_type}")

    # Raw context: return paginated context, no LLM generation
    if is_raw_context(output_type):
        context = researcher.get_research_context()
        snippets = context if isinstance(context, list) else [context]
        chunks = chunk_context(snippets)
        mcp.reports[research_id] = {
            "chunks": chunks,
            "output_type": "raw_context",
            "total_word_count": sum(c["word_count"] for c in chunks),
        }
        return create_success_response({
            "research_id": research_id,
            "output_type": "raw_context",
            "context_chunks": len(chunks),
            "total_word_count": mcp.reports[research_id]["total_word_count"],
            "first_chunk": chunks[0]["content"] if chunks else "",
        })

    try:
        # custom_prompt overrides preset
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = apply_preset(output_type)

        report = await researcher.write_report(custom_prompt=prompt or "")
        sources = researcher.get_research_sources()
        costs = researcher.get_costs()

        # Compact types: return full report
        if not is_paginated_type(output_type):
            return create_success_response({
                "research_id": research_id,
                "output_type": output_type,
                "report": report,
                "source_count": len(sources),
                "costs": costs,
            })

        # Paginated types: split and return TOC + first section
        sections = parse_report_sections(report)
        mcp.reports[research_id] = {
            "sections": sections,
            "output_type": output_type,
            "total_word_count": sum(s["word_count"] for s in sections),
            "raw_markdown": report,
        }
        toc = [{"index": s["index"], "title": s["title"], "word_count": s["word_count"]} for s in sections]

        return create_success_response({
            "research_id": research_id,
            "output_type": output_type,
            "table_of_contents": toc,
            "total_word_count": mcp.reports[research_id]["total_word_count"],
            "first_section": sections[0]["content"] if sections else "",
            "source_count": len(sources),
            "costs": costs,
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
    if os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER"):
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
