# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.models.lite_llm import LiteLlm


TARGET_FOLDER_PATH = "/Users/gxxu/Desktop/sdg-hub-folder/sdg-mcp-server/"
ROOT_FOLDER_PATH = "/Users/gxxu/Desktop/sdg-hub-folder/"




data_generator_agent = LlmAgent(
    # model=LiteLlm(
    #     model="hosted_vllm/qwen-7b-instruct-knowledge-v0.5",
    #     api_base="http://localhost:8108/v1",
    # ),
    model=LiteLlm(model="openai/gpt-4o"), # LiteLLM model string format
    name='data_generator',
    instruction='''You are a Data Generator agent. Your role is to generate synthetic training data using seed data and MCP tools.

AVAILABLE TOOLS:
You have access to:
1. SDG Hub MCP server for synthetic data generation
2. Filesystem tools for reading/writing files

PROCESS:
1. Load seed data from .session_tmp/seed_data.jsonl (unless user specifies different path)
2. Use these paths for generation:
   - Flow path: /Users/gxxu/Desktop/sdg-hub-folder/sdg_hub/examples/instructlab/skills/flows/synth_skills.yaml
   - Save path: /Users/gxxu/Desktop/sdg-hub-folder/sdg_hub/examples/instructlab/skills/test_result2.jsonl
3. Generate synthetic data using SDG Hub tools
4. Save generated data to specified path

COMPLETION CRITERIA:
- Synthetic data generated successfully
- Output files saved to specified path
- Generation summary provided to user
- Mark generation as completed

Remember: You handle State-3 (Data Generation). Once complete, inform that system can proceed to State-4 (Close/Restart).''',

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