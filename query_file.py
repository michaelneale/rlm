#!/usr/bin/env python3
"""
Simple file query tool using RLM - query any large text file.
"""

import sys
from pathlib import Path
from rlm.rlm_repl import RLM_REPL

def query_file(file_path, question):
    """Query a text file using RLM."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return
    
    print(f"Loading {file_path.name}...")
    content = file_path.read_text(encoding='utf-8')
    
    rlm = RLM_REPL(
        model="gpt-4o-mini",
        recursive_model="gpt-4o-mini", 
        enable_logging=True,
        max_iterations=8
    )
    
    print(f"Question: {question}")
    print("=" * 50)
    
    result = rlm.completion(context=content, query=question)
    print(f"Answer: {result}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python query_file.py <file> <question>")
        print("Example: python query_file.py Codebase.txt 'What are the main components?'")
        sys.exit(1)
    
    query_file(sys.argv[1], " ".join(sys.argv[2:]))
