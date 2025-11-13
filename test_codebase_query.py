#!/usr/bin/env python3
"""
Quick test of the codebase query functionality.
"""

from query_codebase import CodebaseQueryTool

def test_quick_query():
    """Test with a simple query to verify everything works."""
    print("🧪 Testing Codebase Query Tool...")
    
    try:
        tool = CodebaseQueryTool()
        
        # Simple test query
        question = "What are the main crates in this goose project?"
        print(f"\n🔍 Testing with: '{question}'\n")
        
        result = tool.query(question)
        
        if result:
            print("\n✅ Test successful! The codebase query tool is working.")
        else:
            print("\n❌ Test failed - no result returned.")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_quick_query()
