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

### Resources
- `research_resource`: Get web resources related to a given task via research.

### Primary Tools

- `deep_research`: Performs deep web research on a topic, finding the most reliable and relevant information
- `quick_search`: Performs a fast web search optimized for speed over quality, returning search results with snippets. Supports any GPTR supported web retriever such as Tavily, Bing, Google, etc... Learn more [here](https://docs.gptr.dev/docs/gpt-researcher/search-engines/retrievers)
- `write_report`: Generate a report based on research results
- `get_research_sources`: Get the sources used in the research
- `get_research_context`: Get the full context of the research

### Prompts

- `research_query`: Create a research query prompt

## Prerequisites

Before running the MCP server, make sure you have:

1. Python 3.10 or higher installed
2. API keys for the services you plan to use:
   - [OpenAI API key](https://platform.openai.com/api-keys)
   - [Tavily API key](https://app.tavily.com)

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

You can start the MCP server in two ways:

### Method 1: Directly using Python

```bash
python server.py
```

### Method 2: Using the MCP CLI (if installed)

```bash
mcp run server.py
```

Once the server is running, you'll see output indicating that the server is ready to accept connections.

## Integrating with Claude

You can integrate your MCP server with Claude using:

**[Claude Desktop Integration](https://docs.gptr.dev/docs/gpt-researcher/mcp-server/claude-integration)** - For using with Claude desktop application on Mac

For detailed instructions, follow the link above.

## 💻 Claude Desktop Integration

To integrate your locally running MCP server with Claude for Mac, you'll need to:

1. Make sure the MCP server is installed and running
2. Configure Claude Desktop:
   - Locate or create the configuration file at `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Add your local GPT Researcher MCP server to the configuration
   - Restart Claude to apply the configuration

For complete step-by-step instructions, see the [Claude Desktop Integration guide](https://docs.gptr.dev/docs/gpt-researcher/mcp-server/claude-integration).

## 📝 Example Usage with Claude

```
User: I'm considering investing in NVIDIA. Can you research the current state of the company, recent stock performance, latest product announcements, and analyst opinions?

Claude: I'll help you research NVIDIA for investment purposes. This will take a moment as I conduct comprehensive research to find the most up-to-date information about their stock performance, recent developments, and expert analysis.

[Claude uses conduct_research tool - this takes 30-40 seconds]

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

1. Make sure your API keys are correctly set in the `.env` file
2. Check that you're using Python 3.10 or higher
3. Ensure all dependencies are installed correctly
4. Check the server logs for error messages

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
