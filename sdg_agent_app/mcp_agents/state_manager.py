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

import json
import os
from enum import Enum
from typing import Optional, Dict, Any
import asyncio


class SystemState(Enum):
    """System states for the synthetic data generation flow."""
    GREETING_INTENT = 0          # State 0 - Greeting & Intent Detection
    GENERAL_QA = 1               # State 1 - General Q&A
    KNOWLEDGE_FLOW = 2           # State 2 - Knowledge Flow (Placeholder)
    SKILLS_GREETING = 3          # State 3 - Skills Greeting
    SEED_DATA_CREATION = 4       # State 4 - Seed Data Creator (was State 1)
    DATA_GENERATION = 5          # State 5 - Data Generator (was State 3)
    REVIEW_EXIT = 6              # State 6 - Review & Exit


class StateManager:
    """Manages state transitions and persistence for the multi-agent system."""
    
    def __init__(self, state_file_path: str = "system_state.json", start_fresh: bool = False):
        self.state_file_path = state_file_path
        self.current_state = SystemState.GREETING_INTENT  # Start with greeting state
        self.state_data: Dict[str, Any] = {}
        
        if start_fresh:
            self.clear_saved_state()
        else:
            self._load_state()
    
    def _load_state(self):
        """Load state from file if it exists."""
        if os.path.exists(self.state_file_path):
            try:
                with open(self.state_file_path, 'r') as f:
                    data = json.load(f)
                    self.current_state = SystemState(data.get('current_state', 0))  # Default to greeting
                    self.state_data = data.get('state_data', {})
            except (json.JSONDecodeError, ValueError, KeyError):
                # If file is corrupted, start fresh
                self.current_state = SystemState.GREETING_INTENT
                self.state_data = {}
    
    def _save_state(self):
        """Save current state to file."""
        data = {
            'current_state': self.current_state.value,
            'state_data': self.state_data
        }
        with open(self.state_file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_current_state(self) -> SystemState:
        """Get the current system state."""
        return self.current_state
    
    def set_state_data(self, key: str, value: Any):
        """Set data for the current state."""
        self.state_data[key] = value
        self._save_state()
    
    def get_state_data(self, key: str, default: Any = None) -> Any:
        """Get data for the current state."""
        return self.state_data.get(key, default)
    
    def can_transition_to(self, target_state: SystemState) -> bool:
        """Check if transition to target state is allowed."""
        transitions = {
            SystemState.GREETING_INTENT: [SystemState.GENERAL_QA, SystemState.KNOWLEDGE_FLOW, SystemState.SKILLS_GREETING],
            SystemState.GENERAL_QA: [SystemState.GREETING_INTENT],
            SystemState.KNOWLEDGE_FLOW: [SystemState.GREETING_INTENT],
            SystemState.SKILLS_GREETING: [SystemState.SEED_DATA_CREATION, SystemState.DATA_GENERATION, SystemState.GREETING_INTENT],
            SystemState.SEED_DATA_CREATION: [SystemState.DATA_GENERATION, SystemState.GREETING_INTENT],
            SystemState.DATA_GENERATION: [SystemState.REVIEW_EXIT, SystemState.GREETING_INTENT],
            SystemState.REVIEW_EXIT: [SystemState.SEED_DATA_CREATION, SystemState.GREETING_INTENT]
        }
        return target_state in transitions.get(self.current_state, [])
    
    def transition_to(self, target_state: SystemState, clear_data: bool = False) -> bool:
        """Transition to a new state if allowed."""
        if not self.can_transition_to(target_state):
            return False
        
        self.current_state = target_state
        if clear_data:
            self.state_data = {}
        self._save_state()
        return True
    
    def validate_state_completion(self) -> bool:
        """Validate that current state completion criteria are met based on interactions."""
        # Simplified validation - routing agent handles most transitions
        
        if self.current_state == SystemState.SEED_DATA_CREATION:
            # Check if agent has indicated completion
            return self.get_state_data('agent_completed', False)
        
        elif self.current_state == SystemState.DATA_GENERATION:
            # Check if agent has indicated generation completion
            return self.get_state_data('agent_completed', False)
        
        # For all other states, always allow routing agent to handle transitions
        return True
    
    def mark_agent_completion(self):
        """Mark that the current agent has completed its task."""
        self.set_state_data('agent_completed', True)
    
    def mark_user_approval(self):
        """Mark that the user has approved the current state."""
        self.set_state_data('user_approved', True)
    
    def reset_to_initial_state(self):
        """Reset system to initial state."""
        self.current_state = SystemState.GREETING_INTENT
        self.state_data = {}
        self._save_state()
    
    def get_next_valid_states(self) -> list[SystemState]:
        """Get list of valid next states from current state."""
        transitions = {
            SystemState.GREETING_INTENT: [SystemState.GENERAL_QA, SystemState.KNOWLEDGE_FLOW, SystemState.SKILLS_GREETING],
            SystemState.GENERAL_QA: [SystemState.GREETING_INTENT],
            SystemState.KNOWLEDGE_FLOW: [SystemState.GREETING_INTENT],
            SystemState.SKILLS_GREETING: [SystemState.SEED_DATA_CREATION, SystemState.DATA_GENERATION],
            SystemState.SEED_DATA_CREATION: [SystemState.DATA_GENERATION],
            SystemState.DATA_GENERATION: [SystemState.REVIEW_EXIT],
            SystemState.REVIEW_EXIT: [SystemState.SEED_DATA_CREATION, SystemState.GREETING_INTENT]
        }
        return transitions.get(self.current_state, [])
    
    def clear_saved_state(self):
        """Delete the saved state file to start completely fresh."""
        if os.path.exists(self.state_file_path):
            try:
                os.remove(self.state_file_path)
                print(f"🗑️  Cleared previous state file: {self.state_file_path}")
            except Exception as e:
                print(f"⚠️  Could not delete state file: {e}")
        
        # Reset to initial state
        self.current_state = SystemState.GREETING_INTENT
        self.state_data = {}
    
    def force_fresh_start(self):
        """Force a completely fresh start by clearing all state."""
        self.clear_saved_state()
        self._save_state()  # Save the fresh state 
