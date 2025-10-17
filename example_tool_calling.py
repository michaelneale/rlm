"""
Example demonstrating external tool calling with RLM.

This example shows how RLM can:
1. Handle massive contexts internally via REPL
2. Expose external tool calling to the caller
3. Continue execution after tool results are provided
"""

import json
from rlm.rlm_api import create_rlm_client

# Example tool: search database
def search_database(query: str) -> str:
    """Simulate searching a database."""
    # In a real scenario, this would query an actual database
    results = {
        "magic": "The magic number is 42",
        "price": "The price of product X is $99.99",
        "status": "The order status is: shipped"
    }
    
    for key, value in results.items():
        if key.lower() in query.lower():
            return value
    
    return "No results found"

# Example tool: calculate
def calculate(expression: str) -> str:
    """Safely evaluate a mathematical expression."""
    try:
        # In production, use a safer evaluation method
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error calculating: {str(e)}"


def execute_tool_call(tool_call) -> dict:
    """Execute a single tool call and return the result."""
    function_name = tool_call['function']['name']
    function_args = json.loads(tool_call['function']['arguments'])
    
    # Route to appropriate function
    if function_name == "search_database":
        result = search_database(function_args.get('query', ''))
    elif function_name == "calculate":
        result = calculate(function_args.get('expression', ''))
    else:
        result = f"Unknown function: {function_name}"
    
    # Return in OpenAI tool message format
    return {
        "role": "tool",
        "tool_call_id": tool_call['id'],
        "name": function_name,
        "content": result
    }


def example_basic_tool_calling():
    """Example 1: Basic tool calling without massive context."""
    print("\n" + "="*60)
    print("Example 1: Basic Tool Calling")
    print("="*60)
    
    api = create_rlm_client(
        model="gpt-5-nano",
        recursive_model="gpt-5",
        enable_logging=True
    )
    
    # Define tools
    tools = [{
        "type": "function",
        "function": {
            "name": "search_database",
            "description": "Search a database for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }
    }]
    
    # Initial request
    messages = [
        {"role": "user", "content": "What is the magic number in our database?"}
    ]
    
    print("\n📤 Initial request:", messages[0]['content'])
    response = api.chat_completion(messages=messages, tools=tools)
    
    # Check if tool calls returned
    if response['choices'][0]['finish_reason'] == 'tool_calls':
        print("\n🔧 Tool calls detected!")
        tool_calls = response['choices'][0]['message']['tool_calls']
        
        # Execute each tool call
        tool_results = []
        for tool_call in tool_calls:
            print(f"  - Calling: {tool_call['function']['name']}")
            print(f"    Args: {tool_call['function']['arguments']}")
            
            result = execute_tool_call(tool_call)
            tool_results.append(result)
            print(f"    Result: {result['content']}")
        
        # Continue with tool results
        messages.append(response['choices'][0]['message'])
        messages.extend(tool_results)
        
        print("\n🔄 Continuing with tool results...")
        response = api.chat_completion(messages=messages, tools=tools)
    
    # Print final answer
    print("\n✅ Final Answer:")
    print(response['choices'][0]['message']['content'])


def example_massive_context_with_tools():
    """Example 2: Tool calling with massive context (RLM's strength)."""
    print("\n" + "="*60)
    print("Example 2: Massive Context + Tool Calling")
    print("="*60)
    
    api = create_rlm_client(
        model="gpt-5-nano",
        recursive_model="gpt-5",
        enable_logging=True,
        max_iterations=10
    )
    
    # Generate a large context
    print("\n📚 Generating massive context (100K lines)...")
    lines = []
    for i in range(100000):
        lines.append(f"Line {i}: Some random data here")
        if i == 50000:
            lines.append("IMPORTANT: The secret code is XYZ-789")
    
    massive_context = "\n".join(lines)
    print(f"   Context size: {len(massive_context)} characters")
    
    # Define tools
    tools = [{
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Calculate a mathematical expression",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        }
    }]
    
    # Request
    messages = [
        {"role": "system", "content": massive_context},
        {"role": "user", "content": "Find the secret code in the context and calculate what 100 * 2 equals"}
    ]
    
    print("\n📤 Request: Find secret code + calculation")
    response = api.chat_completion(messages=messages, tools=tools)
    
    # Handle tool calls if any
    while response['choices'][0]['finish_reason'] == 'tool_calls':
        print("\n🔧 Tool calls detected!")
        tool_calls = response['choices'][0]['message']['tool_calls']
        
        # Execute tools
        tool_results = []
        for tool_call in tool_calls:
            print(f"  - Calling: {tool_call['function']['name']}")
            print(f"    Args: {tool_call['function']['arguments']}")
            
            result = execute_tool_call(tool_call)
            tool_results.append(result)
            print(f"    Result: {result['content']}")
        
        # Continue
        messages.append(response['choices'][0]['message'])
        messages.extend(tool_results)
        
        print("\n🔄 Continuing...")
        response = api.chat_completion(messages=messages, tools=tools)
    
    # Print final answer
    print("\n✅ Final Answer:")
    print(response['choices'][0]['message']['content'])


def example_no_tools_backward_compat():
    """Example 3: Without tools (backward compatible)."""
    print("\n" + "="*60)
    print("Example 3: Without Tools (Backward Compatible)")
    print("="*60)
    
    api = create_rlm_client(
        model="gpt-5-nano",
        recursive_model="gpt-5",
        enable_logging=True
    )
    
    # Generate context
    context = "The answer to the ultimate question is 42. " * 100
    
    messages = [
        {"role": "system", "content": context},
        {"role": "user", "content": "What is the answer to the ultimate question?"}
    ]
    
    print("\n📤 Request without tools")
    response = api.chat_completion(messages=messages)
    
    print("\n✅ Final Answer:")
    print(response['choices'][0]['message']['content'])


if __name__ == "__main__":
    print("="*60)
    print("RLM External Tool Calling Examples")
    print("="*60)
    print("\nThese examples demonstrate how RLM can handle both:")
    print("1. External tool calling (exposed to caller)")
    print("2. Internal REPL/recursion (handles massive contexts)")
    print("\n" + "="*60)
    
    # Run examples
    try:
        # Example 1: Basic tool calling
        example_basic_tool_calling()
        
        # Example 2: Massive context + tools
        # example_massive_context_with_tools()  # Uncomment to run (takes time)
        
        # Example 3: Backward compatibility
        example_no_tools_backward_compat()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)
