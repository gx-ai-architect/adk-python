
import asyncio
from mcp import StdioServerParameters
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
import os


TARGET_FOLDER_PATH = "/Users/gxxu/Desktop/sdg-hub-folder/sdg-mcp-server"

async def main():
    toolset = MCPToolset(
        connection_params=StdioServerParameters(
            command='uv',
            cwd=TARGET_FOLDER_PATH,
            args=[
                "run",
                "--with",
                "mcp",
                "mcp",
                "run",
                "sdg_mcp/server.py",
            ],
        ),
    )
    # Optionally, you can fetch tools or perform other operations
    tools = await toolset.get_tools()
    print(f"Available tools: {tools[0].description}")
    await toolset.close()




if __name__ == "__main__":
    asyncio.run(main())

    breakpoint()