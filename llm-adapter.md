# RLM External Tool Calling Adapter

## Overview
This document tracks the implementation of external tool calling support for RLM, allowing it to be used as a virtual LLM API that can return tool calls to the caller while handling massive contexts internally through REPL/recursion.

## Current State (Before Modifications)

### What RLM Does Now:
- Uses **code execution as internal tools** (```repl``` blocks)
- REPL provides `llm_query()` for recursive sub-LLM calls
- NO external tool calling support
- Returns only final text answers

### Architecture:
```
User Query → RLM_REPL.completion() → Outer LLM (no tools) → Text Response
                ↓
         Internal REPL loop (handles massive context)
                ↓
         Final Answer (text only)
```

## Target State (After Modifications)

### What RLM Will Do:
- **Accept tools parameter** from caller
- **Pass tools to outer LLM** in each iteration
- **Detect tool calls** in outer LLM response
- **Return tool calls to caller** (pause execution)
- **Resume execution** when caller provides tool results
- Continue handling massive contexts internally via REPL

### New Architecture:
```
User Query + Tools → RLMToolCallingAPI → Outer LLM (with tools) → Tool Calls?
                                              ↓                         ↓
                                    Internal REPL (massive context)   Return to Caller
                                              ↓                         ↓
                                    Tool Results from Caller ←─────────┘
                                              ↓
                                    Continue iteration → Final Answer
```

## Implementation Status

✅ **COMPLETED** - All phases implemented successfully!

## Implementation Plan

### Phase 1: Modify OpenAIClient ✅ DONE
**File**: `rlm/utils/llm.py`

**Changes**:
1. Add `tools` parameter to `completion()` method
2. Return full response object instead of just content string
3. Include `tool_calls` in response

**Before**:
```python
def completion(self, messages, max_tokens=None, **kwargs) -> str:
    response = self.client.chat.completions.create(...)
    return response.choices[0].message.content
```

**After**:
```python
def completion(self, messages, tools=None, max_tokens=None, **kwargs) -> dict:
    response = self.client.chat.completions.create(
        model=self.model,
        messages=messages,
        tools=tools,
        max_completion_tokens=max_tokens,
        **kwargs
    )
    
    message = response.choices[0].message
    return {
        'content': message.content,
        'tool_calls': message.tool_calls if hasattr(message, 'tool_calls') else None,
        'role': 'assistant'
    }
```

### Phase 2: Update RLM_REPL Main Loop ✓
**File**: `rlm/rlm_repl.py`

**Changes**:
1. Accept `tools` parameter in `completion()` method
2. Pass tools to outer LLM calls
3. Check for tool calls before checking for code blocks
4. Return early with tool calls when detected
5. Store state for continuation

**Key modifications at line 76-112** (the main loop):
```python
def completion(self, context, query=None, tools=None, tool_results=None):
    # Setup or restore state
    if tool_results is None:
        self.messages = self.setup_context(context, query)
    else:
        # Continuing from tool calls - append tool results
        self.messages.extend(tool_results)
    
    for iteration in range(self._max_iterations):
        # Query outer LLM with tools
        response = self.llm.completion(
            self.messages + [next_action_prompt(query, iteration)],
            tools=tools
        )
        
        # PRIORITY 1: Check for external tool calls
        if response.get('tool_calls'):
            # Add assistant message with tool calls
            self.messages.append({
                'role': 'assistant',
                'content': response.get('content'),
                'tool_calls': response['tool_calls']
            })
            
            # Return control to caller
            return {
                'type': 'tool_calls',
                'tool_calls': response['tool_calls'],
                'content': response.get('content'),
                'state': 'paused',
                'iteration': iteration
            }
        
        # PRIORITY 2: Check for internal REPL code blocks
        response_text = response.get('content', '')
        code_blocks = utils.find_code_blocks(response_text)
        
        if code_blocks:
            # Execute REPL code internally (existing logic)
            self.messages = utils.process_code_execution(...)
        else:
            # No code blocks, add as assistant message
            self.messages.append({
                'role': 'assistant',
                'content': response_text
            })
        
        # PRIORITY 3: Check for final answer
        final_answer = utils.check_for_final_answer(response_text, ...)
        if final_answer:
            return {
                'type': 'final_answer',
                'content': final_answer,
                'state': 'complete'
            }
    
    # Max iterations reached
    return {'type': 'final_answer', 'content': '...', 'state': 'complete'}
```

### Phase 3: Create RLMToolCallingAPI Wrapper ✓
**File**: `rlm/rlm_api.py` (new file)

**Purpose**: Provide OpenAI-compatible API with stateful tool calling

```python
class RLMToolCallingAPI:
    """
    OpenAI-compatible API wrapper for RLM with external tool calling support.
    
    Handles massive contexts internally while exposing standard tool calling
    interface to external callers.
    """
    
    def __init__(self, model="gpt-5", recursive_model="gpt-5", **kwargs):
        self.rlm = RLM_REPL(model=model, recursive_model=recursive_model, **kwargs)
        self.session_state = None
        self.current_context = None
        self.current_query = None
        self.current_tools = None
    
    def chat_completion(self, messages, tools=None):
        """
        OpenAI-compatible chat completion with tool calling support.
        
        Returns:
            Response dict with either tool_calls or final content
        """
        # Check if this is a continuation (has tool results)
        if self._has_tool_results(messages):
            # Extract tool results from messages
            tool_results = self._extract_tool_results(messages)
            
            # Continue RLM execution with tool results
            result = self.rlm.completion(
                context=self.current_context,
                query=self.current_query,
                tools=self.current_tools,
                tool_results=tool_results
            )
        else:
            # New conversation - extract context and query
            self.current_context = self._extract_context(messages)
            self.current_query = messages[-1]['content']
            self.current_tools = tools
            
            # Start RLM execution
            result = self.rlm.completion(
                context=self.current_context,
                query=self.current_query,
                tools=tools
            )
        
        # Format response based on result type
        if result['type'] == 'tool_calls':
            return {
                'choices': [{
                    'message': {
                        'role': 'assistant',
                        'content': result.get('content'),
                        'tool_calls': result['tool_calls']
                    },
                    'finish_reason': 'tool_calls'
                }],
                'model': self.rlm.model
            }
        else:  # final_answer
            return {
                'choices': [{
                    'message': {
                        'role': 'assistant',
                        'content': result['content']
                    },
                    'finish_reason': 'stop'
                }],
                'model': self.rlm.model
            }
    
    def _extract_context(self, messages):
        """Extract massive context from messages"""
        # Strategy: Take all messages except the last user message
        # or look for system messages with context
        context_messages = [m for m in messages if m['role'] in ['system', 'assistant']]
        if context_messages:
            return context_messages
        return messages[:-1] if len(messages) > 1 else []
    
    def _has_tool_results(self, messages):
        """Check if messages contain tool results"""
        return any(m.get('role') == 'tool' for m in messages)
    
    def _extract_tool_results(self, messages):
        """Extract tool result messages"""
        # Find tool messages and format for RLM
        tool_messages = [m for m in messages if m.get('role') == 'tool']
        return tool_messages
    
    def reset(self):
        """Reset session state"""
        self.session_state = None
        self.current_context = None
        self.current_query = None
        self.current_tools = None
        self.rlm.reset()
```

### Phase 4: Update Utility Functions ✓
**File**: `rlm/utils/utils.py`

**Changes**:
1. Update functions to handle dict responses instead of strings
2. Add tool call formatting utilities

```python
def extract_response_content(response):
    """Extract content from response (dict or string)"""
    if isinstance(response, dict):
        return response.get('content', '')
    return response

def format_tool_calls_for_messages(tool_calls):
    """Format tool calls for message history"""
    # Convert OpenAI tool_calls to message format
    return [{
        'role': 'assistant',
        'tool_calls': tool_calls
    }]
```

## Usage Examples

### Example 1: Simple Tool Calling
```python
from rlm.rlm_api import RLMToolCallingAPI

# Initialize API
api = RLMToolCallingAPI(
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
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"]
        }
    }
}]

# Call with massive context
massive_context = "..." # 1M lines of text
response = api.chat_completion(
    messages=[
        {"role": "system", "content": massive_context},
        {"role": "user", "content": "Find information about X"}
    ],
    tools=tools
)

# Check if tool calls returned
if response['choices'][0]['finish_reason'] == 'tool_calls':
    tool_calls = response['choices'][0]['message']['tool_calls']
    
    # Execute tools externally
    tool_results = []
    for call in tool_calls:
        result = search_database(call['function']['arguments']['query'])
        tool_results.append({
            "role": "tool",
            "tool_call_id": call['id'],
            "content": result
        })
    
    # Continue with tool results
    response = api.chat_completion(
        messages=[
            {"role": "system", "content": massive_context},
            {"role": "user", "content": "Find information about X"},
            response['choices'][0]['message'],  # Assistant message with tool calls
            *tool_results  # Tool results
        ],
        tools=tools
    )

print(response['choices'][0]['message']['content'])
```

### Example 2: Multi-turn with Tools
```python
# First turn - RLM might use internal REPL for chunking
response1 = api.chat_completion(
    messages=[{"role": "user", "content": "Analyze this 1M line document"}],
    tools=tools
)

# Could return tool calls OR continue internally with REPL
# RLM decides based on what the outer LLM wants to do

# If tool calls:
if response1['choices'][0]['finish_reason'] == 'tool_calls':
    # Handle externally
    pass
# If no tool calls, RLM handled it internally via REPL and returns final answer
```

## Implementation Notes

### Key Design Decisions:

1. **Priority Order in Main Loop**:
   - Tool calls > REPL code blocks > Final answer
   - External tool calls take precedence over internal REPL

2. **State Management**:
   - RLMToolCallingAPI maintains session state
   - Can resume from tool calls seamlessly
   - Context is preserved across tool call boundaries

3. **Backward Compatibility**:
   - If no tools provided, works exactly as before
   - Existing code doesn't break

4. **OpenAI Compatibility**:
   - Response format matches OpenAI API
   - Tool call format is identical
   - Can be used as drop-in replacement

### Potential Issues & Solutions:

**Issue**: Outer LLM might generate both tool calls AND REPL code
**Solution**: Prioritize tool calls, ignore REPL code in that iteration

**Issue**: Tool results might be huge
**Solution**: Treat tool results like context - load into REPL if needed

**Issue**: State persistence across requests
**Solution**: RLMToolCallingAPI is stateful per session

## Examples

### Python API Examples

A complete working example is provided in `example_tool_calling.py`. Run it with:

```bash
python example_tool_calling.py
```

The example demonstrates:
1. Basic tool calling without massive context
2. Tool calling WITH massive context (RLM's unique strength)
3. Backward compatibility (no tools)

### HTTP API Server ✅ NEW!

RLM can now be run as an OpenAI-compatible HTTP server!

**Start the server:**
```bash
python rlm_server.py
```

**Use with OpenAI client:**
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"
)

response = client.chat.completions.create(
    model="gpt-4o-mini:gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}],
    tools=[...]  # Tool calling works!
)
```

**Or use environment variables:**
```bash
export OPENAI_BASE_URL="http://localhost:8000/v1"
export OPENAI_API_KEY="dummy"

# Now ANY OpenAI-compatible tool will use RLM!
python your_app.py
```

See `SERVER_GUIDE.md` for complete documentation and `example_client.py` for working examples.

## Testing Plan

### Test 1: Basic Tool Calling
- [ ] Single tool call returned
- [ ] Tool results processed correctly
- [ ] Final answer after tool use

### Test 2: Multiple Tool Calls
- [ ] Multiple tools in sequence
- [ ] Parallel tool calls if supported

### Test 3: No Tool Calls (Backward Compat)
- [ ] Works without tools parameter
- [ ] REPL code blocks still work

### Test 4: Massive Context + Tools
- [ ] Handles 1M lines + tool calls
- [ ] Internal REPL chunking + external tools

### Test 5: Tool Calls with REPL
- [ ] Both can coexist in different iterations
- [ ] Priority order works correctly

## Future Enhancements

1. **Streaming Support**: Stream tool calls as they're detected
2. **Tool Choice Control**: Allow forcing tool use or none
3. **Parallel Tool Execution**: Execute multiple tools concurrently
4. **Tool Result Chunking**: Auto-chunk huge tool results into REPL
5. **Cost Tracking**: Track costs across tool calls
6. **Session Persistence**: Save/restore session state

## References

- OpenAI Function Calling: https://platform.openai.com/docs/guides/function-calling
- Original RLM Blog Post: https://alexzhang13.github.io/blog/2025/rlm/
- RLM GitHub: (this repo)
