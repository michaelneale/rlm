#!/usr/bin/env python3
"""
Optimized Codebase Query Tool using RLM with chunking strategies

This version handles large codebases more efficiently by using smart chunking
and progressive context building.
"""

import sys
import os
import re
from pathlib import Path
from rlm.rlm_repl import RLM_REPL

class OptimizedCodebaseQueryTool:
    def __init__(self, codebase_path="Codebase.txt"):
        self.codebase_path = Path(codebase_path)
        self.codebase_content = None
        self.files_index = {}  # Index of file locations
        self.rlm = None
        
        # Initialize RLM with optimized settings for large contexts
        self.rlm = RLM_REPL(
            model="gpt-4o-mini",
            recursive_model="gpt-4o-mini", 
            enable_logging=True,
            max_iterations=8
        )
        
        self.load_and_index_codebase()
    
    def load_and_index_codebase(self):
        """Load and create an index of the codebase."""
        if not self.codebase_path.exists():
            raise FileNotFoundError(f"Codebase file not found: {self.codebase_path}")
        
        print(f"📚 Loading and indexing codebase from {self.codebase_path}...")
        
        with open(self.codebase_path, 'r', encoding='utf-8') as f:
            self.codebase_content = f.read()
        
        # Create file index for efficient retrieval
        self._build_file_index()
        
        # Stats
        lines = len(self.codebase_content.split('\n'))
        size_mb = len(self.codebase_content.encode('utf-8')) / (1024 * 1024)
        num_files = len(self.files_index)
        
        print(f"✅ Loaded codebase: {lines:,} lines, {size_mb:.1f}MB, {num_files} files")
        print(f"🔍 Ready for optimized queries!\n")
    
    def _build_file_index(self):
        """Build an index of file locations for efficient access."""
        pattern = r'// FILE: (.*?)\n// ============================================================================'
        matches = re.finditer(pattern, self.codebase_content)
        
        prev_end = 0
        for match in matches:
            if prev_end > 0:  # Not the first file
                # Store the previous file's content
                prev_file_content = self.codebase_content[prev_end:match.start()]
                # Get the filename from the previous match
                prev_files = list(self.files_index.keys())
                if prev_files:
                    self.files_index[prev_files[-1]]['content'] = prev_file_content.strip()
            
            file_path = match.group(1)
            self.files_index[file_path] = {
                'start': match.end(),
                'content': None  # Will be filled next iteration
            }
            prev_end = match.end()
        
        # Handle the last file
        if prev_end > 0:
            last_files = list(self.files_index.keys())
            if last_files:
                last_content = self.codebase_content[prev_end:].strip()
                self.files_index[last_files[-1]]['content'] = last_content
    
    def get_crate_overview(self):
        """Get a high-level overview of all crates."""
        crates_summary = {}
        
        for file_path in self.files_index.keys():
            parts = file_path.split('/')
            if len(parts) >= 3:  # ./crates/crate-name/...
                crate_name = parts[2]
                if crate_name not in crates_summary:
                    crates_summary[crate_name] = []
                crates_summary[crate_name].append(file_path)
        
        overview = "# Goose Rust Codebase Overview\n\n"
        for crate, files in crates_summary.items():
            overview += f"## {crate} ({len(files)} files)\n"
            # Show key files
            key_files = [f for f in files if any(key in f for key in ['main.rs', 'lib.rs', 'mod.rs'])]
            if key_files:
                overview += "Key files: " + ", ".join([f.split('/')[-1] for f in key_files[:3]]) + "\n"
            overview += f"Files: {', '.join([f.split('/')[-1] for f in files[:5]])}"
            if len(files) > 5:
                overview += f" ... and {len(files)-5} more"
            overview += "\n\n"
        
        return overview
    
    def get_relevant_files(self, query, max_files=10):
        """Get files most relevant to the query."""
        query_lower = query.lower()
        keywords = query_lower.split()
        
        scored_files = []
        
        for file_path, file_data in self.files_index.items():
            score = 0
            file_path_lower = file_path.lower()
            
            # Score based on file path
            for keyword in keywords:
                if keyword in file_path_lower:
                    score += 2
            
            # Score based on content (if available)
            if file_data.get('content'):
                content_lower = file_data['content'][:2000].lower()  # First 2K chars
                for keyword in keywords:
                    score += content_lower.count(keyword)
            
            if score > 0:
                scored_files.append((file_path, score))
        
        # Sort by score and return top files
        scored_files.sort(key=lambda x: x[1], reverse=True)
        return [f[0] for f in scored_files[:max_files]]
    
    def build_focused_context(self, query):
        """Build a focused context based on the query."""
        # Start with overview
        context = self.get_crate_overview()
        context += "\n" + "="*60 + "\n"
        context += "# RELEVANT SOURCE FILES\n\n"
        
        # Get relevant files
        relevant_files = self.get_relevant_files(query, max_files=8)
        
        if not relevant_files:
            # Fall back to a sample of files from each crate
            context += "# SAMPLE FILES FROM EACH CRATE\n\n"
            added_crates = set()
            for file_path in list(self.files_index.keys())[:20]:  # First 20 files
                crate = file_path.split('/')[2] if len(file_path.split('/')) > 2 else 'unknown'
                if crate not in added_crates:
                    context += f"// FILE: {file_path}\n"
                    context += self.files_index[file_path].get('content', '')[:3000]  # First 3K chars
                    context += "\n\n"
                    added_crates.add(crate)
                    if len(added_crates) >= 6:  # Max 6 crates
                        break
        else:
            # Add relevant files
            for file_path in relevant_files:
                context += f"// FILE: {file_path}\n"
                context += self.files_index[file_path].get('content', '')[:4000]  # First 4K chars
                context += "\n\n"
        
        return context
    
    def query(self, question):
        """Query the codebase using RLM with optimized context."""
        print(f"🤔 Question: {question}")
        print("=" * 60)
        
        try:
            # Build focused context instead of using entire codebase
            focused_context = self.build_focused_context(question)
            
            print(f"📊 Using focused context: {len(focused_context):,} characters")
            
            result = self.rlm.completion(
                context=focused_context,
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
        """Run in interactive mode."""
        print("🚀 Optimized Interactive Codebase Query Mode")
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

def main():
    """Main function."""
    if len(sys.argv) > 1:
        # Single query mode
        question = " ".join(sys.argv[1:])
        tool = OptimizedCodebaseQueryTool()
        tool.query(question)
    else:
        # Interactive mode
        tool = OptimizedCodebaseQueryTool()
        tool.interactive_mode()

if __name__ == "__main__":
    main()
