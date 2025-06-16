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
from typing import Dict, Any, Optional, TextIO
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.sessions import Session
from google.genai import types
from google.adk.tools.mcp_tool.mcp_session_manager import StdioServerParameters, SseServerParams
import os
import sys

from .state_manager import StateManager, SystemState
from .routing_agent import routing_agent
from .greeting_agent import greeting_agent
from .general_qa_agent import general_qa_agent
from .knowledge_flow_agent import knowledge_flow_agent
from .skills_greeting_agent import skills_greeting_agent
from .seed_data_creator import seed_data_creator_agent
from .data_generator import data_generator_agent
from .review_exit_agent import review_exit_agent


class MultiAgentController:
    """Controls the multi-agent synthetic data generation system."""
    
    def __init__(self, app_name: str = 'sdg_multi_agent_system', start_fresh: bool = True, *, errlog: TextIO = sys.stderr):
        self.app_name = app_name
        # Force a fresh start by default to avoid state persistence issues
        self.state_manager = StateManager(start_fresh=start_fresh)
        
        # Initialize runners for each agent
        self.runners = {
            SystemState.GREETING_INTENT: InMemoryRunner(
                agent=greeting_agent,
                app_name=f"{app_name}_greeting"
            ),
            SystemState.GENERAL_QA: InMemoryRunner(
                agent=general_qa_agent,
                app_name=f"{app_name}_general_qa"
            ),
            SystemState.KNOWLEDGE_FLOW: InMemoryRunner(
                agent=knowledge_flow_agent,
                app_name=f"{app_name}_knowledge_flow"
            ),
            SystemState.SKILLS_GREETING: InMemoryRunner(
                agent=skills_greeting_agent,
                app_name=f"{app_name}_skills_greeting"
            ),
            SystemState.SEED_DATA_CREATION: InMemoryRunner(
                agent=seed_data_creator_agent,
                app_name=f"{app_name}_seed_creator"
            ),
            SystemState.DATA_GENERATION: InMemoryRunner(
                agent=data_generator_agent,
                app_name=f"{app_name}_data_generator"
            ),
            SystemState.REVIEW_EXIT: InMemoryRunner(
                agent=review_exit_agent,
                app_name=f"{app_name}_review_exit"
            )
        }
        
        # Initialize routing agent runner
        self.routing_runner = InMemoryRunner(
            agent=routing_agent,
            app_name=f"{app_name}_routing"
        )
        self.routing_session: Optional[Session] = None
        
        self.current_session: Optional[Session] = None
        self.user_id = 'default_user'
        
        # Stream to write warning / error logs (esp. MCP cleanup warnings)
        self._errlog = errlog
        
        print(f"🤖 Multi-Agent Controller initialized in {self.state_manager.get_current_state().name}")
    
    async def initialize_session(self) -> Session:
        """Initialize a session for the current state's agent."""
        current_state = self.state_manager.get_current_state()
        
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
                   "Returned to **State 0: Greeting & Intent Detection**\n\n"
                   "All previous state has been cleared. Ready to start fresh.\n"
                   "What would you like to do today?")
        
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
            if "exit cancel scope in a different task" not in str(e):
                print(f"Warning: Error during MCP session cleanup: {e}", file=self._errlog)
            print(f"🔧 General error during agent execution: {e}")
            # Provide a meaningful error message instead of crashing
            response_parts.append(f"I encountered an error while processing your request. Error: {str(e)}")
        
        full_response = '\n'.join(response_parts) if response_parts else "I'm sorry, I couldn't generate a response. Please try again."
        
        # Check if state transition is needed
        await self._check_state_transition(message)
        
        return full_response
    
    async def _check_state_transition(self, user_message: str):
        """Check if current state is complete and transition if needed using routing agent."""
        current_state = self.state_manager.get_current_state()
        
        print(f"🔍 Checking state transition from {current_state.name}")
        
        # Check completion criteria for current state
        completion_valid = self.state_manager.validate_state_completion()
        print(f"🔍 State completion valid: {completion_valid}")
        
        if completion_valid:
            next_states = self.state_manager.get_next_valid_states()
            print(f"🔍 Next valid states: {[s.name for s in next_states]}")
            
            if next_states:
                # Use routing agent to determine next state
                routing_decision = await self.get_routing_decision(user_message, current_state, next_states)
                print(f"🔍 Routing decision: {routing_decision}")
                
                if routing_decision != 'STAY':
                    # Find the target state
                    target_state = None
                    for state in next_states:
                        if state.name == routing_decision:
                            target_state = state
                            break
                    
                    print(f"🔍 Target state found: {target_state.name if target_state else 'None'}")
                    
                    if target_state:
                        can_transition = self.state_manager.can_transition_to(target_state)
                        print(f"🔍 Can transition to {target_state.name}: {can_transition}")
                        
                        if can_transition:
                            transition_success = self.state_manager.transition_to(target_state)
                            print(f"🔍 Transition success: {transition_success}")
                            
                            if transition_success:
                                # Reset session for new agent
                                self.current_session = None
                                # Clear completion flags for the new state
                                self.state_manager.set_state_data('agent_completed', False)
                                self.state_manager.set_state_data('user_approved', False)
                                print(f"🔄 **State Transition**: {current_state.name} → {target_state.name}")
                                return True
        
        # Also check for routing decisions even if state isn't "complete"
        # This allows navigation from any state (like "menu" commands)
        print(f"🔍 Checking global routing options...")
        all_possible_states = [
            SystemState.GREETING_INTENT,
            SystemState.GENERAL_QA,
            SystemState.KNOWLEDGE_FLOW,
            SystemState.SKILLS_GREETING,
            SystemState.SEED_DATA_CREATION,
            SystemState.DATA_GENERATION,
            SystemState.REVIEW_EXIT
        ]
        
        routing_decision = await self.get_routing_decision(user_message, current_state, all_possible_states)
        print(f"🔍 Global routing decision: {routing_decision}")
        
        if routing_decision != 'STAY':
            # Find the target state
            target_state = None
            for state in all_possible_states:
                if state.name == routing_decision:
                    target_state = state
                    break
            
            print(f"🔍 Global target state: {target_state.name if target_state else 'None'}")
            
            if target_state and target_state != current_state:
                can_transition = self.state_manager.can_transition_to(target_state)
                print(f"🔍 Global can transition: {can_transition}")
                
                if can_transition:
                    transition_success = self.state_manager.transition_to(target_state)
                    print(f"🔍 Global transition success: {transition_success}")
                    
                    if transition_success:
                        # Reset session for new agent
                        self.current_session = None
                        # Clear completion flags for the new state
                        self.state_manager.set_state_data('agent_completed', False)
                        self.state_manager.set_state_data('user_approved', False)
                        print(f"🔄 **State Transition**: {current_state.name} → {target_state.name}")
                        return True
        
        print(f"🔍 No state transition occurred")
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
            SystemState.GREETING_INTENT: "Welcome users and detect their intent for routing",
            SystemState.GENERAL_QA: "Answer questions about sdg_hub and InstructLab",
            SystemState.KNOWLEDGE_FLOW: "Handle knowledge data requests (placeholder)",
            SystemState.SKILLS_GREETING: "Explain skills data and determine user's starting point",
            SystemState.SEED_DATA_CREATION: "Create structured seed data JSONL file from user requirements",
            SystemState.DATA_GENERATION: "Generate synthetic training data using approved seed data",
            SystemState.REVIEW_EXIT: "Review generated data and handle user decisions"
        }
        return descriptions.get(state, "Unknown state")
    
    def _get_completion_criteria(self, state: SystemState) -> str:
        """Get completion criteria for a given state."""
        criteria = {
            SystemState.GREETING_INTENT: "User selects from available options (General Q&A, Skills, Knowledge)",
            SystemState.GENERAL_QA: "User indicates they want to return to main menu or are done",
            SystemState.KNOWLEDGE_FLOW: "User acknowledges the placeholder message",
            SystemState.SKILLS_GREETING: "User indicates whether they have seed data or need to create it",
            SystemState.SEED_DATA_CREATION: "Valid seed_data.jsonl file created and user approves",
            SystemState.DATA_GENERATION: "Synthetic data successfully generated and saved",
            SystemState.REVIEW_EXIT: "User chooses to accept, make changes, or return to menu"
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

**State Flow**: 
State-0 (Greeting) → State-1 (General Q&A) | State-2 (Knowledge) | State-3 (Skills Greeting)
State-3 → State-4 (Seed Data Creator) | State-5 (Data Generator)
State-4 → State-5 → State-6 (Review & Exit)
State-6 → State-4 (changes) | State-0 (menu)
"""
        return status.strip()
    
    async def _shutdown_current_runner(self):
        """Close the runner & session belonging to the *current* state."""
        state = self.state_manager.get_current_state()
        runner = self.runners.get(state)
        if runner:
            try:
                # delete the active session so no one tries to reuse it
                if self.current_session:
                    await runner.session_service.delete_session(
                        app_name=runner.app_name,
                        user_id=self.user_id,
                        session_id=self.current_session.id,
                    )
                await runner.close()          # <-- closes toolsets in-task
            except Exception as e:
                if "exit cancel scope in a different task" not in str(e):
                    print(f"Warning: Error during MCP session cleanup: {e}", file=self._errlog)
        self.current_session = None 
    
    async def initialize_routing_session(self) -> Session:
        """Initialize a session for the routing agent."""
        if not self.routing_session:
            self.routing_session = await self.routing_runner.session_service.create_session(
                app_name=self.routing_runner.app_name,
                user_id=self.user_id
            )
        return self.routing_session
    
    async def get_routing_decision(self, user_message: str, current_state: SystemState, legal_states: list[SystemState]) -> str:
        """Get routing decision from the routing agent."""
        try:
            await self.initialize_routing_session()
            
            # Create routing prompt with current context
            legal_state_names = [state.name for state in legal_states]
            routing_prompt = f"""
Current State: {current_state.name}
Legal Next States: {', '.join(legal_state_names)}
User Message: "{user_message}"

Analyze the user's intent and respond with a JSON object containing the target state keyword.
Only choose from the legal next states listed above, or use "STAY" if no transition is appropriate.
"""
            
            print(f"🔍 Routing Debug - Current: {current_state.name}, Legal: {legal_state_names}")
            print(f"🔍 User Message: {user_message}")
            
            content = types.Content(
                role='user',
                parts=[types.Part.from_text(text=routing_prompt)]
            )
            
            response_parts = []
            async for event in self.routing_runner.run_async(
                user_id=self.user_id,
                session_id=self.routing_session.id,
                new_message=content,
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_parts.append(part.text)
            
            routing_response = '\n'.join(response_parts)
            print(f"🔍 Routing Agent Response: {routing_response}")
            
            # Parse JSON response
            import json
            try:
                # Clean up the response - sometimes models add extra text
                routing_response_clean = routing_response.strip()
                if '```json' in routing_response_clean:
                    # Extract JSON from code block
                    start = routing_response_clean.find('{')
                    end = routing_response_clean.rfind('}') + 1
                    if start != -1 and end != 0:
                        routing_response_clean = routing_response_clean[start:end]
                
                routing_data = json.loads(routing_response_clean)
                target_state_name = routing_data.get('target_state', 'STAY')
                
                print(f"🔍 Parsed Target State: {target_state_name}")
                
                # Validate that the target state is legal
                if target_state_name == 'STAY':
                    return 'STAY'
                
                # Check if target state is in legal states
                for state in legal_states:
                    if state.name == target_state_name:
                        print(f"✅ Valid routing decision: {target_state_name}")
                        return target_state_name
                
                # If not found in legal states, log error and stay
                print(f"⚠️ Routing agent suggested invalid state: {target_state_name}")
                print(f"Legal states were: {legal_state_names}")
                return 'STAY'
                
            except json.JSONDecodeError as e:
                print(f"⚠️ Routing agent returned invalid JSON: {routing_response}")
                print(f"JSON Error: {e}")
                return 'STAY'
                
        except Exception as e:
            print(f"⚠️ Error in routing decision: {e}")
            return 'STAY' 