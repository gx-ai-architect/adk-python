#!/usr/bin/env python3
"""
Test script for the MultiAgentWebWrapper
Verifies that the web wrapper correctly interfaces with the multi-agent system.
"""

import asyncio
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_web_wrapper():
    """Test the MultiAgentWebWrapper functionality."""
    print("🧪 Testing Multi-Agent Web Wrapper")
    print("=" * 50)
    
    try:
        # Import the web wrapper
        from multi_agent_web import root_agent
        print("✅ Successfully imported root_agent from multi_agent_web")
        
        # Test basic attributes
        print(f"✅ Agent name: {root_agent.name}")
        print(f"✅ Agent has controller: {hasattr(root_agent, 'controller')}")
        
        # Test status command
        print("\n🔍 Testing 'status' command:")
        status_response = await root_agent.run_async("status")
        print(f"📊 Status Response (first 200 chars): {status_response[:200]}...")
        
        # Test help command
        print("\n🔍 Testing 'help' command:")
        help_response = await root_agent.run_async("help")
        print(f"📚 Help Response (first 200 chars): {help_response[:200]}...")
        
        # Test regular message
        print("\n🔍 Testing regular message:")
        regular_response = await root_agent.run_async("I need help generating training data for a chatbot")
        print(f"💬 Regular Response (first 300 chars): {regular_response[:300]}...")
        
        print("\n✅ All tests passed! Web wrapper is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_adk_web_discovery():
    """Test that ADK web can discover the agent properly."""
    print("\n🔍 Testing ADK Web Discovery")
    print("=" * 50)
    
    try:
        # Simulate what ADK web does
        import importlib.util
        
        # Test loading from web_agent directory
        web_agent_path = os.path.join(os.path.dirname(__file__), 'web_agent', 'agent.py')
        
        if os.path.exists(web_agent_path):
            spec = importlib.util.spec_from_file_location("agent", web_agent_path)
            agent_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(agent_module)
            
            # Check if root_agent exists
            if hasattr(agent_module, 'root_agent'):
                print("✅ ADK Web can discover root_agent from web_agent/agent.py")
                print(f"✅ Discovered agent name: {agent_module.root_agent.name}")
                return True
            else:
                print("❌ No root_agent found in web_agent/agent.py")
                return False
        else:
            print(f"❌ web_agent/agent.py not found at {web_agent_path}")
            return False
            
    except Exception as e:
        print(f"❌ ADK Web discovery test failed: {str(e)}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Multi-Agent Web Wrapper Test Suite")
    print("=" * 60)
    
    # Run tests
    web_wrapper_test = await test_web_wrapper()
    discovery_test = await test_adk_web_discovery()
    
    print("\n" + "=" * 60)
    print("📋 **Test Results Summary**")
    print(f"🧪 Web Wrapper Test: {'✅ PASSED' if web_wrapper_test else '❌ FAILED'}")
    print(f"🔍 ADK Discovery Test: {'✅ PASSED' if discovery_test else '❌ FAILED'}")
    
    if web_wrapper_test and discovery_test:
        print("\n🎉 All tests passed! Ready for ADK Web!")
        print("\n📝 **Next Steps:**")
        print("1. cd web_agent")
        print("2. adk web")
        print("3. Open browser to http://localhost:8000")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 