#!/usr/bin/env python3
"""
Interactive Codebase Query Tool using RLM

This script loads the Goose Rust codebase and allows you to query it
using the Recursive Language Model for deep code analysis.
"""

import sys
import os
from pathlib import Path
from rlm.rlm_repl import RLM_REPL

class CodebaseQueryTool:
    def __init__(self, codebase_path="Codebase.txt"):
        self.codebase_path = Path(codebase_path)
        self.codebase_content = None
        self.rlm = None
        
        # Initialize RLM with cost-effective settings
        self.rlm = RLM_REPL(
            model="gpt-4o-mini",  # Cost effective for large contexts
            recursive_model="gpt-4o-mini", 
            enable_logging=True,
            max_iterations=10  # Allow more iterations for complex code queries
        )
        
        self.load_codebase()
    
    def load_codebase(self):
        """Load the codebase file into memory."""
        if not self.codebase_path.exists():
            raise FileNotFoundError(f"Codebase file not found: {self.codebase_path}")
        
        print(f"📚 Loading codebase from {self.codebase_path}...")
        with open(self.codebase_path, 'r', encoding='utf-8') as f:
            self.codebase_content = f.read()
        
        # Get some stats
        lines = len(self.codebase_content.split('\n'))
        size_mb = len(self.codebase_content.encode('utf-8')) / (1024 * 1024)
        
        print(f"✅ Loaded codebase: {lines:,} lines, {size_mb:.1f}MB")
        print(f"🔍 Ready for queries!\n")
    
    def query(self, question):
        """Query the codebase using RLM."""
        if not self.codebase_content:
            raise ValueError("Codebase not loaded")
        
        print(f"🤔 Question: {question}")
        print("=" * 60)
        
        try:
            result = self.rlm.completion(
                context=self.codebase_content,
                query=question
            )
            
            print(f"\n🎯 ANSWER:")
            print("=" * 60)
            print(result)
            print("=" * 60)
            
            return result
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def interactive_mode(self):
        """Run in interactive mode for multiple queries."""
        print("🚀 Interactive Codebase Query Mode")
        print("Type your questions about the Goose Rust codebase.")
        print("Type 'quit', 'exit', or 'q' to exit.\n")
        
        while True:
            try:
                question = input("🔍 Your question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q', '']:
                    print("👋 Goodbye!")
                    break
                
                print("")  # Add spacing
                self.query(question)
                print("\n" + "="*60 + "\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break

def run_predefined_examples():
    """Run some example queries to test the system."""
    tool = CodebaseQueryTool()
    
    examples = [
        "What are the main crates in this goose project and what does each one do?",
        "How does the authentication system work in goose-server?",
        "What patterns are used for error handling across the codebase?",
        "How is the REPL or command execution implemented?",
        "What are the main data structures used in the goose core crate?"
    ]
    
    print("🧪 Running example queries...\n")
    
    for i, example in enumerate(examples, 1):
        print(f"\n{'='*20} EXAMPLE {i} {'='*20}")
        result = tool.query(example)
        
        if i < len(examples):
            input("\nPress Enter to continue to next example...")
    
    return tool

def single_query_mode(question):
    """Run a single query and exit."""
    tool = CodebaseQueryTool()
    tool.query(question)

def main():
    """Main function with different modes."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--examples":
            # Run predefined examples
            tool = run_predefined_examples()
            
            # Ask if user wants to continue interactively
            print("\n" + "="*60)
            choice = input("Continue with interactive mode? (y/N): ").strip().lower()
            if choice in ['y', 'yes']:
                tool.interactive_mode()
        else:
            # Single query mode
            question = " ".join(sys.argv[1:])
            single_query_mode(question)
    else:
        # Interactive mode
        tool = CodebaseQueryTool()
        tool.interactive_mode()

if __name__ == "__main__":
    main()
