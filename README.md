[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/assafelovic-gptr-mcp-badge.png)](https://mseep.ai/app/assafelovic-gptr-mcp)

<div align="center" id="top">

<img src="https://github.com/assafelovic/gpt-researcher/assets/13554167/20af8286-b386-44a5-9a83-3be1365139c3" alt="Logo" width="80">

# 🔍 GPT Researcher MCP Server

[![Website](https://img.shields.io/badge/Official%20Website-gptr.dev-teal?style=for-the-badge&logo=world&logoColor=white&color=0891b2)](https://gptr.dev)
[![Documentation](https://img.shields.io/badge/Documentation-DOCS-f472b6?logo=googledocs&logoColor=white&style=for-the-badge)](https://docs.gptr.dev/docs/gpt-researcher/mcp-server/getting-started)
[![Discord Follow](https://dcbadge.vercel.app/api/server/QgZXvJAccX?style=for-the-badge&theme=clean-inverted&?compact=true)](https://discord.gg/QgZXvJAccX)

</div>

## Why GPT Researcher MCP?

While LLM apps can access web search tools with MCP, **GPT Researcher MCP delivers deep research results.** Standard search tools return raw results requiring manual filtering, often containing irrelevant sources and wasting context window space.

GPT Researcher autonomously explores and validates numerous sources, focusing only on relevant, trusted and up-to-date information. Though slightly slower than standard search (~30 seconds wait), it delivers:

- ✨ Higher quality information
- 📊 Optimized context usage
- 🔎 Comprehensive results
- 🧠 Better reasoning for LLMs

## 💻 Claude Desktop Demo
https://github.com/user-attachments/assets/ef97eea5-a409-42b9-8f6d-b82ab16c52a8

## 🚀 Quick Start with Claude Desktop

**Want to use this with Claude Desktop right away?** Here's the fastest path:

1. **Install dependencies:**
   ```bash
   git clone https://github.com/assafelovic/gptr-mcp.git
   pip install -r requirements.txt
   ```

2. **Set up your Claude Desktop config** at `~/Library/Application Support/Claude/claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "gptr-mcp": {
         "command": "python",
         "args": ["/absolute/path/to/gpt-researcher/gptr-mcp/server.py"],
         "env": {
           "OPENAI_API_KEY": "your-openai-key-here",
           "TAVILY_API_KEY": "your-tavily-key-here"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop** and start researching! 🎉

For detailed setup instructions, see the [full Claude Desktop Integration section](#-claude-desktop-integration) below.

### Resources
- `research_resource`: Get web resources related to a given task via research.

### Primary Tools

- `deep_research`: Performs deep web research on a topic, finding the most reliable and relevant information
- `quick_search`: Performs a fast web search optimized for speed over quality, returning search results with snippets. Supports any GPTR supported web retriever such as Tavily, Bing, Google, etc... Learn more [here](https://docs.gptr.dev/docs/gpt-researcher/search-engines)
- `write_report`: Generate a report based on research results
- `get_research_sources`: Get the sources used in the research
- `get_research_context`: Get the full context of the research

### Prompts

- `research_query`: Create a research query prompt

## Prerequisites

Before running the MCP server, make sure you have:

1. Python 3.11 or higher installed
   - **Important**: GPT Researcher >=0.12.16 requires Python 3.11+
2. API keys for the services you plan to use:
   - [OpenAI API key](https://platform.openai.com/api-keys)
   - [Tavily API key](https://app.tavily.com)

You can also connect any other web search engines or MCP using GPTR supported retrievers. Check out the [docs here](https://docs.gptr.dev/docs/gpt-researcher/search-engines)

## ⚙️ Installation

1. Clone the GPT Researcher repository:
```bash
git clone https://github.com/assafelovic/gpt-researcher.git
cd gpt-researcher
```

2. Install the gptr-mcp dependencies:
```bash
cd gptr-mcp
pip install -r requirements.txt
```

3. Set up your environment variables:
   - Copy the `.env.example` file to create a new file named `.env`:
   ```bash
   cp .env.example .env
   ```
   - Edit the `.env` file and add your API keys and configure other settings:
   ```bash
   OPENAI_API_KEY=your_openai_api_key
   TAVILY_API_KEY=your_tavily_api_key
   ```
You can also add any other env variable for your GPT Researcher configuration.

## 🚀 Running the MCP Server

You can run the MCP server in several ways:

### Method 1: Directly using Python

```bash
python server.py
```

### Method 2: Using the MCP CLI (if installed)

```bash
mcp run server.py
```

### Method 3: Using Docker (recommended for production)

#### Quick Start

The simplest way to run with Docker:

```bash
# Build and run with docker-compose
docker-compose up -d

# Or manually:
docker build -t gptr-mcp .
docker run -d \
  --name gptr-mcp \
  -p 8000:8000 \
  --env-file .env \
  gptr-mcp
```

#### For n8n Integration

If you need to connect to an existing n8n network:

```bash
# First, start the container
docker-compose up -d

# Then connect to your n8n network
docker network connect n8n-mcp-net gptr-mcp

# Or create a shared network first
docker network create n8n-mcp-net
docker network connect n8n-mcp-net gptr-mcp
```

**Note**: The Docker image uses Python 3.11 to meet the requirements of gpt-researcher >=0.12.16. If you encounter errors during the build, ensure you're using the latest Dockerfile from this repository.

Once the server is running, you'll see output indicating that the server is ready to accept connections. You can verify it's working by:

1. **SSE Endpoint**: Access the Server-Sent Events endpoint at http://localhost:8000/sse to get a session ID
2. **MCP Communication**: Use the session ID to send MCP messages to http://localhost:8000/messages/?session_id=YOUR_SESSION_ID
3. **Testing**: Run the test script with `python test_mcp_server.py`

**Important for Docker/n8n Integration:**
- The server binds to `0.0.0.0:8000` to work with Docker containers
- Uses SSE transport for web-based MCP communication  
- Session management requires getting a session ID from `/sse` endpoint first
- Each client connection needs a unique session ID for proper communication

## 🚦 Transport Modes & Best Practices

The GPT Researcher MCP server supports multiple transport protocols and automatically chooses the best one for your environment:

### Transport Types

| Transport | Use Case | When to Use |
|-----------|----------|-------------|
| **STDIO** | Claude Desktop, Local MCP clients | Default for local development |
| **SSE** | Docker, Web clients, n8n integration | Auto-enabled in Docker |
| **Streamable HTTP** | Modern web deployments | Advanced web deployments |

### Automatic Detection

The server automatically detects your environment:

```bash
# Local development (default)
python server.py
# ➜ Uses STDIO transport (Claude Desktop compatible)

# Docker environment  
docker run gptr-mcp
# ➜ Auto-detects Docker, uses SSE transport

# Manual override
export MCP_TRANSPORT=sse
python server.py
# ➜ Forces SSE transport
```

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `MCP_TRANSPORT` | Force specific transport | `stdio` | `sse`, `streamable-http` |
| `DOCKER_CONTAINER` | Force Docker mode | Auto-detected | `true` |

### Configuration Examples

#### For Claude Desktop (Local)
```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "gpt-researcher": {
      "command": "python",
      "args": ["/absolute/path/to/server.py"],
      "env": {
         "..."
      }
    }
  }
}
```

#### For Docker/Web Deployment
```bash
# Set transport explicitly for web deployment
export MCP_TRANSPORT=sse
python server.py

# Or use Docker (auto-detects)
docker-compose up -d
```

#### For n8n MCP Integration
```bash
# Use the container name as hostname
docker run --name gptr-mcp -p 8000:8000 gptr-mcp

# In n8n, connect to: http://gptr-mcp:8000/sse
```

### Transport Endpoints

When using SSE or HTTP transports:

- **Health Check**: `GET /health`
- **SSE Endpoint**: `GET /sse` (get session ID)
- **MCP Messages**: `POST /messages/?session_id=YOUR_SESSION_ID`

### Best Practices

1. **Local Development**: Use default STDIO for Claude Desktop
2. **Production**: Use Docker with automatic SSE detection
3. **Testing**: Use health endpoints to verify connectivity
4. **n8n Integration**: Always use container networking with Docker
5. **Web Deployment**: Consider Streamable HTTP for modern clients

## Integrating with Claude

You can integrate your MCP server with Claude using:

**[Claude Desktop Integration](https://docs.gptr.dev/docs/gpt-researcher/mcp-server/claude-integration)** - For using with Claude desktop application on Mac

For detailed instructions, follow the link above.

## 💻 Claude Desktop Integration

To integrate your locally running MCP server with Claude for Mac, you'll need to:

1. Make sure the MCP server is installed and running
2. Configure Claude Desktop:
   - Locate or create the configuration file at `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Add your local GPT Researcher MCP server to the configuration **with environment variables**
   - Restart Claude to apply the configuration

### ⚠️ Important: Environment Variables Required

Claude Desktop launches your MCP server as a separate subprocess, so you **must** explicitly pass your API keys in the configuration. The server cannot access your shell's environment variables or `.env` file automatically.

### Configuration Example

```json
{
  "mcpServers": {
    "gptr-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/your/server.py"],
      "env": {
        "OPENAI_API_KEY": "your-actual-openai-key-here",
        "TAVILY_API_KEY": "your-actual-tavily-key-here"
      }
    }
  }
}
```

### Security Note

**🔒 Your Claude Desktop config contains sensitive API keys.** Protect it:

```bash
chmod 600 ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Never commit this file to version control.

### Alternative: Environment Variable Script

For better security, create a wrapper script:

**run_gptr_mcp.sh**:
```bash
#!/bin/bash
source /path/to/your/.env
python /absolute/path/to/server.py
```

Then use it in Claude Desktop:
```json
{
  "mcpServers": {
    "gptr-mcp": {
      "command": "/absolute/path/to/run_gptr_mcp.sh"
    }
  }
}
```

For complete step-by-step instructions, see the [Claude Desktop Integration guide](https://docs.gptr.dev/docs/gpt-researcher/mcp-server/claude-integration).

## 📝 Example Usage with Claude

```
User: I'm considering investing in NVIDIA. Can you research the current state of the company, recent stock performance, latest product announcements, and analyst opinions?

Claude: I'll help you research NVIDIA for investment purposes. This will take a moment as I conduct deep research to find the most up-to-date information about their stock performance, recent developments, and expert analysis.

[Claude uses deep_research tool - this takes 30-40 seconds]

Claude: Based on my research, here's a comprehensive analysis of NVIDIA's current state:

## NVIDIA (NVDA) Current Status

### Recent Stock Performance
- Current price: $942.89 (as of my research)
- YTD performance: +90.4% 
- 52-week range: $460.30 - $974.00
- Market cap: ~$2.32 trillion

### Recent Key Developments
1. **Blackwell AI Platform**: At GTC 2024, NVIDIA unveiled the Blackwell architecture, their next-generation AI chip platform promising 4x performance improvement over Hopper. Major cloud providers (AWS, Google, Microsoft) have already committed to integrating Blackwell.

2. **Q1 FY2025 Earnings (May 2024)**: 
   - Revenue: $26.0 billion (+262% YoY)
   - Data Center revenue: $22.6 billion (+427% YoY)
   - Gross margin: 78.4%
   - Announced 10-for-1 stock split effective June 7, 2024

3. **Supply Chain Expansion**: Increased investments in manufacturing capacity with TSMC to address ongoing chip shortages for their high-demand AI GPUs.

### Analyst Consensus
- Strong Buy consensus with 37 analysts rating it "Buy," 5 "Hold," and 0 "Sell"
- Average price target: $1,042 (post-split adjusted: $104.20)
- Key bull thesis: Continued AI infrastructure spending and NVIDIA's dominant position in AI chips
- Key bear concerns: Valuation, potential competition from AMD, Intel, and custom silicon from tech giants

### Industry Position
- Dominant in AI GPU market with estimated 80-90% market share
- Expanding ecosystem through CUDA software platform and industry partnerships
- Diversifying beyond chips with DGX Cloud, AI software platforms, and automotive solutions
```

## 🔧 Troubleshooting

If you encounter issues while running the MCP server:

### General Issues

1. **API Keys**: Make sure your API keys are correctly set in the `.env` file
2. **Python Version**: Check that you're using Python 3.11 or higher (required by gpt-researcher >=0.14.0)  
3. **Dependencies**: Ensure all dependencies are installed correctly: `pip install -r requirements.txt`
4. **Server Logs**: Check the server logs for error messages

### Docker Issues

1. **Container not accessible**: 
   - Verify the container is running: `docker ps | grep gptr-mcp`
   - Check container logs: `docker logs gptr-mcp`
   - Confirm the server is binding to 0.0.0.0:8000 (logs should show this)

2. **n8n Integration Issues**:
   - Ensure both containers are on the same Docker network
   - Use the container name `gptr-mcp` as the hostname in n8n
   - Set the MCP server URL to: `http://gptr-mcp:8000/sse`

3. **Session ID Issues**:
   - The server uses SSE transport which requires session management
   - First, get a session ID by connecting to `/sse` endpoint
   - Use the session ID in subsequent MCP requests: `/messages/?session_id=YOUR_ID`
   - Each client needs its own session ID

### n8n MCP Integration Steps

1. **Get Session ID**:
   ```bash
   curl http://gptr-mcp:8000/sse
   # Look for: data: /messages/?session_id=XXXXX
   ```

2. **Initialize MCP**:
   ```bash
   curl -X POST http://gptr-mcp:8000/messages/?session_id=YOUR_SESSION_ID \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"roots": {"listChanged": true}}, "clientInfo": {"name": "n8n-client", "version": "1.0.0"}}}'
   ```

3. **Call Tools**:
   ```bash
   curl -X POST http://gptr-mcp:8000/messages/?session_id=YOUR_SESSION_ID \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "quick_search", "arguments": {"query": "test"}}}'
   ```

### Testing the Server

Run the included test script to verify functionality:

```bash
python test_mcp_server.py
```

This will test:
- SSE connection and session ID retrieval
- MCP initialization  
- Tool discovery and execution

### Claude Desktop Issues

If your MCP server isn't working with Claude Desktop:

1. **Server not appearing in Claude**:
   - Check your `claude_desktop_config.json` syntax is valid JSON
   - Ensure you're using **absolute paths** (not relative)
   - Verify the path to `server.py` is correct
   - Restart Claude Desktop completely

2. **"OPENAI_API_KEY not found" error**:
   - Make sure you added API keys to the `env` section in your config
   - Don't forget **both** `OPENAI_API_KEY` and `TAVILY_API_KEY`
   - API keys should be the actual keys, not placeholders

3. **Tools not showing up**:
   - Look for the 🔧 tools icon in Claude Desktop
   - Check that Claude Desktop config file is in the right location:
     - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
     - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

4. **Python/Permission issues**:
   - Make sure Python is accessible from the command line: `python --version`
   - Try using full Python path: `"command": "/usr/bin/python3"` or `"command": "python3"`
   - Check file permissions on your server.py file

5. **Still not working?**
   - Test the server manually: `python server.py` (should show STDIO transport message)
   - Check Claude Desktop logs (if available)
   - Try the alternative script method from the integration section above

## 👣 Next Steps

- Explore the [MCP protocol documentation](https://docs.anthropic.com/claude/docs/model-context-protocol) to better understand how to integrate with Claude
- Learn about [GPT Researcher's core features](https://docs.gptr.dev/docs/gpt-researcher/getting-started/introduction) to enhance your research capabilities
- Check out the [Advanced Usage](https://docs.gptr.dev/docs/gpt-researcher/mcp-server/advanced-usage) guide for more configuration options

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support / Contact

- [Community Discord](https://discord.gg/QgZXvJAccX)
- Email: assaf.elovic@gmail.com

<p align="right">
  <a href="#top">⬆️ Back to Top</a>
</p>
