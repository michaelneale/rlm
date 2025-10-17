# RLM HTTP API Server Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `openai` - For client examples

### 2. Start the Server

```bash
python rlm_server.py
```

The server will start on `http://localhost:8000` by default.

You should see:
```
============================================================
🚀 RLM OpenAI-Compatible API Server Starting
============================================================
Server: http://localhost:8000
Base URL: http://localhost:8000/v1
============================================================

Available endpoints:
  POST /v1/chat/completions - Chat completions (tool calling supported)
  GET  /v1/models - List available models
  GET  /health - Health check
```

### 3. Use the API

#### Option A: Using OpenAI Python Client

```python
from openai import OpenAI

# Point OpenAI client to RLM server
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"  # Any value works
)

# Use exactly like OpenAI API!
response = client.chat.completions.create(
    model="gpt-4o-mini:gpt-4o",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

#### Option B: Using Environment Variables

```bash
export OPENAI_API_KEY="dummy"
export OPENAI_BASE_URL="http://localhost:8000/v1"

# Now any OpenAI client will use RLM!
python your_script.py
```

#### Option C: Using cURL

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini:gpt-4o",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

## Configuration

### Environment Variables

Set these before starting the server:

```bash
# Enable RLM logging (default: false)
export RLM_LOGGING=true

# Max iterations for RLM loop (default: 20)
export RLM_MAX_ITERATIONS=20

# Server port (default: 8000)
export PORT=8000

# Server host (default: 0.0.0.0)
export HOST=0.0.0.0
```

### Model Names

Models follow the format: `base_model:recursive_model`

Available models:
- `gpt-4o-mini:gpt-4o` - Fast outer model, powerful recursive model
- `gpt-4o:gpt-4o` - Powerful for both
- `gpt-4-turbo:gpt-4o` - GPT-4 Turbo outer, GPT-4o recursive
- `claude-3-5-sonnet-20241022:gpt-4o` - Claude outer, GPT-4o recursive

If you omit the recursive model, it defaults intelligently:
- `gpt-4o-mini` → uses `gpt-4o` for recursive calls
- `gpt-4o` → uses `gpt-4o` for recursive calls

## API Endpoints

### POST /v1/chat/completions

OpenAI-compatible chat completions endpoint.

**Request:**
```json
{
  "model": "gpt-4o-mini:gpt-4o",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello!"}
  ],
  "tools": [
    {
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
    }
  ]
}
```

**Response (no tool calls):**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-4o-mini:gpt-4o",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  }
}
```

**Response (with tool calls):**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-4o-mini:gpt-4o",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "get_weather",
              "arguments": "{\"location\": \"San Francisco\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

### GET /v1/models

List available models.

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4o-mini:gpt-4o",
      "object": "model",
      "created": 1234567890,
      "owned_by": "rlm"
    }
  ]
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "rlm-api"
}
```

### GET /

Root endpoint with server information.

## Features

### ✅ OpenAI-Compatible
- Drop-in replacement for OpenAI API
- Works with OpenAI Python client
- Compatible with any tool that uses OpenAI API

### ✅ Tool Calling
- Full support for function calling
- Multiple tool calls in one response
- Stateful sessions across tool call boundaries

### ✅ Massive Context Handling
- Handles 1M+ token contexts internally
- Automatic chunking via REPL
- No context length limits on your end

### ✅ Hybrid Intelligence
- External tools for real-world actions
- Internal REPL for massive context processing
- Both in the same conversation!

## Examples

### Example 1: Basic Chat

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"
)

response = client.chat.completions.create(
    model="gpt-4o-mini:gpt-4o",
    messages=[
        {"role": "user", "content": "Explain quantum computing"}
    ]
)

print(response.choices[0].message.content)
```

### Example 2: With Massive Context

```python
# Generate 1M lines of text
massive_context = "\n".join([f"Line {i}" for i in range(1000000)])

response = client.chat.completions.create(
    model="gpt-4o-mini:gpt-4o",
    messages=[
        {"role": "system", "content": massive_context},
        {"role": "user", "content": "Summarize the context"}
    ]
)

print(response.choices[0].message.content)
```

### Example 3: With Tool Calling

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_stock_price",
        "description": "Get current stock price",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"}
            },
            "required": ["symbol"]
        }
    }
}]

response = client.chat.completions.create(
    model="gpt-4o-mini:gpt-4o",
    messages=[
        {"role": "user", "content": "What's the stock price of AAPL?"}
    ],
    tools=tools
)

if response.choices[0].finish_reason == "tool_calls":
    # Execute tools and continue...
    tool_calls = response.choices[0].message.tool_calls
    # ... handle tool execution ...
```

### Example 4: Massive Context + Tools

```python
# This is RLM's superpower!
# Process huge logs AND call external tools

massive_logs = load_1m_lines_of_logs()

tools = [{
    "type": "function",
    "function": {
        "name": "create_ticket",
        "description": "Create a support ticket",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]}
            }
        }
    }
}]

response = client.chat.completions.create(
    model="gpt-4o-mini:gpt-4o",
    messages=[
        {"role": "system", "content": massive_logs},
        {"role": "user", "content": "Find critical errors and create tickets for them"}
    ],
    tools=tools
)

# RLM will:
# 1. Process massive logs internally via REPL
# 2. Return tool calls to create tickets
# 3. Continue after you execute the tools
```

## Running the Examples

We provide complete examples:

```bash
# Terminal 1: Start server
python rlm_server.py

# Terminal 2: Run client examples
python example_client.py
```

The `example_client.py` includes:
1. Basic chat
2. Massive context handling
3. Tool calling
4. Massive context + tools (RLM's unique capability!)

## Troubleshooting

### Server won't start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Connection refused

**Error:** `Connection refused at localhost:8000`

**Solution:** Make sure server is running
```bash
python rlm_server.py
```

### API key error

**Error:** `Invalid API key`

**Solution:** You can use any API key with RLM server
```python
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"  # Any value works!
)
```

### Model not found

**Error:** `Model 'xyz' not found`

**Solution:** Use the format `base_model:recursive_model` or one of the predefined models
```python
# Good
model="gpt-4o-mini:gpt-4o"

# Also good (uses smart defaults)
model="gpt-4o-mini"

# Bad
model="some-random-model"
```

## Advanced Usage

### Custom Port

```bash
PORT=9000 python rlm_server.py
```

Then use:
```python
client = OpenAI(
    base_url="http://localhost:9000/v1",
    api_key="dummy"
)
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PORT=8000
ENV RLM_LOGGING=false

CMD ["python", "rlm_server.py"]
```

```bash
docker build -t rlm-server .
docker run -p 8000:8000 rlm-server
```

### Behind Nginx

```nginx
server {
    listen 80;
    server_name rlm.example.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Performance Tips

1. **Use faster models for outer loop**: `gpt-4o-mini:gpt-4o` is recommended
2. **Adjust max iterations**: Set `RLM_MAX_ITERATIONS` based on your use case
3. **Cache clients**: The server caches RLM clients per model
4. **Monitor logs**: Enable `RLM_LOGGING=true` to debug

## Integration Examples

### With LangChain

```python
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(
    openai_api_base="http://localhost:8000/v1",
    openai_api_key="dummy",
    model_name="gpt-4o-mini:gpt-4o"
)

response = llm.predict("Hello!")
```

### With LlamaIndex

```python
from llama_index.llms import OpenAI

llm = OpenAI(
    api_base="http://localhost:8000/v1",
    api_key="dummy",
    model="gpt-4o-mini:gpt-4o"
)

response = llm.complete("Hello!")
```

### With Any OpenAI-Compatible Tool

Just set:
```bash
export OPENAI_API_BASE="http://localhost:8000/v1"
export OPENAI_API_KEY="dummy"
```

Then use your tool normally!

## Support

- **Issues**: Check `llm-adapter.md` for implementation details
- **Examples**: See `example_client.py` for working code
- **API Reference**: OpenAI API documentation applies

## License

Same as the RLM project.
