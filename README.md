# Construction Procurement Agent

A multi-agent AI system for construction procurement built with Google ADK. Features intelligent routing, RAG-based knowledge retrieval, and safe email automation with Human-in-the-Loop approval.

## Architecture

**Supervisor Pattern (Router):**
```
root_agent (Supervisor)
├── query_agent (Retrieval Augmented Generation)
└── purchaser_agent (Email Automation + Human-in-the-Loop)
```

The Supervisor Agent analyzes user intent and routes requests to specialist agents:
- **Information queries** → Query Agent (searches ChromaDB knowledge base)
- **Purchase requests** → Purchaser Agent (drafts emails with mandatory approval)

## Features

✅ **Multi-Agent System** - Supervisor orchestrates specialist agents
✅ **RAG Knowledge Base** - ChromaDB stores and retrieves procurement data
✅ **Gmail MCP Integration** - Connects to Gmail for real email sending
✅ **Human-in-the-Loop** - Requires explicit approval before sending emails
✅ **Graceful Fallback** - Works in demo mode without Gmail authentication

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js (for Gmail MCP server)
- Google API Key

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
# Add your GOOGLE_API_KEY to .env file
```

### Run the Agent

```bash
# Command-line interface
adk run .

# Web interface (if ADK web is installed)
adk run web .
```

### Example Usage

**Query the knowledge base:**
```
User: What is the status of the brick order?
Agent: The brick order is currently marked as "In Transit" and is expected to arrive on July 18th.
```

**Place a purchase order:**
```
User: I want to buy 100 bricks from Bob at bob@brickco.com for $1 each
Agent: I'll draft the purchase order... [shows draft] Does this look correct?
User: yes, send it
Agent: ✓ Email sent successfully
```

## Project Structure

```
procure/
├── agent.py                    # Root agent (Supervisor)
├── __init__.py                 # Package initialization  
├── requirements.txt            # Dependencies
├── .env                        # API keys
├── src/
│   ├── agents/
│   │   ├── query_agent.py      # RAG agent
│   │   └── purchaser_agent.py  # Email automation agent
│   └── utils/
│       ├── chroma_db.py        # ChromaDB utilities
│       └── mcp_client.py       # Gmail MCP client
├── ingest.py                   # Data ingestion script
├── GMAIL_SETUP.md              # Gmail OAuth setup guide
└── MCP_STATUS.md               # MCP connection status
```

## Configuration

### Gmail MCP (Optional)
To enable real Gmail sending, configure OAuth credentials. See [GMAIL_SETUP.md](GMAIL_SETUP.md) for details.

**Without Gmail OAuth:** The system works in demo mode with graceful fallback.

### Environment Variables
```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key

# Optional (for Gmail MCP)
MCP_SERVER_COMMAND=npx
MCP_SERVER_ARGS=-y @modelcontextprotocol/server-gmail
```

##Data Ingestion

Populate the knowledge base with procurement data:

```bash
python ingest.py
```

This creates mock email data in ChromaDB. For production, modify `ingest.py` to connect to your actual Gmail account via MCP.

## Technical Details

### ADK Compliance
- Uses `Agent` from `google.adk.agents.llm_agent`
- Defines `root_agent` variable for ADK runtime
- Tools implemented as Python functions
- Follows ADK project structure conventions

### Safety Features
- **Human-in-the-Loop:** Emails require explicit user approval
- **Draft Preview:** Users review email content before sending
- **Graceful Fallback:** Fails safely if MCP unavailable

### Technologies
- **Framework:** Google Agent Development Kit (ADK)
- **LLM:** Gemini 2.0 Flash
- **Vector DB:** ChromaDB
- **MCP:** Gmail MCP Server

## Development

### Testing
```bash
# Test MCP connection
python test_mcp.py

# Test basic MCP availability  
python test_mcp_basic.py
```

### Adding New Agents
1. Create new agent file in `src/agents/`
2. Define tools as Python functions
3. Create `Agent` instance with model, name, description, instruction, and tools
4. Import and use in `agent.py` supervisor

## Troubleshooting

**"Module not found" errors:**
- Ensure you're running from the project root
- ADK handles imports differently than normal Python

**MCP connection fails:**
- Check Node.js is installed: `npx --version`
- For production, complete Gmail OAuth setup
- System works in demo mode without MCP

**Agent not routing correctly:**
- Check the supervisor's `instruction` parameter
- Verify tool docstrings are descriptive
- Test with clearer user prompts

## License

This is a capstone project for educational purposes.

## Acknowledgments

Built with:
- [Google ADK](https://google.github.io/adk-docs/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [ChromaDB](https://www.trychroma.com/)
