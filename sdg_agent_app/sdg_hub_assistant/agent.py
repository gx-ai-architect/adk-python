from typing import Any, AsyncGenerator
from pydantic import Field, PrivateAttr
from google.adk.agents import LlmAgent
from google.adk.events.event import Event
from google.genai import types
from .multi_agent_controller import MultiAgentController


ROOT_FOLDER_PATH = "/Users/gxxu/Desktop/sdg-hub-folder/"


class MultiAgentWebWrapper(LlmAgent):
    """Wrapper that makes MultiAgentController compatible with ADK Web interface."""
    
    # Use PrivateAttr since this is an internal implementation detail
    _controller: MultiAgentController = PrivateAttr()
    name: str = Field(default="sdg_hub_assistant")
    
    def __init__(self):
        super().__init__()
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
"""
                
        except Exception as e:
            error_state = self.controller.get_current_state_info()
            response = f"""❌ **Error in {error_state['current_state']}**

{str(e)}

🔧 **Troubleshooting:**
- Check the system logs for detailed error information
- Try restarting the conversation

📞 **Support**: Contact system administrator if the issue persists."""

        yield Event(
            author="multi_agent_sdg_system",
            content=types.Content(
                role="assistant",
                parts=[types.Part.from_text(text=response)]
            )
        )
    

# Create the root agent that ADK Web will discover
root_agent = MultiAgentWebWrapper()