from google.adk.models.lite_llm import LiteLlm
from litellm import completion

model = LiteLlm(
    model="hosted_vllm/meta-llama/Llama-3.3-70B-Instruct",
    api_base="http://localhost:8100/v1",     # omit if you used env‑vars
    # extra_headers={"Authorization": f"Bearer {token}"}  # if your server needs it
)


def test_basic_inference():
    """Test basic inference functionality using LiteLLM completion API."""
    try:
        # Simple test prompt
        test_prompt = "What is 2 + 2?"
        
        # Generate response using LiteLLM completion API
        response = completion(
            model="hosted_vllm/qwen-knowledge-7b",
            messages=[{"role": "user", "content": test_prompt}],
            api_base="http://localhost:8101/v1"
        )
        
        # Extract content from response
        content = response.choices[0].message.content
        
        # Basic assertions
        assert response is not None, "Response should not be None"
        assert content is not None, "Response content should not be None"
        assert isinstance(content, str), "Response content should be a string"
        assert len(content.strip()) > 0, "Response content should not be empty"
        
        print(f"✅ Basic inference test passed!")
        print(f"Prompt: {test_prompt}")
        print(f"Response: {content}")
        print(f"Usage: {response.usage}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic inference test failed: {str(e)}")
        return False


def test_inference_with_system_message():
    """Test inference with system and user messages."""
    try:
        # Test with system message
        messages = [
            {"role": "system", "content": "You are a helpful math tutor. Always show your work."},
            {"role": "user", "content": "What is 15 + 27?"}
        ]
        
        response = completion(
            model="hosted_vllm/meta-llama/Llama-3.3-70B-Instruct",
            messages=messages,
            api_base="http://localhost:8100/v1"
        )
        
        content = response.choices[0].message.content
        
        assert response is not None, "Response should not be None"
        assert content is not None, "Response content should not be None"
        assert isinstance(content, str), "Response content should be a string"
        assert len(content.strip()) > 0, "Response content should not be empty"
        
        print(f"✅ System message test passed!")
        print(f"Messages: {messages}")
        print(f"Response: {content}")
        print(f"Usage: {response.usage}")
        
        return True
        
    except Exception as e:
        print(f"❌ System message test failed: {str(e)}")
        return False


def test_inference_with_parameters():
    """Test inference with custom parameters like temperature."""
    try:
        # Test with custom parameters
        test_prompt = "Write a creative short story about a robot learning to paint."
        
        response = completion(
            model="hosted_vllm/meta-llama/Llama-3.3-70B-Instruct",
            messages=[{"role": "user", "content": test_prompt}],
            api_base="http://localhost:8100/v1",
            temperature=0.8,
            max_tokens=200
        )
        
        content = response.choices[0].message.content
        
        assert response is not None, "Response should not be None"
        assert content is not None, "Response content should not be None"
        assert isinstance(content, str), "Response content should be a string"
        assert len(content.strip()) > 0, "Response content should not be empty"
        
        print(f"✅ Parameters test passed!")
        print(f"Prompt: {test_prompt}")
        print(f"Response: {content}")
        print(f"Usage: {response.usage}")
        
        return True
        
    except Exception as e:
        print(f"❌ Parameters test failed: {str(e)}")
        return False


def test_streaming_inference():
    """Test streaming inference functionality."""
    try:
        # Test streaming
        test_prompt = "Count from 1 to 10 with explanations."
        
        response = completion(
            model="hosted_vllm/meta-llama/Llama-3.3-70B-Instruct",
            messages=[{"role": "user", "content": test_prompt}],
            api_base="http://localhost:8100/v1",
            stream=True
        )
        
        # Collect streamed chunks
        chunks = []
        for chunk in response:
            if chunk.choices[0].delta.content:
                chunks.append(chunk.choices[0].delta.content)
        
        full_response = ''.join(chunks)
        
        assert len(chunks) > 0, "Should receive at least one chunk"
        assert len(full_response.strip()) > 0, "Full response should not be empty"
        
        print(f"✅ Streaming test passed!")
        print(f"Prompt: {test_prompt}")
        print(f"Response chunks received: {len(chunks)}")
        print(f"Full response: {full_response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Streaming test failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("Testing LiteLLM model inference...")
    print("=" * 60)
    
    # Run tests
    tests = [
        ("Basic inference", test_basic_inference),
        ("System message", test_inference_with_system_message),
        ("Custom parameters", test_inference_with_parameters),
        ("Streaming", test_streaming_inference)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        print("-" * 40)
        results[test_name] = test_func()
        
    # Summary
    print("\n" + "=" * 60)
    print("🏁 TEST SUMMARY:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20} | {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("🎉 All tests PASSED! Your LiteLLM model is working correctly!")
    else:
        print("⚠️  Some tests FAILED. Check your server connection and configuration.")
    print("=" * 60)

