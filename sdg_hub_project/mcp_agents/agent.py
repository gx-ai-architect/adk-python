# ./adk_agent_samples/mcp_agent/agent.py
import os # Required for path operations
import subprocess
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.models.lite_llm import LiteLlm

# Endpoint URL provided by your vLLM deployment
api_base_url = "http://localhost:8100/v1"

# Model name as recognized by *your* vLLM endpoint configuration
model_name_at_endpoint = "hosted_vllm/microsoft/Phi-4-mini-instruct" # Example from vllm_test.py

# Authentication (Example: using gcloud identity token for a Cloud Run deployment)
# Adapt this based on your endpoint's security
try:
    gcloud_token = subprocess.check_output(
        ["gcloud", "auth", "print-identity-token", "-q"]
    ).decode().strip()
    auth_headers = {"Authorization": f"Bearer {gcloud_token}"}
except Exception as e:
    print(f"Warning: Could not get gcloud token - {e}. Endpoint might be unsecured or require different auth.")
    auth_headers = None # Or handle error appropriately

# It's good practice to define paths dynamically if possible,
# or ensure the user understands the need for an ABSOLUTE path.
# For this example, we'll construct a path relative to this file,
# assuming '/path/to/your/folder' is in the same directory as agent.py.
# REPLACE THIS with an actual absolute path if needed for your setup.
# TARGET_FOLDER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "/path/to/your/folder")
# Ensure TARGET_FOLDER_PATH is an absolute path for the MCP server.
# If you created ./adk_agent_samples/mcp_agent/your_folder,
TARGET_FOLDER_PATH = "/Users/gxxu/Desktop/sdg-hub-folder/sdg-mcp-server"

root_agent = LlmAgent(
    model=LiteLlm(model="openai/gpt-4o"), # LiteLLM model string format
    name='sdg_hub_agent',
    instruction='Help me run sdg_hub to generate training data given seed data and formatted documents.',

    tools=[
            MCPToolset(
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
