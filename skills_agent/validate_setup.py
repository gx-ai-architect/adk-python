#!/usr/bin/env python3
"""
Validation script for Multi-Agent Synthetic Data Generation System
Checks that all components are properly installed and configured.
"""

import sys
import os
import traceback
from pathlib import Path

def check_imports():
    """Check that all required modules can be imported."""
    print("🔍 Checking imports...")
    
    try:
        # Google ADK imports
        from google.adk.agents import LlmAgent
        from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
        from google.adk.models.lite_llm import LiteLlm
        from google.adk.runners import InMemoryRunner
        from google.adk.sessions import Session
        from google.genai import types
        print("✅ Google ADK imports successful")
        
        # Multi-agent system imports
        from mcp_agents import (
            StateManager, 
            SystemState, 
            MultiAgentController,
            seed_data_creator_agent,
            seed_data_iterator_agent,
            data_generator_agent,
            root_agent
        )
        print("✅ Multi-agent system imports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        traceback.print_exc()
        return False

def check_agents():
    """Check that agents are properly configured."""
    print("\n🤖 Checking agent configurations...")
    
    try:
        from mcp_agents import (
            seed_data_creator_agent,
            seed_data_iterator_agent, 
            data_generator_agent
        )
        
        agents = [
            ("Seed Data Creator", seed_data_creator_agent),
            ("Seed Data Iterator", seed_data_iterator_agent),
            ("Data Generator", data_generator_agent)
        ]
        
        for name, agent in agents:
            if hasattr(agent, 'name') and hasattr(agent, 'instruction') and hasattr(agent, 'tools'):
                print(f"✅ {name} agent configured correctly")
            else:
                print(f"❌ {name} agent missing required attributes")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Error checking agents: {e}")
        return False

def check_state_manager():
    """Check that state manager works correctly."""
    print("\n📊 Checking state manager...")
    
    try:
        from mcp_agents import StateManager, SystemState
        
        # Create temporary state manager
        temp_state_file = "temp_state_validation.json"
        state_manager = StateManager(temp_state_file)
        
        # Test basic functionality
        initial_state = state_manager.get_current_state()
        if initial_state == SystemState.SEED_DATA_CREATION:
            print("✅ State manager initializes correctly")
        else:
            print(f"❌ State manager initial state incorrect: {initial_state}")
            return False
            
        # Test state data
        state_manager.set_state_data("test_key", "test_value")
        if state_manager.get_state_data("test_key") == "test_value":
            print("✅ State data management working")
        else:
            print("❌ State data management failed")
            return False
            
        # Cleanup
        if os.path.exists(temp_state_file):
            os.remove(temp_state_file)
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking state manager: {e}")
        return False

def check_controller():
    """Check that multi-agent controller can be instantiated."""
    print("\n🎮 Checking multi-agent controller...")
    
    try:
        from mcp_agents import MultiAgentController
        
        controller = MultiAgentController("validation_test")
        
        # Check basic attributes
        if hasattr(controller, 'state_manager') and hasattr(controller, 'runners'):
            print("✅ Multi-agent controller instantiated correctly")
        else:
            print("❌ Multi-agent controller missing required attributes")
            return False
            
        # Check system status
        status = controller.get_system_status()
        if "Multi-Agent SDG System Status" in status:
            print("✅ Controller status reporting working")
        else:
            print("❌ Controller status reporting failed")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking controller: {e}")
        return False

def check_paths():
    """Check that required paths exist."""
    print("\n📁 Checking file paths...")
    
    paths_to_check = [
        "/Users/gxxu/Desktop/sdg-hub-folder/",
        "/Users/gxxu/Desktop/sdg-hub-folder/sdg-mcp-server/"
    ]
    
    all_paths_exist = True
    for path in paths_to_check:
        if os.path.exists(path):
            print(f"✅ Path exists: {path}")
        else:
            print(f"⚠️ Path not found: {path}")
            all_paths_exist = False
            
    if not all_paths_exist:
        print("⚠️ Some paths don't exist, but system may still work if paths are updated")
        
    return True  # Don't fail validation for path issues

def main():
    """Run all validation checks."""
    print("🚀 Multi-Agent SDG System Validation")
    print("=" * 50)
    
    checks = [
        check_imports,
        check_agents,
        check_state_manager,
        check_controller,
        check_paths
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All validation checks passed!")
        print("✅ Multi-agent system is ready to use")
        print("\nTo get started, run:")
        print("   python multi_agent_main.py")
    else:
        print("❌ Some validation checks failed")
        print("Please fix the issues above before using the system")
        
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 