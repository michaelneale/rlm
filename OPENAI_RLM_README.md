# OpenAI-Compatible RLM Server

A simple, single-file OpenAI-compatible API server for the Recursive Language Model (RLM). This allows you to use RLM with any OpenAI-compatible client, including handling arbitrarily large contexts like your 3.3MB `Codebase.txt` file!

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install fastapi uvicorn pydantic
pip install openai  # Optional: for testing with OpenAI client
pip install requests  # Optional: for testing
```

### 2. Start the Server

```bash
python openai_rlm_server.py
```

The server will start at `http://localhost:8000`

### 3. Make Requests

#### Using the OpenAI Python Client

```python
from openai import OpenAI

# Point to RLM server instead of OpenAI
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"  # Not needed for RLM
)

# Simple query
response = client.chat.completions.create(
    model="rlm-gpt-4o-mini",
    messages=[
        {"role": "user", "content": "What is 2+2?"}
    ]
)

print(response.choices[0].message.content)
```

#### With Large Context (like Codebase.txt)

```python
# Load your massive file
with open("Codebase.txt", "r") as f:
    huge_codebase = f.read()

# RLM handles it recursively!
response = client.chat.completions.create(
    model="rlm-gpt-4o-mini",
    messages=[
        {"role": "system", "content": huge_codebase},
        {"role": "user", "content": "What are the main components?"}
    ],
    max_iterations=10  # RLM-specific: how many recursive steps
)
```

#### Using curl

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "rlm-gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

## 📋 Features

### Standard OpenAI Endpoints

- ✅ `POST /v1/chat/completions` - Chat completions
- ✅ `GET /v1/models` - List available models
- ✅ OpenAI-compatible request/response format

### RLM-Specific Features

- 🔄 **Recursive context handling** - Handle arbitrarily large contexts
- ⚙️ **Configurable iterations** - Control recursive depth with `max_iterations`
- 🐛 **Debug logging** - Enable with `enable_logging=true`

### Available Models

- `rlm-gpt-4o-mini` - Cost-effective, good for most tasks
- `rlm-gpt-4o` - More powerful, higher cost
- `gpt-4o-mini` - Direct passthrough (same as rlm-gpt-4o-mini)
- `gpt-4o` - Direct passthrough (same as rlm-gpt-4o)

## 🧪 Testing

Run the test suite:

```bash
# Start the server first
python openai_rlm_server.py

# In another terminal, run tests
python test_openai_rlm.py
```

The test suite includes:
1. Simple queries with OpenAI client
2. Large context queries (with Codebase.txt)
3. curl examples
4. Model listing

## 📚 API Reference

### Chat Completions Request

```json
{
  "model": "rlm-gpt-4o-mini",
  "messages": [
    {"role": "system", "content": "Optional context"},
    {"role": "user", "content": "Your question"}
  ],
  "temperature": 1.0,
  "max_tokens": null,
  "stream": false,
  "max_iterations": 10,      // RLM-specific
  "enable_logging": false     // RLM-specific
}
```

### Response Format

Standard OpenAI format:

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "rlm-gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Response here..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150
  }
}
```

## 🔧 Configuration

### Server Options

```bash
python openai_rlm_server.py --host 0.0.0.0 --port 8000 --reload
```

- `--host` - Host to bind to (default: 0.0.0.0)
- `--port` - Port to bind to (default: 8000)
- `--reload` - Enable auto-reload for development

### Environment Variables

Set your OpenAI API key (required by underlying RLM):

```bash
export OPENAI_API_KEY="sk-..."
```

## 💡 Use Cases

### 1. Analyze Large Codebases

```python
# Load entire codebase (3MB+)
with open("Codebase.txt") as f:
    code = f.read()

response = client.chat.completions.create(
    model="rlm-gpt-4o-mini",
    messages=[
        {"role": "system", "content": code},
        {"role": "user", "content": "Find all database queries"}
    ]
)
```

### 2. Query Long Documents

```python
# Process books, documentation, etc.
with open("war_and_peace.txt") as f:
    book = f.read()

response = client.chat.completions.create(
    model="rlm-gpt-4o-mini",
    messages=[
        {"role": "system", "content": book},
        {"role": "user", "content": "What are the main themes?"}
    ]
)
```

### 3. Use with LangChain

```python
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

# Use RLM as a drop-in replacement
chat = ChatOpenAI(
    openai_api_base="http://localhost:8000/v1",
    openai_api_key="dummy",
    model_name="rlm-gpt-4o-mini"
)

messages = [HumanMessage(content="Hello!")]
response = chat(messages)
```

## 🎯 How It Works

The RLM uses a REPL (Read-Eval-Print Loop) environment to recursively process large contexts:

1. **Context Loading** - Your large context is loaded into a Python REPL environment
2. **Recursive Processing** - The model can write and execute Python code to explore the context
3. **Iterative Refinement** - Over multiple iterations, it builds understanding and formulates answers
4. **Final Response** - Returns a coherent answer based on the recursive exploration

This allows handling contexts that would normally exceed token limits!

## 🔍 Debugging

Enable logging to see what's happening:

```python
response = client.chat.completions.create(
    model="rlm-gpt-4o-mini",
    messages=[...],
    enable_logging=True  # See recursive calls
)
```

Or check the interactive API docs at: `http://localhost:8000/docs`

## ⚠️ Limitations

- **Cost**: RLM makes multiple API calls, so it uses more tokens than standard models
- **Speed**: Recursive processing takes longer than direct inference
- **Best for**: Large contexts where standard models fail, not for simple queries

## 🤝 Integration Examples

### Cursor IDE

Add to your Cursor settings:

```json
{
  "openai.apiBase": "http://localhost:8000/v1",
  "openai.apiKey": "dummy"
}
```

### Continue.dev

```json
{
  "models": [
    {
      "title": "RLM",
      "provider": "openai",
      "model": "rlm-gpt-4o-mini",
      "apiBase": "http://localhost:8000/v1"
    }
  ]
}
```

## 📝 License

Same as the parent RLM project.

## 🙏 Credits

Built on top of the RLM (Recursive Language Model) by [original authors].
