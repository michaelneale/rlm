#!/usr/bin/env python3
"""
Simple example: Query Codebase.txt using the OpenAI RLM API

This demonstrates how easy it is to query large files using the
OpenAI-compatible interface.
"""

from openai import OpenAI
from pathlib import Path


def main():
    # Connect to the RLM server
    client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="dummy"  # Not needed
    )
    
    # Load the large codebase file
    codebase_path = Path("Codebase.txt")
    if not codebase_path.exists():
        print(f"❌ {codebase_path} not found!")
        print("   Make sure you're in the right directory.")
        return
    
    print(f"📚 Loading {codebase_path} ({codebase_path.stat().st_size / 1024 / 1024:.1f}MB)...")
    with open(codebase_path, "r", encoding="utf-8") as f:
        codebase = f.read()
    
    print("✅ Loaded!\n")
    
    # Example queries
    queries = [
        "What is this codebase about? Give me a 3 sentence summary.",
        "What are the main modules or components?",
        "Find any TODO or FIXME comments.",
    ]
    
    print("🔍 Running example queries...\n")
    print("=" * 70)
    
    for i, query in enumerate(queries, 1):
        print(f"\n📝 Query {i}: {query}\n")
        print("⏳ Processing (this may take 30-60 seconds for large contexts)...")
        
        import time
        start = time.time()
        
        response = client.chat.completions.create(
            model="rlm-gpt-4o-mini",
            messages=[
                {"role": "system", "content": codebase},
                {"role": "user", "content": query}
            ]
            # Note: max_iterations can be set via direct API calls
            # For OpenAI client, use extra_body or direct requests
        )
        
        elapsed = time.time() - start
        answer = response.choices[0].message.content
        print(f"✅ Completed in {elapsed:.1f}s")
        print(f"\n💡 Answer:\n{answer}\n")
        print("-" * 70)
    
    print("\n✅ Done!")
    print("\n💡 Try your own query:")
    print("   Just modify the queries list or run interactively!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n🔧 Make sure:")
        print("   1. The RLM server is running: python openai_rlm_server.py")
        print("   2. You have OPENAI_API_KEY set in your environment")
        print("   3. Dependencies are installed: pip install -r requirements_server.txt")
