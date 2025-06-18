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

import asyncio
from typing import Dict, Any, Optional
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.sessions import Session
from google.genai import types

from .state_manager import StateManager, SystemState
from .seed_data_creator import seed_data_creator_agent
from .seed_data_iterator import seed_data_iterator_agent
from .data_generator import data_generator_agent


class MultiAgentController:
    """Controls the multi-agent synthetic data generation system."""
    
    def __init__(self, app_name: str = 'sdg_multi_agent_system', start_fresh: bool = True):
        self.app_name = app_name
        # Force a fresh start by default to avoid state persistence issues
        self.state_manager = StateManager(start_fresh=start_fresh)
        
        # Initialize runners for each agent
        self.runners = {
            SystemState.SEED_DATA_CREATION: InMemoryRunner(
                agent=seed_data_creator_agent,
                app_name=f"{app_name}_seed_creator"
            ),
            SystemState.SEED_DATA_ITERATION: InMemoryRunner(
                agent=seed_data_iterator_agent,
                app_name=f"{app_name}_seed_iterator"
            ),
            SystemState.DATA_GENERATION: InMemoryRunner(
                agent=data_generator_agent,
                app_name=f"{app_name}_data_generator"
            )
        }
        
        self.current_session: Optional[Session] = None
        self.user_id = 'default_user'
        
        print(f"🤖 Multi-Agent Controller initialized in {self.state_manager.get_current_state().name}")
    
    async def initialize_session(self) -> Session:
        """Initialize a session for the current state's agent."""
        current_state = self.state_manager.get_current_state()
        
        if current_state == SystemState.CLOSE_RESTART:
            # Handle close/restart state
            return None
        
        runner = self.runners.get(current_state)
        if not runner:
            raise ValueError(f"No runner available for state: {current_state}")
        
        session = await runner.session_service.create_session(
            app_name=runner.app_name,
            user_id=self.user_id
        )
        
        self.current_session = session
        return session
    
    async def send_message(self, message: str) -> str:
        """Send a message to the current state's agent."""
        current_state = self.state_manager.get_current_state()
        
        # Check for global restart command first (available from any state)
        if message.lower().strip() in ['restart', 'reset', 'start over', 'fresh start']:
            self.state_manager.force_fresh_start()
            self.current_session = None  # Reset session
            return ("🔄 **System Reset Complete**\n\n"
                   "Returned to **State-1: Seed Data Creation**\n\n"
                   "All previous state has been cleared. Ready to create new seed data.\n"
                   "Please describe what kind of training data you need to generate.")
        
        if current_state == SystemState.CLOSE_RESTART:
            return self._handle_close_restart_state(message)
        
        # Check for user completion signals before sending to agent
        if self.state_manager.detect_completion_from_user_input(message):
            self.state_manager.mark_user_approval()
        
        if not self.current_session:
            await self.initialize_session()
        
        runner = self.runners[current_state]
        
        content = types.Content(
            role='user', 
            parts=[types.Part.from_text(text=message)]
        )
        
        # Use a more robust approach to handle async generator issues
        response_parts = []
        try:
            print(f"🔄 Processing message in state {current_state.name}: {message[:100]}...")
            
            events = []
            async for event in runner.run_async(
                user_id=self.user_id,
                session_id=self.current_session.id,
                new_message=content,
            ):
                events.append(event)
                # Extract text immediately to avoid context issues
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_parts.append(part.text)
        except ValueError as e:
            if "is not found in the tools_dict" in str(e):
                print(f"🔧 Tool lookup error: {e}")
                response_parts.append(
                    f"I encountered a configuration issue with the tools. "
                    f"Error: {str(e)}\n\n"
                    f"This might be a temporary issue. Please try rephrasing your request "
                    f"or type 'restart' to start fresh."
                )
            else:
                print(f"🔧 Value error during agent execution: {e}")
                response_parts.append(f"I encountered an error while processing your request. Error: {str(e)}")
        except Exception as e:
            print(f"🔧 General error during agent execution: {e}")
            # Provide a meaningful error message instead of crashing
            response_parts.append(f"I encountered an error while processing your request. Error: {str(e)}")
        
        full_response = '\n'.join(response_parts) if response_parts else "I'm sorry, I couldn't generate a response. Please try again."
        
        # Check for agent completion signals in the response
        if self.state_manager.detect_completion_from_response(message): # detect completion indication from user input 
            self.state_manager.mark_agent_completion()
        
        # Check if state transition is needed
        await self._check_state_transition()
        
        return full_response
    
    def _handle_close_restart_state(self, message: str) -> str:
        """Handle messages in the close/restart state."""
        message_lower = message.lower().strip()
        
        if any(keyword in message_lower for keyword in ['restart', 'start over', 'new', 'begin']):
            # Reset to initial state
            self.state_manager.reset_to_initial_state()
            self.current_session = None
            return ("🔄 **System Reset Complete**\n\n"
                   "Returning to **State-1: Seed Data Creation**\n\n"
                   "Ready to create new seed data. Please describe your data requirements.")
        
        elif any(keyword in message_lower for keyword in ['close', 'exit', 'quit', 'done']):
            return ("👋 **Session Closed**\n\n"
                   "Thank you for using the Synthetic Data Generation system!\n"
                   "Session has been terminated.")
        
        else:
            return ("🔄 **State-4: Close/Restart**\n\n"
                   "Data generation is complete! Choose your next action:\n"
                   "- Type 'restart' or 'start over' to begin a new generation cycle\n"
                   "- Type 'close' or 'exit' to end the session\n\n"
                   f"Current message: {message}")
    
    async def _check_state_transition(self):
        """Check if current state is complete and transition if needed."""
        current_state = self.state_manager.get_current_state()
        
        # Check completion criteria for current state
        if self.state_manager.validate_state_completion():
            next_states = self.state_manager.get_next_valid_states()
            if next_states:
                next_state = next_states[0]  # Take the primary next state
                if self.state_manager.transition_to(next_state):
                    # Reset session for new agent
                    self.current_session = None
                    # Clear completion flags for the new state
                    self.state_manager.set_state_data('agent_completed', False)
                    self.state_manager.set_state_data('user_approved', False)
                    print(f"🔄 **State Transition**: {current_state.name} → {next_state.name}")
                    return True
        return False
    
    def get_current_state_info(self) -> Dict[str, Any]:
        """Get information about the current state."""
        current_state = self.state_manager.get_current_state()
        
        state_info = {
            "current_state": current_state.name,
            "current_state_number": current_state.value,
            "description": self._get_state_description(current_state),
            "next_states": [s.name for s in self.state_manager.get_next_valid_states()],
            "completion_criteria": self._get_completion_criteria(current_state),
            "state_data": self.state_manager.state_data
        }
        
        return state_info
    
    def _get_state_description(self, state: SystemState) -> str:
        """Get description for a given state."""
        descriptions = {
            SystemState.SEED_DATA_CREATION: "Create structured seed data JSON file from user requirements",
            SystemState.SEED_DATA_ITERATION: "Refine seed data based on user feedback and iterations",
            SystemState.DATA_GENERATION: "Generate synthetic training data using approved seed data",
            SystemState.CLOSE_RESTART: "Session complete - choose to restart or close"
        }
        return descriptions.get(state, "Unknown state")
    
    def _get_completion_criteria(self, state: SystemState) -> str:
        """Get completion criteria for a given state."""
        criteria = {
            SystemState.SEED_DATA_CREATION: "Valid seed_data.json file created with all required fields",
            SystemState.SEED_DATA_ITERATION: "User approval received OR maximum iterations (3) reached",
            SystemState.DATA_GENERATION: "Synthetic data successfully generated and saved",
            SystemState.CLOSE_RESTART: "User chooses to restart or close session"
        }
        return criteria.get(state, "Unknown criteria")
    
    async def force_state_transition(self, target_state: SystemState) -> bool:
        """Force transition to a specific state (admin function)."""
        if self.state_manager.transition_to(target_state):
            self.current_session = None
            return True
        return False
    
    def get_system_status(self) -> str:
        """Get a formatted system status message."""
        state_info = self.get_current_state_info()
        
        status = f"""
🤖 **Multi-Agent SDG System Status**

**Current State**: {state_info['current_state']} (State-{state_info['current_state_number']})
**Description**: {state_info['description']}
**Completion Criteria**: {state_info['completion_criteria']}
**Next States**: {', '.join(state_info['next_states']) if state_info['next_states'] else 'None'}

**State Flow**: State-1 → State-2 → State-3 → State-4 → State-1 (loop)
"""
        return status.strip() 