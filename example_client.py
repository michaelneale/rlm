"""
Example client for RLM HTTP API server.

This demonstrates how to use the RLM server as a drop-in replacement
for OpenAI by pointing the OpenAI client to localhost.

Before running:
    1. Start the server: python rlm_server.py
    2. Run this client: python example_client.py
"""

from openai import OpenAI
import json

def example_basic_chat():
    """Example 1: Basic chat without tools."""
    print("\n" + "="*60)
    print("Example 1: Basic Chat")
    print("="*60)
    
    # Create OpenAI client pointing to RLM server
    client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="dummy"  # RLM doesn't need real API key
    )
    
    # Make a request
    response = client.chat.completions.create(
        model="gpt-4o-mini:gpt-4o",
        messages=[
            {"role": "user", "content": "What is 2+2?"}
        ]
    )
    
    print(f"\nResponse: {response.choices[0].message.content}")
    print(f"Finish reason: {response.choices[0].finish_reason}")


def example_with_massive_context():
    """Example 2: Chat with massive context."""
    print("\n" + "="*60)
    print("Example 2: Massive Context")
    print("="*60)
    
    client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="dummy"
    )
    
    # Generate large context
    print("Generating 50K line context...")
    lines = [f"Line {i}: Random data here" for i in range(50000)]
    lines[25000] = "SPECIAL: The secret code is ABC-123"
    massive_context = "\n".join(lines)
    print(f"Context size: {len(massive_context)} characters")
    
    # Make request with massive context
    print("\nQuerying RLM...")
    response = client.chat.completions.create(
        model="gpt-4o-mini:gpt-4o",
        messages=[
            {"role": "system", "content": massive_context},
            {"role": "user", "content": "What is the secret code in the context?"}
        ]
    )
    
    print(f"\nResponse: {response.choices[0].message.content}")


def example_with_tool_calling():
    """Example 3: Chat with tool calling."""
    print("\n" + "="*60)
    print("Example 3: Tool Calling")
    print("="*60)
    
    client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="dummy"
    )
    
    # Define tools
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather in a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "The temperature unit"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]
    
    # First request
    print("\nMaking initial request with tools...")
    response = client.chat.completions.create(
        model="gpt-4o-mini:gpt-4o",
        messages=[
            {"role": "user", "content": "What's the weather in San Francisco?"}
        ],
        tools=tools
    )
    
    # Check if tool calls were made
    if response.choices[0].finish_reason == "tool_calls":
        print("\n🔧 Tool calls detected!")
        
        tool_calls = response.choices[0].message.tool_calls
        for tool_call in tool_calls:
            print(f"  Tool: {tool_call.function.name}")
            print(f"  Args: {tool_call.function.arguments}")
        
        # Simulate executing the tool
        tool_results = []
        for tool_call in tool_calls:
            # In real scenario, actually call the function
            result = json.dumps({
                "location": "San Francisco, CA",
                "temperature": "68",
                "unit": "fahrenheit",
                "condition": "Sunny"
            })
            
            tool_results.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "content": result
            })
            print(f"  Result: {result}")
        
        # Continue with tool results
        print("\n🔄 Continuing with tool results...")
        messages = [
            {"role": "user", "content": "What's the weather in San Francisco?"},
            response.choices[0].message,
            *tool_results
        ]
        
        response = client.chat.completions.create(
            model="gpt-4o-mini:gpt-4o",
            messages=messages,
            tools=tools
        )
    
    print(f"\n✅ Final Response: {response.choices[0].message.content}")


def example_massive_context_with_tools():
    """Example 4: Massive context + tool calling (RLM's superpower!)."""
    print("\n" + "="*60)
    print("Example 4: Massive Context + Tools")
    print("="*60)
    
    client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="dummy"
    )
    
    # Generate massive context with data
    print("Generating 100K line context...")
    lines = []
    for i in range(100000):
        lines.append(f"Log entry {i}: Normal operation")
        if i == 50000:
            lines.append("ERROR: Database connection failed with error code 1234")
    
    massive_context = "\n".join(lines)
    print(f"Context size: {len(massive_context)} characters")
    
    # Define tool for looking up error codes
    tools = [
        {
            "type": "function",
            "function": {
                "name": "lookup_error_code",
                "description": "Look up what an error code means",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "error_code": {
                            "type": "string",
                            "description": "The error code to look up"
                        }
                    },
                    "required": ["error_code"]
                }
            }
        }
    ]
    
    # Make request
    print("\nQuerying RLM with massive context + tools...")
    response = client.chat.completions.create(
        model="gpt-4o-mini:gpt-4o",
        messages=[
            {"role": "system", "content": massive_context},
            {"role": "user", "content": "Find any errors in the logs and look up what they mean"}
        ],
        tools=tools
    )
    
    # Handle tool calls if any
    conversation = [
        {"role": "system", "content": massive_context},
        {"role": "user", "content": "Find any errors in the logs and look up what they mean"}
    ]
    
    while response.choices[0].finish_reason == "tool_calls":
        print("\n🔧 Tool calls detected!")
        
        # Add assistant message with tool calls
        conversation.append(response.choices[0].message)
        
        # Execute tools
        for tool_call in response.choices[0].message.tool_calls:
            print(f"  Calling: {tool_call.function.name}")
            args = json.loads(tool_call.function.arguments)
            print(f"  Args: {args}")
            
            # Simulate tool execution
            result = json.dumps({
                "error_code": args.get("error_code"),
                "description": "Connection timeout - the database server is not responding",
                "solution": "Check database server status and network connectivity"
            })
            
            conversation.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "content": result
            })
            print(f"  Result: {result}")
        
        # Continue
        print("\n🔄 Continuing...")
        response = client.chat.completions.create(
            model="gpt-4o-mini:gpt-4o",
            messages=conversation,
            tools=tools
        )
    
    print(f"\n✅ Final Answer:\n{response.choices[0].message.content}")


def test_models_endpoint():
    """Test the /v1/models endpoint."""
    print("\n" + "="*60)
    print("Testing /v1/models endpoint")
    print("="*60)
    
    client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="dummy"
    )
    
    models = client.models.list()
    print(f"\nAvailable models:")
    for model in models.data:
        print(f"  - {model.id}")


if __name__ == "__main__":
    print("="*60)
    print("RLM HTTP API Client Examples")
    print("="*60)
    print("\nMake sure the server is running:")
    print("  python rlm_server.py")
    print("\n" + "="*60)
    
    try:
        # Test models endpoint
        test_models_endpoint()
        
        # Run examples
        example_basic_chat()
        
        # Uncomment to run other examples:
        # example_with_massive_context()
        # example_with_tool_calling()
        # example_massive_context_with_tools()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("  1. Server is running: python rlm_server.py")
        print("  2. Dependencies installed: pip install -r requirements.txt")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)
