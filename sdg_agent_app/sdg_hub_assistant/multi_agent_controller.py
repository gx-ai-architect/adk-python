import asyncio
from typing import Dict, Any, Optional, TextIO, List
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.sessions import Session
from google.genai import types
from google.adk.tools.mcp_tool.mcp_session_manager import StdioServerParameters, SseServerParams
import os
import sys
import json
from dataclasses import dataclass
from datetime import datetime

from .state_manager import StateManager, SystemState
from .routing_agent import routing_agent
from .agents import (
    greeting_agent,
    general_qa_agent,
    knowledge_flow_agent,
    skills_greeting_agent,
    seed_data_creator_agent,
    data_generator_agent,
    review_exit_agent
)


@dataclass
class ConversationTurn:
    """Represents a single conversation turn between user and agent."""
    timestamp: str
    user_message: str
    agent_response: str
    agent_name: str
    state_name: str


class MultiAgentController:
    """Controls the multi-agent synthetic data generation system."""
    
    def __init__(self, app_name: str = 'sdg_multi_agent_system', start_fresh: bool = True, 
                 conversation_history_limit: int = 8, *, errlog: TextIO = sys.stderr):
        self.app_name = app_name
        # Force a fresh start by default to avoid state persistence issues
        self.state_manager = StateManager(start_fresh=start_fresh)
        
        # Simple conversation history tracking - make these explicit public attributes
        self.conversation_history: List[ConversationTurn] = []
        self.conversation_history_limit: int = conversation_history_limit
        
        # Initialize runners for each agent (without complex memory services)
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
        print(f"💬 Conversation history limit: {self.conversation_history_limit} turns")
    
    @property
    def context_history(self) -> List[ConversationTurn]:
        """Get the conversation history as a public attribute."""
        return self.conversation_history
    
    @property
    def context_history_limit(self) -> int:
        """Get the conversation history limit as a public attribute."""
        return self.conversation_history_limit
    
    @context_history_limit.setter
    def context_history_limit(self, value: int):
        """Set the conversation history limit."""
        if value < 1:
            raise ValueError("Context history limit must be at least 1")
        self.conversation_history_limit = value
        print(f"💬 Updated conversation history limit to {value} turns")

    def _debug_print_conversation_history(self, agent_name: str):
        """Debug function to print conversation history that will be sent to the agent."""
        print(f"\n💬 [CONVERSATION DEBUG] Agent '{agent_name}' will see:")
        print("=" * 60)
        
        if not self.conversation_history:
            print("   📭 No conversation history")
        else:
            recent_history = self.conversation_history[-self.conversation_history_limit:]
            print(f"   📚 Last {len(recent_history)} conversation turns (limit: {self.conversation_history_limit}):")
            
            for i, turn in enumerate(recent_history, 1):
                print(f"   {i:2d}. [{turn.timestamp}] {turn.state_name}")
                user_msg = turn.user_message[:80] + "..." if len(turn.user_message) > 80 else turn.user_message
                agent_msg = turn.agent_response[:80] + "..." if len(turn.agent_response) > 80 else turn.agent_response
                print(f"       User: {user_msg}")
                print(f"       {turn.agent_name}: {agent_msg}")
                print()
        
        print("=" * 60)
        print()

    def _build_conversation_context(self, current_user_message: str) -> str:
        """Build conversation context from recent history to prepend to current message."""
        if not self.conversation_history:
            return current_user_message
        
        recent_history = self.conversation_history[-self.conversation_history_limit:]
        
        context_parts = ["Previous conversation context:"]
        for turn in recent_history:
            context_parts.append(f"User: {turn.user_message}")
            context_parts.append(f"Assistant ({turn.agent_name}): {turn.agent_response}")
        
        context_parts.append("Current message:")
        context_parts.append(f"User: {current_user_message}")
        
        return "\n".join(context_parts)

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
        
        # Debug: Show what conversation history this agent will see
        self._debug_print_conversation_history(f"{current_state.name}_agent")
        
        return session
    
    async def send_message(self, message: str) -> str:
        """Send a message to the current state's agent."""
        # Check if state transition is needed
        await self._check_state_transition(message)
        current_state = self.state_manager.get_current_state()
        
        # Check for global restart command first (available from any state)
        if message.lower().strip() in ['restart', 'reset', 'start over', 'fresh start']:
            self.state_manager.force_fresh_start()
            self.current_session = None  # Reset session
            self.conversation_history.clear()  # Clear conversation history
            return ("🔄 **System Reset Complete**\n\n"
                   "Returned to **State 0: Greeting & Intent Detection**\n\n"
                   "All previous state has been cleared. Ready to start fresh.\n"
                   "What would you like to do today?")
        
        if not self.current_session:
            await self.initialize_session()
        
        runner = self.runners[current_state]
        
        # Build message with conversation context
        contextual_message = self._build_conversation_context(message)
        
        content = types.Content(
            role='user', 
            parts=[types.Part.from_text(text=contextual_message)]
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
        
        # Save this conversation turn to history
        self._save_conversation_turn(message, full_response, current_state)
        
        return full_response
    
    def _save_conversation_turn(self, user_message: str, agent_response: str, state: SystemState):
        """Save a conversation turn to the history."""
        turn = ConversationTurn(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_message=user_message,
            agent_response=agent_response,
            agent_name=f"{state.name}_agent",
            state_name=state.name
        )
        
        self.conversation_history.append(turn)
        print(f"💾 Saved conversation turn (total: {len(self.conversation_history)} turns)")
        
        # Keep only recent history to prevent unlimited growth
        if len(self.conversation_history) > self.conversation_history_limit * 2:
            # Keep double the limit to have some buffer
            self.conversation_history = self.conversation_history[-self.conversation_history_limit * 2:]
            print(f"🗂️ Trimmed conversation history to {len(self.conversation_history)} turns")

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
                                # Reset session for new agent (conversation history is preserved)
                                self.current_session = None
                                # Clear completion flags for the new state
                                self.state_manager.set_state_data('agent_completed', False)
                                self.state_manager.set_state_data('user_approved', False)
                                print(f"🔄 **State Transition**: {current_state.name} → {target_state.name}")
                                
                                # Initialize new session and explicitly pass context
                                await self.initialize_session()
                                await self.pass_context_to_new_agent(target_state)
                                
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
                        # Reset session for new agent (conversation history is preserved)
                        self.current_session = None
                        # Clear completion flags for the new state
                        self.state_manager.set_state_data('agent_completed', False)
                        self.state_manager.set_state_data('user_approved', False)
                        print(f"🔄 **State Transition**: {current_state.name} → {target_state.name}")
                        
                        # Initialize new session and explicitly pass context
                        await self.initialize_session()
                        await self.pass_context_to_new_agent(target_state)
                        
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
            
            # Build conversation context for routing agent
            context_for_routing = self._build_conversation_context(user_message)
            
            # Create routing prompt with current context
            legal_state_names = [state.name for state in legal_states]
            routing_prompt = f"""
Current State: {current_state.name}
Legal Next States: {', '.join(legal_state_names)}

{context_for_routing}

Analyze the user's intent and respond with a JSON object containing the target state keyword.
Only choose from the legal next states listed above, or use "STAY" if no transition is appropriate.
"""
            
            print(f"🔍 Routing Debug - Current: {current_state.name}, Legal: {legal_state_names}")
            print(f"🔍 User Message: {user_message}")
            print(f"🔍 Context passed to routing agent: {len(context_for_routing)} characters")
            
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
    
    async def pass_context_to_new_agent(self, new_state: SystemState) -> bool:
        """Explicitly pass conversation context to a new agent after state transition."""
        if not self.conversation_history:
            print(f"🔄 No context to pass to {new_state.name} agent")
            return True
        
        if not self.current_session:
            print(f"⚠️ No active session for {new_state.name} agent")
            return False
        
        # Build context message for the new agent
        recent_history = self.conversation_history[-min(3, len(self.conversation_history)):]
        
        context_parts = [
            f"[SYSTEM CONTEXT] You are now handling the conversation in {new_state.name} state.",
            f"[SYSTEM CONTEXT] Here is the recent conversation context:",
            ""
        ]
        
        for turn in recent_history:
            context_parts.append(f"User: {turn.user_message}")
            context_parts.append(f"Previous Agent ({turn.agent_name}): {turn.agent_response}")
            context_parts.append("")
        
        context_parts.append("[SYSTEM CONTEXT] Please continue the conversation based on this context.")
        context_message = "\n".join(context_parts)
        
        try:
            print(f"🔄 Explicitly passing context to {new_state.name} agent ({len(context_message)} chars)")
            
            runner = self.runners[new_state]
            context_content = types.Content(
                role='user',
                parts=[types.Part.from_text(text=context_message)]
            )
            
            # Send context and consume response (don't save it as conversation turn)
            async for event in runner.run_async(
                user_id=self.user_id,
                session_id=self.current_session.id,
                new_message=context_content,
            ):
                pass  # We just want to establish context, not save the response
            
            print(f"✅ Context successfully passed to {new_state.name} agent")
            return True
            
        except Exception as e:
            print(f"⚠️ Failed to pass context to {new_state.name} agent: {e}")
            return False 

    def debug_context_passing(self) -> str:
        """Debug method to inspect context passing state."""
        current_state = self.state_manager.get_current_state()
        
        debug_info = [
            "=== CONTEXT PASSING DEBUG ===",
            f"Current State: {current_state.name}",
            f"Active Session: {self.current_session is not None}",
            f"Routing Session: {self.routing_session is not None}",
            f"Conversation History Length: {len(self.conversation_history)}",
            f"History Limit: {self.conversation_history_limit}",
            ""
        ]
        
        if self.conversation_history:
            debug_info.append("Last 2 conversation turns:")
            recent = self.conversation_history[-2:]
            for i, turn in enumerate(recent, 1):
                debug_info.append(f"  {i}. {turn.state_name} - {turn.timestamp}")
                debug_info.append(f"     User: {turn.user_message[:50]}...")
                debug_info.append(f"     Agent: {turn.agent_response[:50]}...")
        else:
            debug_info.append("No conversation history")
        
        return "\n".join(debug_info) 