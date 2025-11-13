# Recursive Language Models (minimal version) 

[Link to the original blogpost 📝](https://alexzhang13.github.io/blog/2025/rlm/)

## 🚀 Quick Start

### CLI Usage

```bash
# Set your API key
export OPENAI_API_KEY="sk-..."

# Query a file
./query Codebase.txt "What is this codebase about?"

# Query text directly
./query --text "Some long text here" "Summarize this"
```

### MCP Server

Run RLM as an MCP (Model Context Protocol) server - use it as a tool from Claude Desktop, Cline, or any MCP client.

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add to your MCP client config
# See MCP Configuration below
```

### MCP Configuration

**Option 1: Local install**

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "rlm": {
      "command": "python",
      "args": ["/absolute/path/to/rlm/mcp_server.py"],
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

**Option 2: Using uvx (recommended for published packages)**

If published to PyPI:
```json
{
  "mcpServers": {
    "rlm": {
      "command": "uvx",
      "args": ["mcp-server-rlm"],
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

Or from git:
```json
{
  "mcpServers": {
    "rlm": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/yourusername/rlm.git", "mcp-server-rlm"],
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

**Option 3: Using uv run (for local development)**

```json
{
  "mcpServers": {
    "rlm": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/rlm", "run", "mcp-server-rlm"],
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

### Available Tools

**`query_text`** - Query large text using RLM
- `text`: The text/document to query (any size)
- `query`: Your question
- `max_iterations`: Optional, default 10

**`query_file`** - Query a file using RLM  
- `file_path`: Path to the file
- `query`: Your question
- `max_iterations`: Optional, default 10

### Example Usage

From Claude Desktop or any MCP client:

```
"Can you use the query_file tool to analyze Codebase.txt 
and tell me what the main components are?"
```

RLM will recursively process the file and return an answer, even if it's 3MB+!

---

## Original README

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
