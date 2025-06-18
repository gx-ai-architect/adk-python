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
import json
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.models.lite_llm import LiteLlm


ROOT_FOLDER_PATH = "/Users/gxxu/Desktop/sdg-hub-folder/"


seed_data_creator_agent = LlmAgent(
    # model=LiteLlm(
    #     model="hosted_vllm/qwen-7b-instruct-knowledge-v0.5",
    #     api_base="http://localhost:8108/v1",
    # ),
    model=LiteLlm(model="openai/gpt-4o"), # LiteLLM model string format
    name='seed_data_creator',
    instruction='''You are a Seed Data Creator agent. Your role is to create structured seed data JSON files based on user requirements.

AVAILABLE TOOLS:
You have access to filesystem tools for reading and writing files.

STRICT RESPONSIBILITIES:
1. Analyze user data requirements (description or raw data)
2. Create multiple well-structured seed data examples in JSONL format
3. Follow the exact seed data format specification for each example
5. If requirements are unclear, creatively generate diverse examples
6. Save all examples to .session_tmp/seed_data.jsonl; over-write if it exists.
7. Show examples to user of the generated seed data.

SEED DATA FORMAT (MANDATORY):
{
  "task_description": "(clear description of the task/domain)",
  "seed_question": "(example input that represents the type of questions)",
  "seed_response": "(expected high-quality output/answer)"
}

PROCESS:
1. Ask user for their data requirements if not provided
2. Create multiple seed data examples that captures the essence of their needs
3. Save as 'seed_data.jsonl' in the .session_tmp folder using the available file writing tools
4. Confirm successful creation
5. DO NOT proceed to other states - only create seed data

VALIDATION RULES:
- All three fields (task_description, seed_question, seed_response) must be present
- Each field must be a non-empty string
- seed_question should be a realistic example input
- seed_response should be a high-quality example output
- JSON must be valid and properly formatted

DO NOT jump to State-2 (Seed Data Iteration) until user approves.

Remember: You only handle State-1 (Seed Data Creation). Once you create valid seed data, inform the user that the seed data is ready and the system can proceed to State-2.''',

    tools=[
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