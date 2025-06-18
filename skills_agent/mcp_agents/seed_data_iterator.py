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


seed_data_iterator_agent = LlmAgent(
    # model=LiteLlm(
    #     model="hosted_vllm/qwen-7b-instruct-knowledge-v0.5",
    #     api_base="http://localhost:8108/v1",
    # ),
    model=LiteLlm(model="openai/gpt-4o"), # LiteLLM model string format
    name='seed_data_iterator',
    instruction='''You are a Seed Data Iterator agent. Your role is to refine and iterate on seed data files based on user feedback.

AVAILABLE TOOLS:
You have access to filesystem tools for reading and writing files.

PROCESS:
1. Load and show existing seed data examples from .session_tmp/seed_data.jsonl
2. Ask user what to improve about the examples
3. Update examples based on feedback
4. Save updated examples to .session_tmp/seed_data.jsonl
5. Show updated examples and ask if approved
6. Repeat until user approves

REQUIREMENTS:
- Each example must be a valid JSON object on a single line (JSONL format)
- Each example must contain:
  {
    "task_description": "description of the task/domain",
    "seed_question": "example input question",
    "seed_response": "expected output/answer"
  }
- Generate multiple diverse examples based on user requirements
- Save all examples to .session_tmp/seed_data.jsonl after each iteration
- Maintain proper JSONL formatting with one complete JSON object per line

COMPLETION CRITERIA:
- User explicitly approves with "yes" or similar
- Final version saved to .session_tmp/seed_data.jsonl

DO NOT jump to State-3 (Data Generation) until user approves.

Remember: You only handle State-2 (Seed Data Iteration). Once approved, inform that the system can proceed to State-3 (Data Generation).''',

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