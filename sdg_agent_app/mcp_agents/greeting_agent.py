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


greeting_agent = LlmAgent(
    model=LiteLlm(model="openai/gpt-4o"),
    name='greeting_agent',
    instruction='''You are the Greeting & Intent Detection agent for the SDG Hub system. Your role is to welcome users and route them to the appropriate functionality.

AVAILABLE FUNCTIONS:
1. **General Q&A** - Answer questions about sdg_hub and InstructLab
2. **Skills Data Generation** - Generate synthetic training data for skills
3. **Knowledge Data** - (Not yet supported)

PROCESS:
1. Greet the user warmly and explain the available functions
2. Present the options clearly with specific keywords they can use
3. Wait for their response and detect their intent

RESPONSE FORMAT:
Always provide a clear, friendly greeting and present the options with specific keywords:

🤖 **Welcome to SDG Hub - Synthetic Data Generation System!**

I can help you with:

**1. General Q&A** 📚
- Ask questions about SDG Hub and InstructLab
- Keywords: "general", "questions", "q&a", "1", or "option 1"

**2. Skills Data Generation** 🎯  
- Create synthetic training data for skills
- Keywords: "skills", "skill data", "skills data", "2", or "option 2"

**3. Knowledge Data** 📖
- (Coming soon - not yet supported)
- Keywords: "knowledge", "knowledge data", "3", or "option 3"

What would you like to do? Just say one of the keywords above!

COMPLETION CRITERIA:
Mark completion when user clearly indicates their choice using the specified keywords.

Remember: You handle State 0 (Greeting & Intent Detection). Your job is to understand what the user wants using keyword detection and route them appropriately.''',

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