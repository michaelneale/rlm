# 🚀 Quick Start Guide: OpenAI RLM API

Get up and running with the OpenAI-compatible RLM server in 3 steps!

## Step 1: Install Dependencies

```bash
pip install -r requirements_server.txt
```

Or install individually:
```bash
pip install fastapi uvicorn pydantic openai requests
```

## Step 2: Set Your API Key

```bash
export OPENAI_API_KEY="sk-your-key-here"
```

## Step 3: Start the Server

```bash
python openai_rlm_server.py
```

You should see:
```
╔════════════════════════════════════════════════════════════════╗
║                  RLM OpenAI-Compatible API                     ║
╠════════════════════════════════════════════════════════════════╣
║  Server running at: http://0.0.0.0:8000                       ║
║  ...                                                           ║
╚════════════════════════════════════════════════════════════════╝
```

## 🎯 Try It Out!

### Option A: Run Example with Codebase.txt

```bash
# In a new terminal
python example_codebase_query.py
```

This will query your large `Codebase.txt` file with example questions!

### Option B: Run Tests

```bash
python test_openai_rlm.py
```

### Option C: Use Python Directly

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"
)

# Load a huge file
with open("Codebase.txt") as f:
    huge_text = f.read()

# Query it!
response = client.chat.completions.create(
    model="rlm-gpt-4o-mini",
    messages=[
        {"role": "system", "content": huge_text},
        {"role": "user", "content": "Summarize this codebase"}
    ]
)

print(response.choices[0].message.content)
```

### Option D: Use curl

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "rlm-gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Hello RLM!"}
    ]
  }'
```

## 📊 What's Different?

| Standard LLM | RLM via OpenAI API |
|--------------|-------------------|
| ❌ Fails with 3MB files | ✅ Handles 3MB+ easily |
| ❌ Context limit ~200K tokens | ✅ Virtually unlimited |
| ✅ Single API call | ⚠️ Multiple recursive calls |
| ✅ Fast response | ⚠️ Slower (more thorough) |

## 🎨 Use Cases

### 1. Analyze Entire Codebases
```python
# 3MB+ codebase? No problem!
with open("Codebase.txt") as f:
    code = f.read()

response = client.chat.completions.create(
    model="rlm-gpt-4o-mini",
    messages=[
        {"role": "system", "content": code},
        {"role": "user", "content": "Find all security vulnerabilities"}
    ]
)
```

### 2. Process Long Documents
```python
# Books, legal docs, research papers
with open("document.txt") as f:
    doc = f.read()

response = client.chat.completions.create(
    model="rlm-gpt-4o-mini",
    messages=[
        {"role": "system", "content": doc},
        {"role": "user", "content": "Extract key findings"}
    ]
)
```

### 3. Multi-file Analysis
```python
# Combine multiple files
context = ""
for file in ["file1.py", "file2.py", "file3.py"]:
    with open(file) as f:
        context += f"\n# {file}\n{f.read()}\n"

response = client.chat.completions.create(
    model="rlm-gpt-4o-mini",
    messages=[
        {"role": "system", "content": context},
        {"role": "user", "content": "How do these files interact?"}
    ]
)
```

## ⚙️ Configuration

### Adjust Recursive Depth
```python
response = client.chat.completions.create(
    model="rlm-gpt-4o-mini",
    messages=[...],
    max_iterations=20  # More iterations = more thorough
)
```

### Enable Debug Logging
```python
response = client.chat.completions.create(
    model="rlm-gpt-4o-mini",
    messages=[...],
    enable_logging=True  # See what's happening
)
```

### Change Models
```python
# More powerful (costs more)
response = client.chat.completions.create(
    model="rlm-gpt-4o",  # Instead of gpt-4o-mini
    messages=[...]
)
```

## 🐛 Troubleshooting

### Server won't start
```bash
# Check if port 8000 is in use
lsof -ti:8000 | xargs kill -9

# Try different port
python openai_rlm_server.py --port 8001
```

### "OPENAI_API_KEY not set"
```bash
# Set it in your shell
export OPENAI_API_KEY="sk-..."

# Or create .env file
echo "OPENAI_API_KEY=sk-..." > .env
```

### Timeouts on large files
```python
# Increase iterations
response = client.chat.completions.create(
    model="rlm-gpt-4o-mini",
    messages=[...],
    max_iterations=30  # Default is 10
)
```

## 📚 Learn More

- **Full Documentation**: See `OPENAI_RLM_README.md`
- **API Reference**: Visit `http://localhost:8000/docs` when server is running
- **Examples**: Check `example_codebase_query.py`
- **Tests**: Run `test_openai_rlm.py`

## 💡 Pro Tips

1. **Start small**: Test with small files first, then scale up
2. **Use mini model**: `rlm-gpt-4o-mini` is cost-effective for most tasks
3. **Adjust iterations**: Complex queries need more iterations (15-20)
4. **System messages**: Put large context in system message, question in user message
5. **Enable logging**: Use `enable_logging=True` to understand what's happening

## 🎉 That's It!

You now have an OpenAI-compatible API that can handle **arbitrarily large contexts**.

Try it with your 3.3MB `Codebase.txt` file! 🚀
