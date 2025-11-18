# CLAUDE.md - GPT Researcher MCP Server

## Project Overview

**GPT Researcher MCP Server** is a Model Context Protocol (MCP) server implementation that provides AI assistants with deep web research capabilities. Unlike standard web search tools that return raw results, this server uses GPT Researcher to autonomously explore, validate, and synthesize information from multiple sources, delivering high-quality, relevant, and up-to-date research results.

### Key Capabilities
- **Deep Research**: Comprehensive multi-source research with validation
- **Quick Search**: Fast web search for time-sensitive queries
- **Report Generation**: Automated report writing from research results
- **Resource Access**: MCP resource API for direct topic information access
- **Multiple Transports**: STDIO (Claude Desktop), SSE (Docker/Web), HTTP

### Technology Stack
- **Language**: Python 3.11+
- **MCP Framework**: FastMCP (>=2.8.0)
- **Research Engine**: GPT Researcher (>=0.14.0)
- **Web Framework**: FastAPI + Uvicorn
- **Dependencies**: OpenAI, Tavily, loguru, python-dotenv

---

## Repository Structure

```
gptr-mcp/
├── server.py              # Main MCP server implementation
├── utils.py               # Utility functions and helpers
├── __init__.py            # Package initialization
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── Dockerfile            # Docker containerization
├── docker-compose.yml    # Docker orchestration
├── run.sh               # Setup and run script
├── tests/
│   └── test_mcp_server.py  # Integration tests
├── README.md            # User-facing documentation
└── CLAUDE.md            # This file - AI assistant guide
```

---

## Core Components

### 1. server.py

**Purpose**: Main MCP server implementation with FastMCP

**Key Responsibilities**:
- MCP protocol setup and initialization
- Tool definitions (deep_research, quick_search, write_report, etc.)
- Resource endpoint (research://{topic})
- Prompt templates (research_query)
- Transport detection and server startup
- Researcher instance management

**Architecture Pattern**:
```python
# FastMCP initialization
mcp = FastMCP(name="GPT Researcher")

# Tools are defined as async functions with @mcp.tool() decorator
@mcp.tool()
async def deep_research(query: str) -> Dict[str, Any]:
    # Implementation
    pass

# Resources use @mcp.resource() with URI patterns
@mcp.resource("research://{topic}")
async def research_resource(topic: str) -> str:
    # Implementation
    pass

# Prompts use @mcp.prompt()
@mcp.prompt()
def research_query(topic: str, goal: str) -> str:
    # Implementation
    pass
```

**Important Functions**:
- `run_server()`: Entry point - handles transport detection and server startup
- `deep_research()`: Primary research tool - conducts thorough web research
- `quick_search()`: Fast search tool - optimized for speed over depth
- `write_report()`: Report generation from research results
- `get_research_sources()`: Retrieves sources from completed research
- `get_research_context()`: Retrieves full context from research
- `research_resource()`: MCP resource for direct topic access

**State Management**:
- `mcp.researchers`: Dictionary storing researcher instances by ID
- Research IDs are UUIDs generated for each research session
- Researchers persist for the lifetime of the server process

### 2. utils.py

**Purpose**: Shared utilities and helper functions

**Key Functions**:
- `create_error_response()`: Standardized error responses
- `create_success_response()`: Standardized success responses
- `handle_exception()`: Consistent exception handling
- `get_researcher_by_id()`: Retrieve researcher instances safely
- `format_sources_for_response()`: Format source data for API responses
- `format_context_with_sources()`: Format research context with citations
- `store_research_results()`: Cache research results in research_store
- `create_research_prompt()`: Generate research prompt templates

**Global State**:
- `research_store`: Dictionary caching research results by topic
  - Used by the resource API to avoid redundant research
  - Stores: context, sources, source_urls

### 3. tests/test_mcp_server.py

**Purpose**: Integration testing for MCP server functionality

**Test Coverage**:
- SSE connection establishment
- Session ID acquisition
- MCP protocol initialization
- Tool discovery (tools/list)
- Tool execution (quick_search)

**Usage**: `python tests/test_mcp_server.py`

---

## Development Workflow

### Initial Setup

1. **Clone and Install**:
```bash
git clone https://github.com/assafelovic/gptr-mcp.git
cd gptr-mcp
pip install -r requirements.txt
```

2. **Configure Environment**:
```bash
cp .env.example .env
# Edit .env and add your API keys:
# - OPENAI_API_KEY (required)
# - TAVILY_API_KEY (required)
```

3. **Verify Installation**:
```bash
python server.py  # Should start with STDIO transport
```

### Environment Variables

**Required**:
- `OPENAI_API_KEY`: OpenAI API key for LLM operations
- `TAVILY_API_KEY`: Tavily API key for web search

**Optional Configuration**:
- `MCP_TRANSPORT`: Force transport mode (stdio|sse|streamable-http)
- `DOCKER_CONTAINER`: Set to "true" to force Docker mode
- `EMBEDDING`: Embedding model (default: openai:text-embedding-3-small)
- `STRATEGIC_LLM`: LLM for research (default: openai:gpt-4o-mini)
- `MAX_ITERATIONS`: Research iterations (default: 2)
- `LOG_LEVEL`: Logging level (default: INFO)
- `PORT`: Server port (default: 8000)

### Running the Server

**Local Development** (STDIO - for Claude Desktop):
```bash
python server.py
```

**Docker** (SSE transport):
```bash
docker-compose up -d
```

**Manual Transport Selection**:
```bash
export MCP_TRANSPORT=sse
python server.py
```

### Testing

**Run Integration Tests**:
```bash
# Start server first
docker-compose up -d

# Run tests
python tests/test_mcp_server.py
```

**Manual Testing with curl**:
```bash
# Get session ID
curl http://localhost:8000/sse

# Initialize MCP
curl -X POST "http://localhost:8000/messages/?session_id=YOUR_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'

# Call a tool
curl -X POST "http://localhost:8000/messages/?session_id=YOUR_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"quick_search","arguments":{"query":"AI news"}}}'
```

---

## Code Conventions

### Python Style
- **Python Version**: 3.11+ (required by gpt-researcher >=0.14.0)
- **Async/Await**: All tools and resources are async functions
- **Type Hints**: Use type hints for function parameters and return values
- **Error Handling**: Use try/except with `handle_exception()` utility
- **Logging**: Use the `logging` module, configured in server.py

### Response Format

**Success Response**:
```python
{
    "status": "success",
    "research_id": "uuid",
    "query": "original query",
    "source_count": 5,
    "context": "research context...",
    "sources": [...],
    "source_urls": [...]
}
```

**Error Response**:
```python
{
    "status": "error",
    "message": "error description"
}
```

### Naming Conventions
- **Functions**: snake_case (e.g., `deep_research`, `get_research_sources`)
- **Variables**: snake_case (e.g., `research_id`, `source_urls`)
- **Constants**: UPPER_CASE (e.g., `MAX_ITERATIONS`)
- **Classes**: PascalCase (e.g., `MCPServerTester`)

### Documentation
- **Docstrings**: All public functions have docstrings explaining:
  - Purpose
  - Args with types
  - Returns with types
  - Usage examples (when helpful)

---

## MCP Protocol Implementation

### Protocol Overview

This server implements the **Model Context Protocol (MCP)** specification version 2024-11-05. MCP is a standardized protocol for AI assistants to access external context and tools.

### MCP Components

**1. Tools** - Executable functions that AI can call:
- `deep_research`: Comprehensive research
- `quick_search`: Fast web search
- `write_report`: Report generation
- `get_research_sources`: Retrieve sources
- `get_research_context`: Retrieve context

**2. Resources** - Readable data sources:
- `research://{topic}`: Direct access to research on a topic

**3. Prompts** - Reusable prompt templates:
- `research_query`: Template for research queries

### Tool Definition Pattern

```python
@mcp.tool()
async def tool_name(param1: str, param2: Optional[str] = None) -> Dict[str, Any]:
    """
    Tool description for AI assistant.

    Args:
        param1: Description of param1
        param2: Optional description of param2

    Returns:
        Dict containing response data
    """
    try:
        # Implementation
        result = await some_async_operation(param1, param2)
        return create_success_response({
            "data": result
        })
    except Exception as e:
        return handle_exception(e, "Tool name")
```

### Resource Definition Pattern

```python
@mcp.resource("resource://{variable}")
async def resource_name(variable: str) -> str:
    """
    Resource description.

    Args:
        variable: Path variable from URI

    Returns:
        String containing resource data
    """
    # Check cache first
    if variable in cache:
        return cache[variable]

    # Generate resource data
    data = await generate_data(variable)

    # Cache and return
    cache[variable] = data
    return data
```

---

## Transport Modes

### STDIO Transport (Default)

**Use Case**: Claude Desktop, local MCP clients

**Characteristics**:
- Communicates via stdin/stdout
- No HTTP server required
- Synchronous, blocking communication
- Best for local development

**Detection**:
- Default mode
- When not in Docker environment
- When `MCP_TRANSPORT=stdio`

**Usage**:
```json
// Claude Desktop config
{
  "mcpServers": {
    "gptr-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/server.py"],
      "env": {
        "OPENAI_API_KEY": "key",
        "TAVILY_API_KEY": "key"
      }
    }
  }
}
```

### SSE Transport (Docker)

**Use Case**: Docker deployments, web clients, n8n integration

**Characteristics**:
- HTTP server on 0.0.0.0:8000
- Server-Sent Events for streaming
- Session-based communication
- Requires session ID from /sse endpoint

**Detection**:
- Auto-enabled when `/.dockerenv` exists
- When `DOCKER_CONTAINER=true`
- When `MCP_TRANSPORT=sse`

**Endpoints**:
- `GET /sse` - Get session ID
- `POST /messages/?session_id={id}` - Send MCP messages
- `GET /health` - Health check

**Workflow**:
1. Connect to `/sse` to get session ID
2. Use session ID in all `/messages/` requests
3. Each client needs unique session ID

### Streamable HTTP Transport

**Use Case**: Modern web deployments

**Characteristics**:
- HTTP server on 0.0.0.0:8000
- Streamable responses
- Advanced web client support

**Detection**:
- When `MCP_TRANSPORT=streamable-http`

---

## Key Patterns and Best Practices

### 1. Research ID Management

**Pattern**: Generate UUID for each research session and store researcher instance

```python
research_id = str(uuid.uuid4())
researcher = GPTResearcher(query)
await researcher.conduct_research()
mcp.researchers[research_id] = researcher
```

**Why**: Allows follow-up operations (write_report, get_sources) on the same research

### 2. Dual Return Strategy

**Pattern**: Tools return both structured data AND full context

```python
return create_success_response({
    "research_id": research_id,
    "query": query,
    "source_count": len(sources),
    "context": context,  # Full context for immediate use
    "sources": format_sources_for_response(sources),
    "source_urls": source_urls
})
```

**Why**: AI can use context immediately OR save research_id for later operations

### 3. Resource Caching

**Pattern**: Store research results in `research_store` for resource API

```python
# Check cache first
if topic in research_store:
    return research_store[topic]["context"]

# Conduct research
researcher = GPTResearcher(topic)
await researcher.conduct_research()

# Store for future use
store_research_results(topic, context, sources, source_urls)
```

**Why**: Avoid redundant research for the same topic

### 4. Error Handling

**Pattern**: Consistent error handling with `handle_exception()`

```python
try:
    result = await operation()
    return create_success_response({"data": result})
except Exception as e:
    return handle_exception(e, "Operation name")
```

**Why**: Standardized error responses, proper logging, user-friendly messages

### 5. Transport Auto-Detection

**Pattern**: Detect environment and choose appropriate transport

```python
transport = os.getenv("MCP_TRANSPORT", "stdio").lower()

if os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER"):
    transport = "sse"
```

**Why**: Works seamlessly in different deployment environments

---

## Common Development Tasks

### Adding a New Tool

1. **Define the tool function** in server.py:

```python
@mcp.tool()
async def new_tool(param1: str, param2: Optional[int] = None) -> Dict[str, Any]:
    """
    Description of what this tool does.

    Args:
        param1: Description of param1
        param2: Optional description of param2

    Returns:
        Dict containing the tool results
    """
    logger.info(f"Running new_tool with param1={param1}")

    try:
        # Implementation
        result = await perform_operation(param1, param2)

        return create_success_response({
            "result": result,
            "param1": param1
        })
    except Exception as e:
        return handle_exception(e, "New tool")
```

2. **Add helper functions** (if needed) in utils.py

3. **Test the tool**:
```bash
# Start server
python server.py

# In another terminal, test via MCP client or test script
```

### Adding a New Resource

1. **Define the resource** in server.py:

```python
@mcp.resource("resource_type://{identifier}")
async def resource_name(identifier: str) -> str:
    """
    Description of what this resource provides.

    Args:
        identifier: The resource identifier from URI

    Returns:
        String containing the resource data
    """
    logger.info(f"Accessing resource: {identifier}")

    # Check cache
    cache_key = f"resource_{identifier}"
    if cache_key in research_store:
        return research_store[cache_key]["data"]

    # Generate resource
    data = await generate_resource_data(identifier)

    # Cache and return
    research_store[cache_key] = {"data": data}
    return data
```

2. **Document the resource** in README.md

### Adding a New Prompt Template

1. **Define the prompt** in server.py:

```python
@mcp.prompt()
def prompt_name(topic: str, context: str = "") -> str:
    """
    Description of when to use this prompt.

    Args:
        topic: The main topic
        context: Optional additional context

    Returns:
        A formatted prompt string
    """
    return f"""
    Your prompt template here with {topic} and {context}.

    Instructions for the AI assistant...
    """
```

### Modifying Research Behavior

**Key Configuration Variables** (in .env):
- `MAX_ITERATIONS`: Number of research iterations (default: 2)
- `STRATEGIC_LLM`: LLM model for research (e.g., openai:gpt-4o-mini)
- `EMBEDDING`: Embedding model for similarity search

**Customize Research in Code**:
```python
# In server.py, modify GPTResearcher initialization
researcher = GPTResearcher(
    query=query,
    report_type="research_report",  # or "quick_research", "detailed_report", etc.
    config_path=None  # or path to custom config
)
```

---

## Docker Deployment

### Building the Image

```bash
docker build -t gptr-mcp .
```

### Running with Docker Compose

```bash
# Edit .env first with your API keys
docker-compose up -d
```

### Environment Variables in Docker

Set in docker-compose.yml:
```yaml
environment:
  - MCP_TRANSPORT=sse
  - DOCKER_CONTAINER=true
  - OPENAI_API_KEY=${OPENAI_API_KEY}
  - TAVILY_API_KEY=${TAVILY_API_KEY}
```

### Health Checks

The Docker container includes a health check:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=7s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

### Networking

**For n8n Integration**:
```bash
# Create shared network
docker network create n8n-mcp-net

# Connect gptr-mcp to n8n network
docker network connect n8n-mcp-net gptr-mcp

# In n8n, use: http://gptr-mcp:8000/sse
```

---

## Claude Desktop Integration

### Configuration Location

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Configuration Example

```json
{
  "mcpServers": {
    "gptr-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/gptr-mcp/server.py"],
      "env": {
        "OPENAI_API_KEY": "your-actual-key",
        "TAVILY_API_KEY": "your-actual-key"
      }
    }
  }
}
```

### Important Notes

1. **Use absolute paths** - relative paths won't work
2. **Include env variables** - Claude Desktop doesn't inherit shell environment
3. **Restart Claude** after configuration changes
4. **Secure the config file**: `chmod 600 ~/Library/Application\ Support/Claude/claude_desktop_config.json`

### Alternative: Wrapper Script

Create `run_gptr_mcp.sh`:
```bash
#!/bin/bash
source /path/to/.env
exec python /absolute/path/to/server.py
```

Then use in config:
```json
{
  "mcpServers": {
    "gptr-mcp": {
      "command": "/absolute/path/to/run_gptr_mcp.sh"
    }
  }
}
```

---

## Troubleshooting Guide

### Server Won't Start

**Problem**: OPENAI_API_KEY not found
**Solution**: Ensure .env file exists with valid API keys

**Problem**: Python version error
**Solution**: Verify Python 3.11+ is installed: `python --version`

**Problem**: Module not found
**Solution**: Install dependencies: `pip install -r requirements.txt`

### Claude Desktop Issues

**Problem**: Server not appearing in Claude
**Solution**:
- Check JSON syntax in claude_desktop_config.json
- Use absolute paths
- Restart Claude Desktop completely

**Problem**: Tools not showing
**Solution**:
- Look for 🔧 icon in Claude Desktop
- Verify config file location
- Check server starts successfully: `python server.py`

**Problem**: Permission denied
**Solution**: Make sure Python and server.py are executable

### Docker Issues

**Problem**: Container not accessible
**Solution**:
- Check container is running: `docker ps | grep gptr-mcp`
- Check logs: `docker logs gptr-mcp`
- Verify port 8000 is exposed

**Problem**: n8n can't connect
**Solution**:
- Ensure both on same Docker network
- Use container name as hostname: `http://gptr-mcp:8000/sse`
- Check session ID is being obtained correctly

### Research Issues

**Problem**: Research taking too long
**Solution**: Reduce `MAX_ITERATIONS` in .env (try 2 or 1)

**Problem**: Low-quality results
**Solution**: Increase `MAX_ITERATIONS` or use more powerful `STRATEGIC_LLM`

**Problem**: API rate limits
**Solution**: Add delays between requests or upgrade API tier

---

## Performance Optimization

### Speed vs Quality Trade-offs

**Fast Research** (30 seconds):
```
MAX_ITERATIONS=2
STRATEGIC_LLM=openai:gpt-4o-mini
```

**Deep Research** (60-90 seconds):
```
MAX_ITERATIONS=4
STRATEGIC_LLM=openai:gpt-4o
```

### Caching Strategy

The server caches research results in `research_store`:
- Key: Topic string
- Value: {context, sources, source_urls}
- Lifetime: Server process duration
- Used by: Resource API

To implement persistent caching, modify `utils.py` to use Redis or file system.

### Resource Usage

**Memory**:
- Each researcher instance stores full context
- Clean up old researchers periodically in production

**API Costs**:
- Monitor via `researcher.get_costs()`
- Implement cost tracking and limits if needed

---

## Security Considerations

### API Key Management

1. **Never commit .env** - it's in .gitignore
2. **Use environment variables** in production
3. **Rotate keys regularly**
4. **Limit key permissions** to required scopes

### Claude Desktop Config Security

```bash
# Secure the config file
chmod 600 ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Never commit this file to version control
```

### Docker Security

1. **Don't expose port 8000** publicly without authentication
2. **Use Docker secrets** for API keys in production
3. **Run as non-root user** (consider adding USER in Dockerfile)
4. **Scan image for vulnerabilities**: `docker scan gptr-mcp`

### Input Validation

The server accepts user queries - ensure:
- No command injection in research queries
- Reasonable query length limits
- Rate limiting in production deployments

---

## Advanced Configuration

### Custom GPT Researcher Config

Create a custom config file:
```python
# custom_config.py
from gpt_researcher.config import Config

class CustomConfig(Config):
    MAX_ITERATIONS = 3
    RETRIEVER = "tavily"  # or "bing", "google", etc.
    # ... other settings
```

Use in server.py:
```python
researcher = GPTResearcher(
    query=query,
    config=CustomConfig()
)
```

### Multiple Search Engines

Configure in .env:
```bash
# Primary retriever
RETRIEVER=tavily

# Fallback retrievers
FALLBACK_RETRIEVERS=bing,google

# Engine-specific keys
BING_API_KEY=your_bing_key
GOOGLE_API_KEY=your_google_key
```

### Custom Report Formats

Modify `write_report()` to support custom formats:
```python
@mcp.tool()
async def write_report(
    research_id: str,
    report_format: str = "research_report",
    custom_prompt: Optional[str] = None
) -> Dict[str, Any]:
    # Implementation with format support
```

---

## Monitoring and Logging

### Log Locations

**STDIO Mode**: stderr
**Docker Mode**: Container logs via `docker logs gptr-mcp`
**File Logs**: Not enabled by default (can add to utils.py)

### Log Levels

Set in .env:
```bash
LOG_LEVEL=DEBUG  # or INFO, WARNING, ERROR
```

### Adding Structured Logging

Modify utils.py to add structured logging:
```python
from loguru import logger
import json

logger.configure(handlers=[{
    "sink": sys.stderr,
    "serialize": True  # JSON output
}])
```

### Monitoring Metrics

Key metrics to track:
- Research duration: Time between tool call and response
- API costs: Via `researcher.get_costs()`
- Error rates: Count of handle_exception() calls
- Cache hit rate: research_store hits vs misses

---

## Contributing Guidelines

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to all public functions
- Keep functions focused and small
- Use meaningful variable names

### Testing

Before submitting changes:
1. Test with STDIO transport (Claude Desktop)
2. Test with SSE transport (Docker)
3. Run integration tests: `python tests/test_mcp_server.py`
4. Verify all tools work correctly

### Documentation

Update when making changes:
- This CLAUDE.md file for architecture changes
- README.md for user-facing features
- Docstrings for function changes
- .env.example for new environment variables

### Git Workflow

1. Create feature branch from main
2. Make changes with clear commit messages
3. Test thoroughly
4. Submit pull request with description

---

## References and Resources

### MCP Protocol
- [MCP Specification](https://modelcontextprotocol.io/docs/specification)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Anthropic MCP Docs](https://docs.anthropic.com/claude/docs/model-context-protocol)

### GPT Researcher
- [GPT Researcher Docs](https://docs.gptr.dev)
- [GPT Researcher GitHub](https://github.com/assafelovic/gpt-researcher)
- [Search Engines Guide](https://docs.gptr.dev/docs/gpt-researcher/search-engines)

### Claude Desktop
- [Claude Desktop Integration](https://docs.gptr.dev/docs/gpt-researcher/mcp-server/claude-integration)
- [Claude Desktop Config Reference](https://docs.anthropic.com/claude/docs/claude-desktop)

---

## Quick Reference

### File Map
- `server.py:line_number` - Main server code
- `utils.py:line_number` - Helper functions
- `tests/test_mcp_server.py:line_number` - Tests

### Key Functions
- `run_server()` - server.py:277 - Server entry point
- `deep_research()` - server.py:94 - Primary research tool
- `quick_search()` - server.py:141 - Fast search tool
- `research_resource()` - server.py:50 - Resource endpoint
- `create_success_response()` - utils.py:23 - Response formatter
- `handle_exception()` - utils.py:28 - Error handler

### Common Commands
```bash
# Start local server
python server.py

# Start with Docker
docker-compose up -d

# Run tests
python tests/test_mcp_server.py

# Check logs
docker logs gptr-mcp

# Health check
curl http://localhost:8000/health
```

---

## Version History

**Current Version**: Based on gpt-researcher >=0.14.0, fastmcp >=2.8.0

**Python Requirement**: 3.11+ (due to gpt-researcher dependency)

**Breaking Changes**:
- v0.12.16+: Python 3.11 required (was 3.10)
- v2.8.0+: FastMCP API changes

---

*This document is maintained for AI assistants working with the GPT Researcher MCP Server codebase. For user-facing documentation, see README.md.*
