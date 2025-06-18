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

"""
Multi-Agent Web Interface Module

This module creates a wrapper that makes the MultiAgentController compatible
with ADK Web's expected agent interface. ADK Web expects to find a 'root_agent'
attribute that is a standard ADK agent.
"""

import os
import asyncio
from typing import Any, AsyncGenerator
from pydantic import Field, PrivateAttr
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.models.lite_llm import LiteLlm
from google.adk.events.event import Event
from google.genai import types
from .multi_agent_controller import MultiAgentController


ROOT_FOLDER_PATH = "/Users/gxxu/Desktop/sdg-hub-folder/"


class MultiAgentWebWrapper(LlmAgent):
    """Wrapper that makes MultiAgentController compatible with ADK Web interface."""
    
    # Use PrivateAttr since this is an internal implementation detail
    _controller: MultiAgentController = PrivateAttr()
    
    def __init__(self, **kwargs):
        # Initialize as a standard LlmAgent for ADK Web compatibility
        super().__init__(
            # model=LiteLlm(
            #     # model="hosted_vllm/qwen-7b-instruct-knowledge-v0.5",
            #     api_base="http://localhost:8108/v1",
            # ),
            model=LiteLlm(model="openai/gpt-4o"), # LiteLLM model string format
            name='multi_agent_sdg_system',
            instruction='''🤖 **Multi-Agent Synthetic Data Generation System**

I am a multi-agent system that guides you through a structured 4-state workflow to generate synthetic training data:

**State Flow:**
State-1: Seed Data Creation → State-2: Seed Data Iteration → State-3: Data Generation → State-4: Close/Restart

**Current Capabilities:**
- 🌱 **State-1**: Create structured seed data from your requirements
- 🔄 **State-2**: Refine seed data based on your feedback  
- ⚡ **State-3**: Generate synthetic training data using SDG hub
- 🎯 **State-4**: Complete session or start new cycle

**How to Use:**
1. Describe your data requirements to create seed data
2. Provide feedback to refine the seed data
3. Specify generation parameters for synthetic data
4. Choose to restart or close when complete

**Special Commands (available from any state):**
- Type 'status' to see current state
- Type 'help' for detailed guidance
- Type 'restart' or 'reset' to start fresh from State-1
- System automatically transitions between states based on completion criteria

**Fresh Start:** The system starts fresh each session in State-1 (Seed Data Creation).

Let's start! Please describe what kind of training data you need to generate.''',
            
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
            **kwargs
        )
        
        # Initialize the multi-agent controller as a private attribute
        self._controller = MultiAgentController('web_multi_agent_system', start_fresh=True)
    
    @property
    def controller(self) -> MultiAgentController:
        """Access the controller via property."""
        return self._controller
    
    async def run_async(self, invocation_context: Any) -> AsyncGenerator[Event, None]:
        """Override run_async to use MultiAgentController."""
        try:
            # Extract user message from the invocation context
            if invocation_context.user_content and invocation_context.user_content.parts:
                prompt = invocation_context.user_content.parts[0].text
            else:
                prompt = ""
            
            # Handle special commands
            if prompt.lower().strip() == 'status':
                response = self.controller.get_system_status()
            elif prompt.lower().strip() == 'help':
                response = self._get_help_message()
            else:
                # Send message to the multi-agent controller
                response = await self.controller.send_message(prompt)
                
                # Add state context to response
                state_info = self.controller.get_current_state_info()
                current_state = state_info['current_state']
                
                response = f"""🤖 **{current_state}** Response:

{response}

---
📊 **Current State**: {current_state} (State-{state_info['current_state_number']})
🎯 **Next**: {', '.join(state_info['next_states']) if state_info['next_states'] else 'Complete'}
💡 **Tip**: Type 'status' for full system information
"""
                
        except Exception as e:
            error_state = self.controller.get_current_state_info()
            response = f"""❌ **Error in {error_state['current_state']}**

{str(e)}

🔧 **Troubleshooting:**
- Type 'status' to check system state
- Ensure all required services are running
- Try restarting with 'restart' command

📞 **Support**: Check the system logs for detailed error information."""

        yield Event(
            author="multi_agent_sdg_system",
            content=types.Content(
                role="assistant",
                parts=[types.Part.from_text(text=response)]
            )
        )
    
    def _get_help_message(self) -> str:
        """Generate comprehensive help message."""
        state_info = self.controller.get_current_state_info()
        
        help_message = f"""🤖 **Multi-Agent SDG System Help**

**Current State**: {state_info['current_state']} (State-{state_info['current_state_number']})
**Description**: {state_info['description']}

**System States:**
- 🌱 **State-1**: Seed Data Creation - Create structured seed data from requirements
- 🔄 **State-2**: Seed Data Iteration - Refine seed data based on feedback  
- ⚡ **State-3**: Data Generation - Generate synthetic training data
- 🎯 **State-4**: Close/Restart - Complete session or start over

**Commands:**
- `status` - Show current system state and information
- `help` - Show this help message

**Current State Actions:**
- **State-1**: Describe your data requirements
- **State-2**: Provide feedback on seed data or approve it
- **State-3**: Specify generation parameters (count, variation, format)
- **State-4**: Type 'restart' for new cycle or 'close' to end

**Completion Criteria**: {state_info['completion_criteria']}

**Flow**: State-1 → State-2 → State-3 → State-4 → State-1 (loop)

Ready to continue? I'm here to help with your synthetic data generation needs!"""

        return help_message


# Create the root agent that ADK Web will discover
root_agent = MultiAgentWebWrapper()