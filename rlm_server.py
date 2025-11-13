#!/usr/bin/env python3
"""
OpenAI-compatible API server for RLM (Recursive Language Model)

This provides a simple OpenAI-compatible interface to RLM, allowing it to handle
arbitrarily large contexts by recursively processing them.

Usage:
    python openai_rlm_server.py

Then make requests like:
    curl http://localhost:8000/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d '{
        "model": "rlm-gpt-4o-mini",
        "messages": [{"role": "user", "content": "Your question here"}]
      }'

Or use the OpenAI Python client:
    from openai import OpenAI
    client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")
    response = client.chat.completions.create(
        model="rlm-gpt-4o-mini",
        messages=[{"role": "user", "content": "Your question"}]
    )
"""

import os
import time
import uuid
from typing import List, Dict, Optional, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

from rlm.rlm_repl import RLM_REPL


# ============================================================================
# Request/Response Models (OpenAI-compatible)
# ============================================================================

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    # RLM-specific parameters (allow extra fields)
    max_iterations: Optional[int] = 10
    enable_logging: Optional[bool] = True  # Default to True so you can see what's happening
    
    model_config = {"extra": "allow"}  # Allow extra fields from OpenAI client

class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: str

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Usage

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = int(time.time())
    owned_by: str = "rlm"

class ModelList(BaseModel):
    object: str = "list"
    data: List[ModelInfo]


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="RLM OpenAI-Compatible API",
    description="OpenAI-compatible API for Recursive Language Model",
    version="1.0.0"
)


# ============================================================================
# Helper Functions
# ============================================================================

def extract_context_and_query(messages: List[Message]) -> tuple[str, str]:
    """
    Extract context and query from the message list.
    
    Strategy:
    - System message content becomes the context (as a string)
    - Last user message becomes the query
    - If no system message, concatenate all non-user messages as context
    """
    if not messages:
        raise ValueError("No messages provided")
    
    # Find last user message as query
    query = None
    for msg in reversed(messages):
        if msg.role == "user":
            query = msg.content
            break
    
    if not query:
        raise ValueError("No user message found")
    
    # Get context from system message or concatenate other messages
    context_parts = []
    for msg in messages:
        if msg.role == "system":
            # System message is the main context
            context_parts.append(msg.content)
        elif msg.role != "user":
            # Include assistant messages too
            context_parts.append(msg.content)
    
    # Join all context parts, or use empty string if none
    context = "\n\n".join(context_parts) if context_parts else ""
    
    return context, query


def parse_model_params(model: str) -> tuple[str, str]:
    """
    Parse model string to extract base model and recursive model.
    
    Formats:
    - "rlm-gpt-4o-mini" -> base: gpt-4o-mini, recursive: gpt-4o-mini
    - "rlm-gpt-4o" -> base: gpt-4o, recursive: gpt-4o-mini
    - "gpt-4o-mini" -> base: gpt-4o-mini, recursive: gpt-4o-mini
    """
    # Remove 'rlm-' prefix if present
    model_clean = model.replace("rlm-", "")
    
    # Default recursive model is cost-effective mini
    recursive_model = "gpt-4o-mini"
    base_model = model_clean or "gpt-4o-mini"
    
    # Use the same model for both if specified
    if model_clean:
        base_model = model_clean
    
    return base_model, recursive_model


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "RLM OpenAI-Compatible API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "chat_completions": "/v1/chat/completions",
            "models": "/v1/models"
        }
    }


@app.get("/v1/models")
async def list_models():
    """List available models."""
    models = [
        ModelInfo(id="rlm-gpt-4o-mini"),
        ModelInfo(id="rlm-gpt-4o"),
        ModelInfo(id="gpt-4o-mini"),
        ModelInfo(id="gpt-4o"),
    ]
    return ModelList(data=models)


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions endpoint.
    
    This endpoint accepts standard OpenAI chat completion requests and
    processes them using RLM for handling large contexts.
    """
    try:
        # Parse model parameters
        base_model, recursive_model = parse_model_params(request.model)
        
        # Extract context and query from messages
        context, query = extract_context_and_query(request.messages)
        
        # Initialize RLM
        rlm = RLM_REPL(
            model=base_model,
            recursive_model=recursive_model,
            max_iterations=request.max_iterations,
            enable_logging=request.enable_logging
        )
        
        # Get completion from RLM
        start_time = time.time()
        result = rlm.completion(context=context, query=query)
        elapsed_time = time.time() - start_time
        
        # Build OpenAI-compatible response
        response = ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
            created=int(start_time),
            model=request.model,
            choices=[
                Choice(
                    index=0,
                    message=Message(role="assistant", content=result),
                    finish_reason="stop"
                )
            ],
            usage=Usage(
                # We don't track exact tokens, but give estimates
                prompt_tokens=sum(len(m.content) // 4 for m in request.messages),
                completion_tokens=len(result) // 4,
                total_tokens=(sum(len(m.content) for m in request.messages) + len(result)) // 4
            )
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """Run the server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="RLM OpenAI-Compatible API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║                  RLM OpenAI-Compatible API                     ║
╠════════════════════════════════════════════════════════════════╣
║  Server running at: http://{args.host}:{args.port}              ║
║  API Documentation: http://{args.host}:{args.port}/docs        ║
║                                                                ║
║  Endpoints:                                                    ║
║    • POST /v1/chat/completions                                ║
║    • GET  /v1/models                                          ║
║                                                                ║
║  Example usage with curl:                                     ║
║    curl http://localhost:{args.port}/v1/chat/completions \\      ║
║      -H "Content-Type: application/json" \\                    ║
║      -d '{{"model": "rlm-gpt-4o-mini",                         ║
║           "messages": [{{"role": "user",                       ║
║                        "content": "Hello!"}}]}}'               ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "rlm_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
