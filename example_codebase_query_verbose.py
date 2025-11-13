#!/usr/bin/env python3
"""
Verbose version with direct requests to see RLM working with logging enabled.
"""

import requests
from pathlib import Path
import time


def main():
    # Load the large codebase file
    codebase_path = Path("Codebase.txt")
    if not codebase_path.exists():
        print(f"❌ {codebase_path} not found!")
        return
    
    print(f"📚 Loading {codebase_path} ({codebase_path.stat().st_size / 1024 / 1024:.1f}MB)...")
    with open(codebase_path, "r", encoding="utf-8") as f:
        codebase = f.read()
    
    print("✅ Loaded!\n")
    
    # Simple query with verbose logging
    query = "What is this codebase about? Give me a 2 sentence summary."
    
    print(f"📝 Query: {query}\n")
    print("⏳ Processing with verbose logging enabled...")
    print("   (Watch the server terminal for detailed RLM iterations)\n")
    
    start = time.time()
    
    # Make direct request with logging enabled
    response = requests.post(
        "http://localhost:8000/v1/chat/completions",
        json={
            "model": "rlm-gpt-4o-mini",
            "messages": [
                {"role": "system", "content": codebase},
                {"role": "user", "content": query}
            ],
            "max_iterations": 10,
            "enable_logging": True  # Enable verbose logging!
        },
        timeout=300  # 5 minute timeout
    )
    
    elapsed = time.time() - start
    
    if response.status_code == 200:
        result = response.json()
        answer = result["choices"][0]["message"]["content"]
        print(f"✅ Completed in {elapsed:.1f}s\n")
        print(f"💡 Answer:\n{answer}\n")
        print(f"📊 Token usage: {result['usage']['total_tokens']} tokens")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n🔧 Make sure the server is running!")
