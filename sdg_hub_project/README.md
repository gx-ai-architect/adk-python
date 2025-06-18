# MCP Client Project

This project is a local MCP client that interacts with the MCP server. Below are the instructions to set up and run the client.

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

Before starting the MCP client agent, ensure that you have set the `OPENAI_API_KEY` as an environment variable. You can do this by running:

```bash
export OPENAI_API_KEY=your_openai_api_key
```

Replace `your_openai_api_key` with your actual OpenAI API key.

## Starting the MCP Client Agent

To start the MCP client agent, use the following command:

```bash
adk web
```

This will launch the MCP client agent, allowing it to interact with the MCP server.

