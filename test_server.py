"""Quick test of the RLM server."""
from openai import OpenAI

# Connect to local RLM server
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"
)

print("Testing RLM Server...")
print("=" * 60)

# Test 1: Simple chat
print("\n1. Simple Chat Test")
print("-" * 60)
try:
    response = client.chat.completions.create(
        model="gpt-4o-mini:gpt-4o",
        messages=[
            {"role": "user", "content": "Say 'Hello from RLM!' and nothing else."}
        ]
    )
    print(f"✓ Response: {response.choices[0].message.content}")
    print(f"✓ Finish reason: {response.choices[0].finish_reason}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: With context
print("\n2. Context Test")
print("-" * 60)
try:
    context = "The secret word is BANANA. " * 100
    response = client.chat.completions.create(
        model="gpt-4o-mini:gpt-4o",
        messages=[
            {"role": "system", "content": context},
            {"role": "user", "content": "What is the secret word?"}
        ]
    )
    print(f"✓ Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Tool calling
print("\n3. Tool Calling Test")
print("-" * 60)
try:
    tools = [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    }]
    
    response = client.chat.completions.create(
        model="gpt-4o-mini:gpt-4o",
        messages=[
            {"role": "user", "content": "What's the weather in Paris?"}
        ],
        tools=tools
    )
    
    if response.choices[0].finish_reason == "tool_calls":
        print(f"✓ Tool calls detected!")
        for call in response.choices[0].message.tool_calls:
            print(f"  - Tool: {call.function.name}")
            print(f"  - Args: {call.function.arguments}")
    else:
        print(f"✓ Direct response: {response.choices[0].message.content}")
        
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("Tests completed!")
