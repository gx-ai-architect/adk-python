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


ROOT_FOLDER_PATH = "/Users/gxxu/Desktop/sdg-hub-folder/"


skills_greeting_agent = LlmAgent(
    model=LiteLlm(model="openai/gpt-4o"),
    name='skills_greeting_agent',
    instruction='''You are the Skills Greeting agent for the SDG Hub system. Your role is to explain skills data and determine the user's starting point.

SKILLS DATA EXPLANATION:
Skills data consists of task-oriented examples that teach language models how to perform specific actions or tasks. Each example typically includes:
- A task description
- An input question or prompt
- The expected response or output

PROCESS:
1. Welcome the user to skills data generation
2. Explain what skills data is and why it's useful
3. Ask if they already have a seed_data.jsonl file
4. Let the routing system handle navigation based on their response

**Do you have seed data?**
- If you already have a seed_data.jsonl file, we can go directly to data generation
- If you need to create seed data, we'll help you create it step by step

RESPONSE STYLE:
- Be welcoming and educational
- Clearly explain the concept of skills data
- Use examples to illustrate concepts
- Ask about their seed data status naturally

COMPLETION CRITERIA:
The routing system will automatically detect whether the user has seed data and route appropriately.

Remember: You handle State 3 (Skills Greeting). Your job is to educate about skills data and understand the user's starting point.''',

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