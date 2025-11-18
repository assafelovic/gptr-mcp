# Enhanced MCP Servers - Professional Implementation

## 🚀 Overview

This repository contains two professionally enhanced MCP (Model Context Protocol) servers built with FastMCP, following industry best practices:

1. **GPT-Researcher MCP Server** (`gpt_researcher_mcp_enhanced.py`)
   - Advanced research and analysis capabilities
   - Document analysis with AI
   - Stakeholder identification
   - Comprehensive reporting

2. **Document Analysis MCP Server** (`document_analysis_mcp.py`)
   - Full stakeholder analysis suite
   - Funding program matching
   - Problem/solution analysis
   - Opportunity identification
   - Multi-format report generation

## ✨ Key Improvements

### Architecture & Design
- ✅ **FastMCP Framework**: Modern async implementation with decorators
- ✅ **Pydantic V2 Models**: Type-safe input validation with comprehensive constraints
- ✅ **Proper Error Handling**: Detailed error messages with actionable suggestions
- ✅ **Security**: Path traversal prevention, input sanitization
- ✅ **Async/Await**: Non-blocking I/O operations for better performance

### Code Quality
- ✅ **Clean Code Structure**: Organized into sections (models, helpers, tools)
- ✅ **Type Hints**: Full type annotations throughout
- ✅ **Documentation**: Comprehensive docstrings for all tools
- ✅ **Enums**: Type-safe options for all parameters
- ✅ **DRY Principle**: Reusable helper functions
- ✅ **Configuration**: Environment-based with validation

### Features
- ✅ **Multiple Output Formats**: JSON, Markdown, HTML, Text
- ✅ **AI Integration**: OpenAI API with proper error handling
- ✅ **Web Search**: Tavily API integration for funding discovery
- ✅ **Pagination Support**: Handle large datasets efficiently
- ✅ **Context Preservation**: Detailed context in search results
- ✅ **Metadata Tracking**: Timestamps, file info, analysis details

## 📋 Prerequisites

```bash
# Python 3.8 or higher required
python --version

# Create virtual environment (recommended)
python -m venv mcp_env
source mcp_env/bin/activate  # On Windows: mcp_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 🔧 Configuration

Create a `.env` file in your project directory:

```env
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# Optional: OpenAI Configuration
OPENAI_BASE_URL=https://api.openai.com/v1

# Document Path Configuration
DOC_PATH=C:/Desk  # Or your preferred directory

# Optional: LLM Model Selection
STRATEGIC_LLM=gpt-4o
SMART_LLM=gpt-4o
FAST_LLM=gpt-3.5-turbo
```

## 🚀 Running the Servers

### Option 1: GPT-Researcher MCP Server

```bash
# Run directly with FastMCP
python gpt_researcher_mcp_enhanced.py

# Or run as MCP server
mcp install gpt_researcher_mcp_enhanced.py
mcp run gpt_researcher_mcp
```

### Option 2: Document Analysis MCP Server

```bash
# Run directly with FastMCP
python document_analysis_mcp.py

# Or run as MCP server
mcp install document_analysis_mcp.py
mcp run document_analysis_mcp
```

## 📚 Available Tools

### GPT-Researcher Server (5 tools)

| Tool | Description | Key Features |
|------|-------------|--------------|
| `gpt_research` | Run GPT Researcher on topics | Multi-page reports, source tracking |
| `analyze_project_data` | Analyze JSON data | Statistics, trends, AI insights |
| `analyze_documents` | Analyze files in directory | Count, details, content, metadata |
| `identify_stakeholders` | AI stakeholder identification | Categories, roles, influence mapping |
| `generate_stakeholder_report` | Comprehensive reports | Multiple formats, customizable sections |

### Document Analysis Server (7 tools)

| Tool | Description | Key Features |
|------|-------------|--------------|
| `read_file_content` | Safe file reading | Path traversal protection, encoding handling |
| `search_in_files` | Search text in files | Context extraction, line numbers |
| `identify_stakeholders` | AI-powered identification | Multi-category, relationship mapping |
| `analyze_stakeholder_problems` | Problem analysis | Severity assessment, root causes |
| `identify_opportunities` | Opportunity discovery | Multiple types, ROI estimation |
| `find_matching_funding` | Funding program matching | Web crawling, compatibility scoring |
| `generate_comprehensive_report` | Full analysis reports | Multiple formats, customizable depth |

## 📖 Usage Examples

### Example 1: Research a Topic

```python
# Using gpt_research tool
{
  "tool": "gpt_research",
  "params": {
    "topic": "AI applications in healthcare",
    "pages": 5
  }
}
```

### Example 2: Identify Stakeholders

```python
# Using identify_stakeholders tool
{
  "tool": "identify_stakeholders",
  "params": {
    "file_pattern": "*.txt",
    "max_files": 20,
    "use_ai_analysis": true,
    "categories": ["primary", "secondary", "indirect"]
  }
}
```

### Example 3: Find Funding Matches

```python
# Using find_matching_funding tool
{
  "tool": "find_matching_funding",
  "params": {
    "funding_websites": [
      "https://ec.europa.eu/info/funding-tenders",
      "https://www.grants.gov"
    ],
    "project_files_pattern": "*.txt",
    "top_matches": 5
  }
}
```

### Example 4: Generate Comprehensive Report

```python
# Using generate_comprehensive_report tool
{
  "tool": "generate_comprehensive_report",
  "params": {
    "title": "Project Stakeholder Analysis",
    "file_pattern": "*.txt",
    "include_problems": true,
    "include_solutions": true,
    "include_opportunities": true,
    "format": "markdown",
    "report_type": "detailed"
  }
}
```

## 🔍 Testing with MCP Inspector

Test your MCP server using the MCP Inspector:

```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Test the server
npx @modelcontextprotocol/inspector python gpt_researcher_mcp_enhanced.py

# Or for the document analysis server
npx @modelcontextprotocol/inspector python document_analysis_mcp.py
```

## 📊 Response Formats

All tools support multiple output formats:

- **JSON**: Structured data for programmatic processing
- **Markdown**: Human-readable with formatting
- **HTML**: Web-ready with styling
- **Text**: Plain text for simple consumption

## 🛡️ Security Features

1. **Path Traversal Protection**: Validates all file paths
2. **Input Sanitization**: Pydantic validation on all inputs
3. **Rate Limiting Ready**: Structured for rate limit implementation
4. **Error Masking**: No sensitive data in error messages
5. **Encoding Safety**: Handles multiple file encodings

## 🔄 Error Handling

The servers provide detailed error information:

```json
{
  "status": "error",
  "error": "Descriptive error message",
  "suggestion": "Actionable suggestion to fix the issue",
  "context": {
    "parameter": "value that caused error",
    "expected": "what was expected"
  }
}
```

## 📈 Performance Considerations

- **Async Operations**: All I/O operations are async for better concurrency
- **Pagination**: Large datasets are paginated automatically
- **Caching Ready**: Structure supports adding caching layers
- **Resource Limits**: Configurable limits on file sizes and counts
- **Timeout Handling**: HTTP requests with configurable timeouts

## 🔧 Advanced Configuration

### Custom Models

You can use different LLM providers by modifying the environment variables:

```env
# Use different models for different tasks
STRATEGIC_LLM=gpt-4-turbo-preview  # For complex analysis
SMART_LLM=gpt-4o                    # For standard analysis
FAST_LLM=gpt-3.5-turbo              # For quick tasks
```

### Custom Document Paths

Configure multiple document paths:

```python
# In your .env file
DOC_PATH=/path/to/documents
ARCHIVE_PATH=/path/to/archives
REPORTS_PATH=/path/to/reports
```

## 🐛 Troubleshooting

### Common Issues and Solutions

1. **OPENAI_API_KEY not working**
   - Verify key is active: `curl https://api.openai.com/v1/models -H "Authorization: Bearer YOUR_KEY"`
   - Check for extra spaces in .env file
   - Ensure .env is in the same directory

2. **File not found errors**
   - Check DOC_PATH exists and is accessible
   - Verify file patterns match actual files
   - Use forward slashes (/) in paths even on Windows

3. **Timeout errors**
   - Increase timeout in httpx.AsyncClient
   - Check network connectivity
   - Reduce max_tokens for faster responses

4. **Memory issues with large files**
   - Reduce max_files parameter
   - Decrease max_chars_per_file
   - Process files in batches

## 📝 Development Guidelines

### Adding New Tools

1. Define Pydantic model for input validation
2. Create tool function with @mcp.tool decorator
3. Add comprehensive docstring
4. Implement error handling
5. Add to documentation

Example:

```python
class MyToolInput(BaseModel):
    """Input validation for my tool."""
    param1: str = Field(..., description="Description")
    param2: int = Field(default=10, ge=1, le=100)

@mcp.tool(
    name="my_tool",
    annotations={
        "title": "My Tool Title",
        "readOnlyHint": True,
        "destructiveHint": False
    }
)
async def my_tool(params: MyToolInput) -> str:
    """Tool description and documentation."""
    try:
        # Implementation
        return json.dumps({"status": "success"})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})
```

## 📚 Project Structure

```
.
├── gpt_researcher_mcp_enhanced.py  # Enhanced research server
├── document_analysis_mcp.py        # Document analysis server
├── requirements.txt                 # Python dependencies
├── .env                            # Environment configuration
├── README.md                       # This file
└── docs/                          # Additional documentation
    ├── API.md                     # API reference
    ├── EXAMPLES.md                # Usage examples
    └── DEVELOPMENT.md             # Development guide
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Use type hints
5. Run linting before submitting

## 📄 License

This project is provided as-is for educational and commercial use.

## 🙏 Acknowledgments

- Built with [FastMCP](https://github.com/modelcontextprotocol/fastmcp)
- Following [MCP Best Practices](https://modelcontextprotocol.io)
- Inspired by the MCP community

## 📞 Support

For issues or questions:
1. Check this README
2. Review code comments
3. Test with MCP Inspector
4. Check environment variables

---

**Version**: 2.0.0  
**Last Updated**: November 2024  
**Status**: Production Ready

## 🎯 Next Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Configure environment**: Create `.env` file
3. **Run server**: `python gpt_researcher_mcp_enhanced.py`
4. **Test with Inspector**: `npx @modelcontextprotocol/inspector`
5. **Integrate with your application**: Use MCP client libraries

Enjoy your enhanced MCP servers! 🚀