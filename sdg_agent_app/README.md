# SDG Hub Multi-Agent System

A multi-agent system for creating synthetic training data using SDG Hub and InstructLab.

## 7-State System Overview

The system uses intelligent routing across 7 states:

- **State 0**: Greeting & Intent Detection - Welcome and route to workflows
- **State 1**: General Q&A - Answer questions about SDG Hub/InstructLab  
- **State 2**: Knowledge Flow - Handle knowledge data (placeholder)
- **State 3**: Skills Greeting - Explain skills data and assess needs
- **State 4**: Seed Data Creator - Create structured seed data files
- **State 5**: Data Generator - Generate synthetic training data
- **State 6**: Review & Exit - Review results and choose next steps

## Quick Start

```bash
cd sdg_agent_app
adk web
```

Then open your browser to the URL shown (typically http://localhost:8000).

## Environment Setup

1. Set your OpenAI API key:
```bash
export OPENAI_API_KEY=your_openai_api_key
```

2. Setup the SDG Hub MCP server:
https://github.com/Red-Hat-AI-Innovation-Team/sdg-mcp-server

That's it! The system will guide you through creating training data with natural language interaction.

