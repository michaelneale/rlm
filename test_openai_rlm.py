#!/usr/bin/env python3
"""
Test client for the OpenAI-compatible RLM server.

This demonstrates how to use the RLM server with both:
1. The OpenAI Python client
2. Direct HTTP requests
3. Loading and querying large files (like Codebase.txt)
"""

import sys
from pathlib import Path


def test_with_openai_client():
    """Test using the official OpenAI Python client."""
    print("=" * 70)
    print("TEST 1: Using OpenAI Python Client")
    print("=" * 70)
    
    try:
        from openai import OpenAI
    except ImportError:
        print("❌ OpenAI package not installed. Install with: pip install openai")
        return
    
    # Point to our RLM server instead of OpenAI
    client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="dummy"  # RLM doesn't need a real key
    )
    
    # Simple test
    print("\n📝 Simple query...")
    response = client.chat.completions.create(
        model="rlm-gpt-4o-mini",
        messages=[
            {"role": "user", "content": "What is 2+2?"}
        ]
    )
    
    print(f"✅ Response: {response.choices[0].message.content}")
    print(f"   Usage: {response.usage.total_tokens} tokens\n")


def test_with_large_context():
    """Test with a large context (like Codebase.txt)."""
    print("=" * 70)
    print("TEST 2: Large Context Query")
    print("=" * 70)
    
    try:
        from openai import OpenAI
    except ImportError:
        print("❌ OpenAI package not installed")
        return
    
    # Check if Codebase.txt exists
    codebase_path = Path("Codebase.txt")
    if not codebase_path.exists():
        print(f"⚠️  Codebase.txt not found at {codebase_path.absolute()}")
        print("   Creating a sample large text file instead...")
        
        # Create sample large context
        large_text = "\n".join([
            f"This is line {i}. It contains information about topic {i % 10}."
            for i in range(1000)
        ])
    else:
        print(f"📚 Loading {codebase_path} ({codebase_path.stat().st_size / 1024 / 1024:.1f}MB)...")
        with open(codebase_path, 'r', encoding='utf-8') as f:
            large_text = f.read()
    
    client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="dummy"
    )
    
    print("\n🔍 Querying the large context...")
    response = client.chat.completions.create(
        model="rlm-gpt-4o-mini",
        messages=[
            {"role": "system", "content": large_text},
            {"role": "user", "content": "Summarize the main topics in this codebase in 3 bullet points."}
        ],
        max_iterations=5  # RLM-specific parameter
    )
    
    print(f"\n✅ Response:")
    print(response.choices[0].message.content)
    print(f"\n   Usage: {response.usage.total_tokens} tokens")


def test_with_curl():
    """Show example curl command."""
    print("\n" + "=" * 70)
    print("TEST 3: Using curl")
    print("=" * 70)
    
    curl_command = """
curl http://localhost:8000/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "rlm-gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Hello, RLM!"}
    ],
    "max_iterations": 5
  }'
"""
    
    print("\n📋 Example curl command:")
    print(curl_command)
    
    print("\n💡 Or test with httpie:")
    print("   http POST localhost:8000/v1/chat/completions \\")
    print('     model=rlm-gpt-4o-mini \\')
    print('     messages:=\'[{"role":"user","content":"Hello!"}]\'')


def test_models_endpoint():
    """Test the models endpoint."""
    print("\n" + "=" * 70)
    print("TEST 4: List Available Models")
    print("=" * 70)
    
    import requests
    
    try:
        response = requests.get("http://localhost:8000/v1/models")
        response.raise_for_status()
        
        models = response.json()
        print("\n📋 Available models:")
        for model in models.get("data", []):
            print(f"   • {model['id']}")
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Start it with: python openai_rlm_server.py")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all tests."""
    print("\n🧪 RLM OpenAI-Compatible API Test Suite\n")
    
    # Check if server is running
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is running!\n")
        else:
            print("⚠️  Server returned unexpected status\n")
    except:
        print("❌ Server not running!")
        print("   Start it with: python openai_rlm_server.py")
        print("   Then run this test again.\n")
        sys.exit(1)
    
    # Run tests
    test_models_endpoint()
    test_with_openai_client()
    test_with_curl()
    
    # Optional: large context test (may take time)
    print("\n" + "=" * 70)
    try:
        choice = input("\n⏱️  Run large context test? (may take 1-2 minutes) [y/N]: ")
        if choice.lower() == 'y':
            test_with_large_context()
    except EOFError:
        print("\n⏭️  Skipping large context test (no interactive input)")
        pass
    
    print("\n" + "=" * 70)
    print("✅ All tests complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
