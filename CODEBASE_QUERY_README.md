# Codebase Query Tool

Interactive tool for querying the Goose Rust codebase using RLM (Recursive Language Models).

## Files Created

- `Codebase.txt` - Complete Goose Rust source code (3.4MB, 96K+ lines)
- `query_codebase.py` - Main interactive query tool  
- `test_codebase_query.py` - Quick test script

## Usage

### 1. Interactive Mode (Recommended)
```bash
python query_codebase.py
```
This starts an interactive session where you can ask multiple questions.

### 2. Single Query Mode
```bash
python query_codebase.py "What are the main data structures in goose?"
```
Ask one question and get an answer.

### 3. Example Queries Mode  
```bash
python query_codebase.py --examples
```
Runs predefined example queries to demonstrate capabilities.

### 4. Quick Test
```bash
python test_codebase_query.py
```
Runs a simple test to verify everything works.

## Example Questions You Can Ask

**Architecture & Overview:**
- "What are the main crates and what does each one do?"
- "What's the overall architecture of the goose system?"
- "How do the different crates interact with each other?"

**Specific Implementation:**
- "How does the authentication system work in goose-server?"
- "How is command execution implemented?"
- "What error handling patterns are used?"
- "How does the session management work?"

**Code Analysis:**
- "What are the main traits defined in the codebase?"
- "How is configuration handled across the crates?"
- "What async patterns are used?"
- "How are external tools integrated?"

**Development:**
- "What testing patterns are used?"
- "How is logging implemented?"
- "What are the main dependencies?"

## How It Works

1. **Loads** the entire Goose Rust codebase (96K+ lines) into RLM context
2. **Uses** GPT-4o-mini for cost-effective processing of large contexts
3. **Applies** Recursive Language Model techniques to break down complex queries
4. **Provides** detailed answers based on the actual source code

## Features

- 🔍 **Interactive querying** - Ask follow-up questions
- 🧠 **Intelligent analysis** - RLM breaks down complex questions
- 💰 **Cost-effective** - Uses gpt-4o-mini for processing
- 📊 **Rich logging** - See how RLM processes your queries
- 🎯 **Accurate results** - Based on actual source code, not documentation

## Tips for Better Queries

- Be specific about what aspect you're interested in
- Ask about patterns, architectures, and implementations
- Follow up with clarifying questions
- Ask for code examples or specific file references

Enjoy exploring the Goose codebase! 🚀
