# Recursive Language Models (minimal version) 

[Link to the original blogpost 📝](https://alexzhang13.github.io/blog/2025/rlm/)

I received a lot of requests to put out a notebook or gist version of the codebase I've been using. Sadly it's a bit entangled with a bunch of random state, cost, and code execution tracking logic that I want to clean up while I run other experiments. In the meantime, I've re-written a simpler version of what I'm using so people can get started building on top and writing their own RLM implementations. Happy hacking!

![teaser](media/rlm.png)

I've provided a basic, minimal implementation of a recursive language model (RLM) with a REPL environment for OpenAI clients. Like the blogpost, we only implement recursive sub-calls with `depth=1` inside the RLM environment. Enabling further depths is as simple as replacing the `Sub_RLM` class with the `RLM_REPL` class, but you may need to finagle the `exec`-based REPL environments to work better here (because now your sub-RLMs have their own REPL environments!).

In this stripped implementation, we exclude a lot of the logging, cost tracking, prompting, and REPL execution details of the experiments run in the blogpost. It's relatively easy to modify and build on top of this code to reproduce those results, but it's currently harder to go from my full codebase to supporting any new functionality.

## Basic Example
We have all the basic dependencies in `requirements.txt`, although none are really necessary if you change your implementation (`openai` for LM API calls, `dotenv` for .env loading, and `rich` for logging).

In `main.py`, we have a basic needle-in-the-haystack (NIAH) example that embeds a random number inside ~1M lines of random words, and asks the model to go find it. It's a silly Hello World type example to emphasize that `RLM.completion()` calls are meant to replace `LM.completion()` calls.

## Code Structure
In the `rlm/` folder, the two main files are `rlm_repl.py` and `repl.py`. 
* `rlm_repl.py` offers a basic implementation of an RLM using a REPL environment in the `RLM_REPL` class. The `completion()` function gets called when we query an RLM.
* `repl.py` is a simple `exec`-based implementation of a REPL environment that adds an LM sub-call function. To make the system truly recursive beyond `depth=1`, you can replace the `Sub_RLM` class with `RLM_REPL` (they all inherit from the `RLM` base class).

The functionality for parsing and handling base LLM clients are all in `rlm/utils/`. We also add example prompts here.

> The `rlm/logger/` folder mainly contains optional logging utilities used by the RLM REPL implementation. If you want to enable colorful or enhanced logging outputs, you may need to install the [`rich`](https://github.com/Textualize/rich) library as a dependency.
```
pip install rich
```

When you run your code, you'll see something like this:

![Example logging output using `rich`](media/rich.png)

## 🆕 External Tool Calling Support

RLM now supports **external tool calling** (OpenAI-compatible)! This means you can use RLM as a virtual LLM API that:
- ✅ Handles massive contexts internally via REPL/recursion
- ✅ Exposes external tool calls to the caller
- ✅ Seamlessly continues when tool results are provided
- ✅ Maintains full backward compatibility

### Quick Start with Tool Calling

```python
from rlm.rlm_api import create_rlm_client

# Initialize RLM with tool calling support
api = create_rlm_client(
    model="gpt-5-nano",
    recursive_model="gpt-5",
    enable_logging=True
)

# Define tools (OpenAI format)
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

# Make request with massive context + tools
response = api.chat_completion(
    messages=[
        {"role": "system", "content": "...1M lines of context..."},
        {"role": "user", "content": "Find X in the context"}
    ],
    tools=tools
)

# Handle tool calls if returned
if response['choices'][0]['finish_reason'] == 'tool_calls':
    # Execute tools externally
    tool_results = execute_tools(response['choices'][0]['message']['tool_calls'])
    
    # Continue with results
    response = api.chat_completion(
        messages=[...previous_messages..., tool_results],
        tools=tools
    )

print(response['choices'][0]['message']['content'])
```

### Example & Documentation

- **Example**: `example_tool_calling.py` - Complete working examples
- **Documentation**: `llm-adapter.md` - Full implementation details
- **Run example**: `python example_tool_calling.py`

### Key Features

1. **OpenAI-Compatible**: Drop-in replacement for OpenAI API
2. **Stateful Sessions**: Automatically handles tool call continuations
3. **Priority Handling**: External tools > Internal REPL > Final answer
4. **Backward Compatible**: Works with or without tools parameter

## 🌐 HTTP API Server

Run RLM as an **OpenAI-compatible HTTP server** on localhost!

### Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start server
python rlm_server.py

# 3. Use with any OpenAI client!
```

### Usage

```python
from openai import OpenAI

# Point to RLM server instead of OpenAI
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"
)

# Use exactly like OpenAI!
response = client.chat.completions.create(
    model="gpt-4o-mini:gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

Or set environment variables:
```bash
export OPENAI_BASE_URL="http://localhost:8000/v1"
export OPENAI_API_KEY="dummy"

# Now ANY tool using OpenAI will use RLM!
```

### Server Features

- ✅ **Full OpenAI API compatibility** - Works with OpenAI Python client
- ✅ **Tool calling support** - Function calling works perfectly
- ✅ **Massive contexts** - Handles 1M+ tokens internally
- ✅ **Multiple models** - Switch between different model combinations
- ✅ **Easy integration** - Works with LangChain, LlamaIndex, etc.

### Documentation

- **Server Guide**: `SERVER_GUIDE.md` - Complete server documentation
- **Client Examples**: `example_client.py` - Working code examples
- **Run examples**: See `SERVER_GUIDE.md` for all use cases