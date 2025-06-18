# ./adk_agent_samples/mcp_agent/agent.py
import os # Required for path operations
import subprocess
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.models.lite_llm import LiteLlm

TARGET_FOLDER_PATH = "/Users/gxxu/Desktop/sdg-hub-folder/code-rag-mcp"

root_agent = LlmAgent(
    # model=LiteLlm(model="openai/gpt-4o"), # LiteLLM model string format
    model = LiteLlm(
        # model="hosted_vllm/qwen-knowledge-7b",
        model="hosted_vllm/Qwen/Qwen2.5-7B-Instruct",
        api_base="http://localhost:8106/v1",     # omit if you used env‑vars
        # extra_headers={"Authorization": f"Bearer {token}"}  # if your server needs it
    ),
    name='sdg_hub_agent',
    instruction='Help me answer questions regarding SDG Hub using the provided mcp tool to access the SDG Hub codebase.',

    tools=[
            # Configure MCPToolset so the spawned process runs with the
            # required GitHub environment variables already set.
            # This is functionally the same as executing:
            #   export GITHUB_REPO="sdg_hub" && \
            #   export GITHUB_OWNER="Red-Hat-AI-Innovation-Team" && \
            #   uv run --with mcp mcp run code_rag_mcp/server.py
            MCPToolset(
                connection_params=StdioServerParameters(
                    command="uv",
                    cwd=TARGET_FOLDER_PATH,
                    env={
                        "GITHUB_REPO": "sdg_hub",
                        "GITHUB_OWNER": "Red-Hat-AI-Innovation-Team",
                    },
                    args=[
                        "run",
                        "--with",
                        "mcp",
                        "mcp",
                        "run",
                        "code_rag_mcp/server.py",
                    ],
                ),
        )
    ],

)

    # tools=[
    #     MCPToolset(
    #         connection_params=StdioServerParameters(
    #             command='uv',
    #             args=[
    #                 "run",
    #                 "--with",
    #                 "mcp",
    #                 "mcp",
    #                 "run",
    #                 "sdg_mcp/server.py",
    #             ],
    #         ),
    #     )
    # ],
