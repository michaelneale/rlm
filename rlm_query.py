"""
Shared query logic for both CLI and MCP server.
"""

import os
from pathlib import Path
from rlm.rlm_repl import RLM_REPL


def query_text(text: str, query: str, max_iterations: int = 10, enable_logging: bool = False) -> str:
    """
    Query text using RLM.
    
    Args:
        text: The text/document to query
        query: The question to ask
        max_iterations: Maximum RLM iterations
        enable_logging: Whether to show RLM iterations
    
    Returns:
        The answer from RLM
    """
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    # Initialize RLM
    rlm = RLM_REPL(
        model="gpt-4o-mini",
        recursive_model="gpt-4o-mini",
        max_iterations=max_iterations,
        enable_logging=enable_logging,
    )
    
    # Run query
    result = rlm.completion(context=text, query=query)
    return result


def query_file(file_path: str, query: str, max_iterations: int = 10, enable_logging: bool = False) -> str:
    """
    Query a file using RLM.
    
    Args:
        file_path: Path to the file
        query: The question to ask
        max_iterations: Maximum RLM iterations
        enable_logging: Whether to show RLM iterations
    
    Returns:
        The answer from RLM
    """
    # Load file
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Use shared query_text logic
    return query_text(text, query, max_iterations, enable_logging)
