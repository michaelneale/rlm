# Recursive Language Models (minimal version) 

[Link to the original blogpost 📝](https://alexzhang13.github.io/blog/2025/rlm/)

## 🚀 OpenAI-Compatible Server

Run RLM as an OpenAI-compatible API server to handle arbitrarily large contexts.

### Quick Start

```bash
# 1. Set your OpenAI API key
export OPENAI_API_KEY="sk-..."

# 2. Start the server
python rlm_server.py
```

Server runs at `http://localhost:8000` with verbose logging enabled.

### Usage

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")

# Load any size file
with open("huge_file.txt") as f:
    content = f.read()

response = client.chat.completions.create(
    model="rlm-gpt-4o-mini",
    messages=[
        {"role": "system", "content": content},
        {"role": "user", "content": "Summarize this"}
    ]
)

print(response.choices[0].message.content)
```

### Examples

```bash
cd examples

# Simple example with small document
python simple_example.py

# Large file example (3.3MB Codebase.txt)
python large_file_example.py
```

Watch the server terminal to see RLM's recursive iterations in real-time!

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
