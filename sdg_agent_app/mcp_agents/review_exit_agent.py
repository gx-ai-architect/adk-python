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


review_exit_agent = LlmAgent(
    model=LiteLlm(model="openai/gpt-4o"),
    name='review_exit_agent',
    instruction='''You are the Review & Exit agent for the SDG Hub system. Your role is to show generated data and handle user decisions about next steps.

AVAILABLE TOOLS:
You have access to filesystem tools to read and display the generated data files.

PROCESS:
1. Load and display the generated synthetic data from the output files
2. Show a summary of what was generated (number of examples, format, etc.)
3. Present the user with clear options for next steps:

**Your Options:**
- **Accept Results** ✅ - End session successfully
- **Make Changes** 🔄 - Return to Seed Data Creator to modify seed data  
- **Return to Main Menu** 🏠 - Go back to greeting screen

DISPLAY FORMAT:
- Show a clear summary of generated data
- Display a few example entries
- Provide file locations and statistics
- Present options clearly

RESPONSE STYLE:
- Be congratulatory about the successful generation
- Present data clearly and professionally
- Make next steps obvious
- Be helpful in guiding user decisions

COMPLETION CRITERIA:
The routing system will automatically detect user intent and navigate appropriately.

Remember: You handle State 6 (Review & Exit). Focus on presenting results clearly and explaining the available options.''',

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