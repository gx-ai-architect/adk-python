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
            #     model="hosted_vllm/Qwen/Qwen2.5-7B-Instruct",
            #     api_base="http://localhost:8106/v1",
            # ),
            model=LiteLlm(model="openai/gpt-4o"), # LiteLLM model string format
            name='multi_agent_sdg_system',
            instruction='''🤖 **Multi-Agent Synthetic Data Generation System**

I am a multi-agent system that guides you through a structured workflow to generate synthetic training data:

**Available Functions:**
🔍 **General Q&A** - Ask questions about SDG Hub and InstructLab
🎯 **Skills Data Generation** - Create synthetic training data for skills
📚 **Knowledge Data** - (Coming soon - not yet supported)

**State Flow:**
State-0: Greeting & Intent Detection → Route to appropriate function
State-1: General Q&A ↔ State-0 (Main Menu)
State-2: Knowledge Flow (Placeholder) ↔ State-0 (Main Menu)
State-3: Skills Greeting → State-4 or State-5 (based on seed data availability)
State-4: Seed Data Creator → State-5: Data Generator → State-6: Review & Exit
State-6: Review & Exit → State-4 (changes) or State-0 (menu)

**How to Use:**
1. **Start**: System greets you and asks what you'd like to do
2. **Choose**: Select from General Q&A, Skills Data Generation, or Knowledge Data
3. **Skills Path**: If you choose skills, system asks if you have seed data
   - No seed data → Create seed data → Generate synthetic data → Review
   - Have seed data → Generate synthetic data → Review
4. **Complete**: Review results and choose next steps

**Special Commands (available from any state):**
- Type 'status' to see current state information
- Type 'help' for detailed guidance  
- Type 'restart' or 'reset' to start fresh from State-0

**Fresh Start:** The system starts fresh each session in State-0 (Greeting & Intent Detection).

Welcome! What would you like to do today?''',
            
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
- 👋 **State-0**: Greeting & Intent Detection - Welcome and route users
- 🔍 **State-1**: General Q&A - Answer questions about SDG Hub and InstructLab
- 📚 **State-2**: Knowledge Flow - Handle knowledge data requests (placeholder)
- 🎯 **State-3**: Skills Greeting - Explain skills data and determine starting point
- 🌱 **State-4**: Seed Data Creator - Create structured seed data from requirements
- ⚡ **State-5**: Data Generator - Generate synthetic training data
- 📊 **State-6**: Review & Exit - Review results and choose next steps

**Commands:**
- `status` - Show current system state and information
- `help` - Show this help message
- `restart` - Start fresh from State-0

**Current State Actions:**
- **State-0**: Choose from General Q&A, Skills Data Generation, or Knowledge Data
- **State-1**: Ask questions about SDG Hub, InstructLab, or synthetic data generation
- **State-2**: Acknowledge that knowledge data is not yet supported
- **State-3**: Indicate whether you have seed data or need to create it
- **State-4**: Describe your data requirements and approve seed data
- **State-5**: Specify generation parameters and review progress
- **State-6**: Accept results, request changes, or return to main menu

**Completion Criteria**: {state_info['completion_criteria']}

**Flow**: State-0 → (State-1|State-2|State-3) → State-4 → State-5 → State-6

Ready to continue? I'm here to help with your synthetic data generation needs!"""

        return help_message


# Create the root agent that ADK Web will discover
root_agent = MultiAgentWebWrapper()