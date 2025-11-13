#!/usr/bin/env python3
"""
Large file example: Query a huge codebase file using RLM via OpenAI API.
This demonstrates RLM's ability to handle contexts that exceed normal LLM limits.
"""

from openai import OpenAI
from pathlib import Path

# Connect to RLM server
client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")

# Load large codebase file (3.3MB+)
codebase_path = Path("../Codebase.txt")

if not codebase_path.exists():
    print(f"❌ {codebase_path} not found!")
    print("   Make sure Codebase.txt exists in the parent directory.")
    exit(1)

print(f"📚 Loading {codebase_path.name}...")
with open(codebase_path) as f:
    codebase = f.read()

size_mb = len(codebase) / (1024 * 1024)
print(f"✅ Loaded {size_mb:.1f}MB file\n")

# Query the large file
query = "What is this codebase about? Give a 2 sentence summary."
print(f"🔍 Query: {query}\n")
print("⏳ Processing (may take 30-60 seconds)...\n")

response = client.chat.completions.create(
    model="rlm-gpt-4o-mini",
    messages=[
        {"role": "system", "content": codebase},
        {"role": "user", "content": query}
    ]
)

print(f"💡 Answer:\n{response.choices[0].message.content}\n")
print(f"✅ Successfully processed {size_mb:.1f}MB file!")
