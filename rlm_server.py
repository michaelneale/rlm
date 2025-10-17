"""
OpenAI-compatible HTTP API server for RLM.

This server exposes RLM as a localhost endpoint compatible with OpenAI's API format.
You can use it as a drop-in replacement for OpenAI by pointing clients to:
    http://localhost:8000/v1

Example usage:
    python rlm_server.py
    
Then use with OpenAI client:
    from openai import OpenAI
    client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")
    response = client.chat.completions.create(...)
"""

import os
import time
import uuid
from typing import List, Optional, Dict, Any, Literal
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from rlm.rlm_api import create_rlm_client


# Pydantic models for OpenAI API compatibility
class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


class FunctionDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class Tool(BaseModel):
    type: Literal["function"]
    function: FunctionDefinition


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    tools: Optional[List[Tool]] = None
    tool_choice: Optional[str] = None
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[List[str]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionChoice(BaseModel):
    index: int
    message: Message
    finish_reason: str


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[Usage] = None


class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str = "rlm"


class ModelListResponse(BaseModel):
    object: str = "list"
    data: List[ModelInfo]


# Global RLM client cache
rlm_clients: Dict[str, Any] = {}


def get_rlm_client(model: str, recursive_model: Optional[str] = None):
    """Get or create RLM client for a model."""
    # Parse model name to extract recursive model if specified
    # Format: "model_name:recursive_model_name"
    if ":" in model:
        base_model, recursive_model = model.split(":", 1)
    else:
        base_model = model
        if recursive_model is None:
            # Default mapping
            recursive_model = "gpt-4o" if "nano" in model or "mini" in model else model
    
    cache_key = f"{base_model}:{recursive_model}"
    
    if cache_key not in rlm_clients:
        print(f"Creating RLM client: {base_model} (recursive: {recursive_model})")
        rlm_clients[cache_key] = create_rlm_client(
            model=base_model,
            recursive_model=recursive_model,
            enable_logging=os.getenv("RLM_LOGGING", "false").lower() == "true",
            max_iterations=int(os.getenv("RLM_MAX_ITERATIONS", "20"))
        )
    
    return rlm_clients[cache_key]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print("=" * 60)
    print("🚀 RLM OpenAI-Compatible API Server Starting")
    print("=" * 60)
    print(f"Server: http://localhost:{os.getenv('PORT', '8000')}")
    print(f"Base URL: http://localhost:{os.getenv('PORT', '8000')}/v1")
    print("=" * 60)
    print("\nAvailable endpoints:")
    print("  POST /v1/chat/completions - Chat completions (tool calling supported)")
    print("  GET  /v1/models - List available models")
    print("  GET  /health - Health check")
    print("\nEnvironment variables:")
    print(f"  RLM_LOGGING={os.getenv('RLM_LOGGING', 'false')}")
    print(f"  RLM_MAX_ITERATIONS={os.getenv('RLM_MAX_ITERATIONS', '20')}")
    print(f"  PORT={os.getenv('PORT', '8000')}")
    print("\nExample usage:")
    print('  export OPENAI_API_KEY="dummy"')
    print('  export OPENAI_BASE_URL="http://localhost:8000/v1"')
    print("  # Then use OpenAI client normally!")
    print("=" * 60)
    yield
    print("\n🛑 RLM Server Shutting Down")


# Create FastAPI app
app = FastAPI(
    title="RLM OpenAI-Compatible API",
    description="OpenAI-compatible API server for Recursive Language Models",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "rlm-api"}


@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI-compatible)."""
    models = [
        ModelInfo(id="gpt-4o-mini:gpt-4o", created=int(time.time())),
        ModelInfo(id="gpt-4o:gpt-4o", created=int(time.time())),
        ModelInfo(id="gpt-4-turbo:gpt-4o", created=int(time.time())),
        ModelInfo(id="claude-3-5-sonnet-20241022:gpt-4o", created=int(time.time())),
    ]
    return ModelListResponse(data=models)


@app.post("/v1/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest):
    """
    Create chat completion (OpenAI-compatible).
    
    Supports:
    - Tool calling (function calling)
    - Massive contexts via RLM internal processing
    - Standard chat completions
    """
    try:
        # Get RLM client
        client = get_rlm_client(request.model)
        
        # Convert request to RLM format
        messages = [
            {
                "role": msg.role,
                "content": msg.content,
                **({"tool_calls": msg.tool_calls} if msg.tool_calls else {}),
                **({"tool_call_id": msg.tool_call_id, "name": msg.name} if msg.tool_call_id else {})
            }
            for msg in request.messages
        ]
        
        # Convert tools to OpenAI format
        tools = None
        if request.tools:
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.function.name,
                        "description": tool.function.description,
                        "parameters": tool.function.parameters or {}
                    }
                }
                for tool in request.tools
            ]
        
        # Call RLM
        print(f"\n📥 Request: {len(messages)} messages, {len(tools) if tools else 0} tools")
        response = client.chat_completion(messages=messages, tools=tools)
        
        # Convert RLM response to OpenAI format
        choice = response['choices'][0]
        finish_reason = choice['finish_reason']
        
        print(f"📤 Response: finish_reason={finish_reason}")
        
        # Create response - convert tool_calls to dicts if present
        message_dict = {
            "role": "assistant",
            "content": choice['message'].get('content')
        }
        
        # Add tool_calls if present - need to convert to dict format
        if choice['message'].get('tool_calls'):
            tool_calls = choice['message']['tool_calls']
            # Convert tool_calls objects to dicts
            if tool_calls and not isinstance(tool_calls[0], dict):
                tool_calls = [
                    {
                        "id": tc.id if hasattr(tc, 'id') else f"call_{uuid.uuid4().hex[:8]}",
                        "type": "function",
                        "function": {
                            "name": tc.function.name if hasattr(tc.function, 'name') else tc['function']['name'],
                            "arguments": tc.function.arguments if hasattr(tc.function, 'arguments') else tc['function']['arguments']
                        }
                    }
                    for tc in tool_calls
                ]
            message_dict['tool_calls'] = tool_calls
        
        openai_response = ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=Message(**message_dict),
                    finish_reason=finish_reason
                )
            ],
            usage=Usage(
                prompt_tokens=0,  # TODO: Calculate actual tokens
                completion_tokens=0,
                total_tokens=0
            )
        )
        
        return openai_response
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "RLM OpenAI-Compatible API",
        "version": "1.0.0",
        "endpoints": {
            "chat_completions": "/v1/chat/completions",
            "models": "/v1/models",
            "health": "/health"
        },
        "features": [
            "OpenAI-compatible API",
            "Tool calling (function calling)",
            "Massive context handling (1M+ tokens)",
            "Stateful sessions"
        ],
        "usage": {
            "openai_python": {
                "base_url": "http://localhost:8000/v1",
                "api_key": "dummy"
            }
        }
    }


def main():
    """Run the server."""
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
