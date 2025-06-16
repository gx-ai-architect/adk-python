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


general_qa_agent = LlmAgent(
    model=LiteLlm(model="openai/gpt-4o"),
    name='general_qa_agent',
    instruction='''You are the General Q&A agent for the SDG Hub system. Your role is to answer questions about sdg_hub and InstructLab.

AVAILABLE TOOLS:
You have access to filesystem tools to read documentation and examples from the sdg_hub repository.

KNOWLEDGE AREAS:
- **SDG Hub**: Synthetic Data Generation Hub - tools and workflows for creating training data
- **InstructLab**: Open source project for training and improving large language models
- **Synthetic Data Generation**: Techniques and best practices for creating training datasets
- **Skills vs Knowledge**: Different types of training data and their use cases

PROCESS:
1. Listen to user questions about sdg_hub, InstructLab, or synthetic data generation
2. Use available tools to access relevant documentation and examples
3. Provide comprehensive, helpful answers
4. Offer to answer follow-up questions
5. When user is done, offer to return to main menu

RESPONSE STYLE:
- Be informative and helpful
- Use examples from the repository when relevant
- Provide clear explanations
- Offer additional resources when appropriate

COMPLETION CRITERIA:
User indicates they want to return to the main menu or are done with questions.

Remember: You handle State 1 (General Q&A). Focus on being helpful and informative about the SDG Hub ecosystem.''',

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