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
import re


class SystemState(Enum):
    """System states for the synthetic data generation flow."""
    SEED_DATA_CREATION = 1
    SEED_DATA_ITERATION = 2
    DATA_GENERATION = 3
    CLOSE_RESTART = 4


class StateManager:
    """Manages state transitions and persistence for the multi-agent system."""
    
    def __init__(self, state_file_path: str = "system_state.json", start_fresh: bool = False):
        self.state_file_path = state_file_path
        self.current_state = SystemState.SEED_DATA_CREATION
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
                    self.current_state = SystemState(data.get('current_state', 1))
                    self.state_data = data.get('state_data', {})
            except (json.JSONDecodeError, ValueError, KeyError):
                # If file is corrupted, start fresh
                self.current_state = SystemState.SEED_DATA_CREATION
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
            SystemState.SEED_DATA_CREATION: [SystemState.SEED_DATA_ITERATION],
            SystemState.SEED_DATA_ITERATION: [SystemState.DATA_GENERATION, SystemState.SEED_DATA_ITERATION],
            SystemState.DATA_GENERATION: [SystemState.CLOSE_RESTART],
            SystemState.CLOSE_RESTART: [SystemState.SEED_DATA_CREATION]
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
    
    def detect_completion_from_response(self, user_input: str) -> bool:
        """Detect if the current state is complete based on user input patterns."""
        user_input = user_input.lower()
        
        if self.current_state == SystemState.SEED_DATA_CREATION:
            # Look for user indicating seed data is ready
            completion_patterns = [
                r"(?:yes|looks? good|proceed|continue|next)",
                r"seed data (?:is )?ready",
                r"move to (?:next|iteration)",
                r"start iterating",
                r"next step",
                r"next state",
                r"next stage"
            ]
            return any(re.search(pattern, user_input) for pattern in completion_patterns)
        
        elif self.current_state == SystemState.SEED_DATA_ITERATION:
            # Look for user approval to move to data generation
            completion_patterns = [
                r"(?:yes|approved|accept|good|ok|proceed)",
                r"ready to generate",
                r"start generation",
                r"move to generation",
                r"next step",
                r"next state",
                r"next stage"
            ]
            rejection_patterns = [
                r"(?:no|not yet|wait|hold|stop)",
                r"needs? (?:more|changes|work)",
                r"not (?:good|ready)",
            ]
            has_approval = any(re.search(pattern, user_input) for pattern in completion_patterns)
            has_rejection = any(re.search(pattern, user_input) for pattern in rejection_patterns)
            return has_approval and not has_rejection
        
        elif self.current_state == SystemState.DATA_GENERATION:
            # Look for user confirming generation is complete
            completion_patterns = [
                r"looks? good",
                r"that's enough",
                r"next step",
                r"next stage",
                r"next state",
            ]
            return any(re.search(pattern, user_input) for pattern in completion_patterns)
        
        return False
    
    def detect_completion_from_user_input(self, user_message: str) -> bool:
        """Detect completion signals from user input."""
        if self.current_state == SystemState.SEED_DATA_ITERATION:
            # Look for user approval/acceptance
            approval_patterns = [
                r"(?:yes|approve|accept|good|ok|proceed)",
                r"looks?\s+good",
                r"that.s?\s+(?:fine|good|perfect|great)",
                r"ready.*(?:to.*)?(?:proceed|continue|generate)",
                r"move.*(?:to.*)?next"
            ]
            rejection_patterns = [
                r"(?:no|reject|change|modify|improve|fix)",
                r"not\s+(?:good|right|correct)",
                r"needs?\s+(?:change|improvement|fix)"
            ]
            
            user_lower = user_message.lower()
            has_approval = any(re.search(pattern, user_lower) for pattern in approval_patterns)
            has_rejection = any(re.search(pattern, user_lower) for pattern in rejection_patterns)
            
            return has_approval and not has_rejection
        
        return False
    
    def validate_state_completion(self) -> bool:
        """Validate that current state completion criteria are met based on interactions."""
        if self.current_state == SystemState.SEED_DATA_CREATION:
            # Check if agent has indicated completion
            return self.get_state_data('agent_completed', False)
        
        elif self.current_state == SystemState.SEED_DATA_ITERATION:
            # Check if user has approved or max iterations reached
            return (self.get_state_data('user_approved', False) or 
                   self.get_state_data('agent_completed', False) or
                   self.get_state_data('iteration_count', 0) >= self.get_state_data('max_iterations', 3))
        
        elif self.current_state == SystemState.DATA_GENERATION:
            # Check if agent has indicated generation completion
            return self.get_state_data('agent_completed', False)
        
        return True
    
    def mark_agent_completion(self):
        """Mark that the current agent has completed its task."""
        self.set_state_data('agent_completed', True)
    
    def mark_user_approval(self):
        """Mark that the user has approved the current state."""
        self.set_state_data('user_approved', True)
    
    def reset_to_initial_state(self):
        """Reset system to initial state."""
        self.current_state = SystemState.SEED_DATA_CREATION
        self.state_data = {}
        self._save_state()
    
    def get_next_valid_states(self) -> list[SystemState]:
        """Get list of valid next states from current state."""
        transitions = {
            SystemState.SEED_DATA_CREATION: [SystemState.SEED_DATA_ITERATION],
            SystemState.SEED_DATA_ITERATION: [SystemState.DATA_GENERATION],
            SystemState.DATA_GENERATION: [SystemState.CLOSE_RESTART],
            SystemState.CLOSE_RESTART: [SystemState.SEED_DATA_CREATION]
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
        self.current_state = SystemState.SEED_DATA_CREATION
        self.state_data = {}
    
    def force_fresh_start(self):
        """Force a completely fresh start by clearing all state."""
        self.clear_saved_state()
        self._save_state()  # Save the fresh state 
