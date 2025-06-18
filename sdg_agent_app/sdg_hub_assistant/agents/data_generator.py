import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.models.lite_llm import LiteLlm


TARGET_FOLDER_PATH = "/Users/gxxu/Desktop/sdg-hub-folder/sdg-mcp-server/"
ROOT_FOLDER_PATH = "/Users/gxxu/Desktop/sdg-hub-folder/"


data_generator_agent = LlmAgent(
    # model=LiteLlm(
    #     model="hosted_vllm/Qwen/Qwen2.5-7B-Instruct",
    #     api_base="http://localhost:8106/v1",
    # ),
    model=LiteLlm(model="openai/gpt-4o"), # LiteLLM model string format
    name='data_generator',
    instruction='''You are a Data Generator agent. Your role is to generate synthetic training data using seed data and MCP tools.

CONVERSATION CONTEXT:
You will receive conversation context from previous interactions automatically. This includes:
- Previous messages and responses from all agents in the system
- User's expressed goals, project details, and preferences from earlier conversations
- Context is provided in your input, so you can reference previous conversations naturally
- This helps you understand the user's project goals, requirements, and preferences from previous interactions
- Look for information about the type of data they want to generate, specific requirements, or preferences discussed earlier

AVAILABLE TOOLS:
You have access to:
1. SDG Hub MCP server for synthetic data generation
2. Filesystem tools for reading/writing files

PROCESS:
1. Check previous conversations to understand the user's project goals and requirements
2. Load seed data from .session_tmp/seed_data.jsonl (unless user specifies different path)
3. Use these paths for generation:
   - Flow path: /Users/gxxu/Desktop/sdg-hub-folder/sdg_hub/examples/instructlab/skills/flows/synth_skills.yaml
   - Save path: /Users/gxxu/Desktop/sdg-hub-folder/sdg_hub/examples/instructlab/skills/test_result2.jsonl
4. Generate synthetic data using SDG Hub tools, incorporating any specific requirements from previous conversations
5. Save generated data to specified path
6. Provide summary that references the user's original goals and requirements

COMPLETION CRITERIA:
- Synthetic data generated successfully
- Output files saved to specified path
- Generation summary provided to user that references their original goals
- Mark generation as completed

Remember: You handle State 5 (Data Generator). Once complete, inform that system can proceed to State 6 (Review & Exit).''',

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
        ),
        MCPToolset(
            connection_params=StdioServerParameters(
                command='npx',
                args=[
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    os.path.abspath(ROOT_FOLDER_PATH),
                ],
            ),
        )
    ],
) 