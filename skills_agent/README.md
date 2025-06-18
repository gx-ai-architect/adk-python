# MCP Client Project

This project contains both a legacy single-agent MCP client and a new **Multi-Agent Synthetic Data Generation System**.

## 🚀 Multi-Agent System (NEW)

The new multi-agent system provides a structured 4-state workflow for synthetic data generation:

**State-1** → **State-2** → **State-3** → **State-4** → **State-1** (loop)

### Quick Start Options

#### Option 1: Interactive Terminal Session
```bash
python multi_agent_main.py
# Choose option 1 for interactive session
```

#### Option 2: ADK Web Interface  
```bash
cd web_agent
adk web
```
Then open your browser to the URL shown (typically http://localhost:8000)

#### Option 3: Validation and Demo
```bash
# Validate system setup
python validate_setup.py

# Run demo session
python multi_agent_main.py
# Choose option 2 for demo
```

### System Features

- **🌱 State-1**: Seed Data Creation - Create structured seed data from requirements
- **🔄 State-2**: Seed Data Iteration - Refine seed data based on feedback  
- **⚡ State-3**: Data Generation - Generate synthetic training data using SDG hub
- **🎯 State-4**: Close/Restart - Complete session or start new cycle

### Special Commands (Available in all interfaces)
- `status` - Show current system state
- `help` - Show detailed help
- `restart` - Start new generation cycle (in State-4)

---

## 📚 Legacy Single Agent

For backward compatibility, the original single agent is still available.

## Installation

To install the `adk` package from the parent directory, navigate to the `adk-python` directory and run the following command:

```bash
cd ..
pip install .
```

## Testing MCP Server Connection

To test your MCP server connection, you can use the `test_mcp_server.py` script. This script uses the `MCPToolset` to connect to the server. Run the following command:

```bash
cd sdg_hub_project
python test_mcp_server.py
```

Ensure that the `TARGET_FOLDER_PATH` in the script is correctly set to your MCP server's directory.

## Environment Variables

Before starting any agent, ensure that you have set the required environment variables:

```bash
export OPENAI_API_KEY=your_openai_api_key  # If using OpenAI models
```

Replace `your_openai_api_key` with your actual API key.

## Legacy Single Agent Web Interface

To start the original single agent in web mode:

```bash
# In the main skills_agent directory (not web_agent)
adk web
```

---

## 📖 Documentation

- **[Multi-Agent System Documentation](MULTI_AGENT_README.md)** - Complete guide to the new system
- **[Validation Script](validate_setup.py)** - Check system health
- **[Interactive Examples](multi_agent_main.py)** - See the system in action

## 🎯 Which Interface Should I Use?

| Interface | Best For | Features |
|-----------|----------|-----------|
| **ADK Web** | Web-based interaction, visual interface | Browser UI, session management, easy sharing |
| **Interactive Terminal** | Development, testing, automation | Full control, scripting capability, detailed logs |
| **Demo Mode** | Learning, presentations | Pre-defined workflow, no user input needed |

## 🔧 Troubleshooting

If you encounter issues:

1. **Run validation**: `python validate_setup.py`
2. **Check paths**: Ensure SDG hub paths are correct in configuration
3. **Verify services**: Make sure LLM server and MCP servers are running
4. **Check logs**: Look for detailed error messages in terminal output

## 📁 Project Structure

```
skills_agent/
├── mcp_agents/                  # Multi-agent system core
├── web_agent/                   # ADK Web interface wrapper
├── multi_agent_main.py          # Interactive terminal interface
├── multi_agent_web.py           # Web interface wrapper
├── validate_setup.py            # System validation
├── MULTI_AGENT_README.md        # Detailed documentation
└── README.md                    # This file
```

