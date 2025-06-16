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
import time
from dotenv import load_dotenv
from google.adk.cli.utils import logs
from mcp_agents import MultiAgentController, SystemState

load_dotenv(override=True)
logs.log_to_tmp_folder()


async def interactive_session():
    """Run an interactive session with the multi-agent system."""
    print("🚀 **Multi-Agent Synthetic Data Generation System**")
    print("=" * 60)
    
    controller = MultiAgentController()
    
    # Display initial system status
    print(controller.get_system_status())
    print("\n" + "=" * 60)
    print("💬 **Interactive Session Started**")
    print("Type 'status' to see current state")
    print("Type 'exit' to quit the session")
    print("=" * 60)
    
    while True:
        try:
            # Get user input
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'status':
                print(controller.get_system_status())
                continue
            elif user_input.lower() == 'help':
                print_help()
                continue
            elif not user_input:
                print("⚠️ Please enter a message.")
                continue
            
            # Send message to current agent
            print("🤖 Processing...")
            start_time = time.time()
            
            response = await controller.send_message(user_input)
            
            end_time = time.time()
            print(f"\n🤖 Agent: {response}")
            print(f"\n⏱️ Response Time: {end_time - start_time:.2f}s")
            
        except KeyboardInterrupt:
            print("\n👋 Session interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Type 'status' to check system state or 'exit' to quit.")


def print_help():
    """Print help information."""
    help_text = """
🤖 **Multi-Agent SDG System Help**

**System States:**
- State-0: Greeting & Intent Detection - Welcome users and route to appropriate function
- State-1: General Q&A - Answer questions about SDG Hub and InstructLab
- State-2: Knowledge Flow - Handle knowledge data requests (placeholder)
- State-3: Skills Greeting - Explain skills data and determine starting point
- State-4: Seed Data Creator - Create structured seed data from requirements
- State-5: Data Generator - Generate synthetic training data
- State-6: Review & Exit - Review results and choose next steps

**Commands:**
- 'status' - Show current system state and information
- 'help' - Show this help message
- 'exit' or 'quit' - End the session

**State-Specific Actions:**
- State-0: Choose from General Q&A, Skills Data Generation, or Knowledge Data
- State-1: Ask questions about SDG Hub, InstructLab, or synthetic data generation
- State-2: Acknowledge that knowledge data is not yet supported
- State-3: Indicate whether you have seed data or need to create it
- State-4: Describe your data requirements and approve seed data
- State-5: Specify generation parameters and review progress
- State-6: Accept results, request changes, or return to main menu

**Flow:** State-0 → (State-1|State-2|State-3) → State-4 → State-5 → State-6 → (State-0|State-4)
"""
    print(help_text)


async def demo_session():
    """Run a demonstration session with predefined prompts."""
    print("🎭 **Demo Session: Multi-Agent SDG System**")
    print("=" * 60)
    
    controller = MultiAgentController()
    
    demo_prompts = [
        "Hello! I'd like to generate skills data for training.",
        "I don't have seed data yet, I need to create it.",
        "I need to generate training data for a customer service chatbot. The chatbot should help customers with order inquiries and tracking.",
        "That looks good, I approve this seed data.",
        "Generate 5 examples with medium variation in JSONL format.",
        "That looks great! I accept these results."
    ]
    
    print(controller.get_system_status())
    print("\n" + "=" * 60)
    
    for i, prompt in enumerate(demo_prompts, 1):
        print(f"\n**Demo Step {i}:**")
        print(f"👤 User: {prompt}")
        print("🤖 Processing...")
        
        start_time = time.time()
        response = await controller.send_message(prompt)
        end_time = time.time()
        
        print(f"🤖 Agent: {response}")
        print(f"⏱️ Time: {end_time - start_time:.2f}s")
        print("-" * 40)
        
        # Small delay for readability
        await asyncio.sleep(2)
    
    print("\n🎭 **Demo Complete**")


async def main():
    """Main function with session choice."""
    print("🚀 **Multi-Agent Synthetic Data Generation System**")
    print("Choose session type:")
    print("1. Interactive Session")
    print("2. Demo Session")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        await interactive_session()
    elif choice == "2":
        await demo_session()
    else:
        print("Invalid choice. Starting interactive session by default.")
        await interactive_session()


if __name__ == '__main__':
    asyncio.run(main()) 