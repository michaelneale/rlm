#!/usr/bin/env python3
"""
MCP Server for RLM (Recursive Language Model)

Provides tools to query large text/files using RLM's recursive processing.
"""

import os
import sys
from pathlib import Path
from typing import Any

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from rlm_query import query_text, query_file


# Initialize MCP server
server = Server("rlm-server")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available RLM tools."""
    return [
        Tool(
            name="query_text",
            description="Query a large text using RLM. Can handle arbitrarily large contexts that exceed normal LLM limits. The text can be a document, codebase, or any long content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text/document to query (can be very large)",
                    },
                    "query": {
                        "type": "string",
                        "description": "The question to ask about the text",
                    },
                    "max_iterations": {
                        "type": "integer",
                        "description": "Maximum RLM iterations (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["text", "query"],
            },
        ),
        Tool(
            name="query_file",
            description="Query a file using RLM. Loads the file content and queries it. Supports any text file (code, documents, logs, etc). Can handle files of any size.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to query",
                    },
                    "query": {
                        "type": "string",
                        "description": "The question to ask about the file",
                    },
                    "max_iterations": {
                        "type": "integer",
                        "description": "Maximum RLM iterations (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["file_path", "query"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution using shared query logic."""
    
    try:
        if name == "query_text":
            text = arguments.get("text")
            question = arguments.get("query")
            max_iterations = arguments.get("max_iterations", 10)
            
            if not text or not question:
                return [TextContent(
                    type="text",
                    text="Error: Both 'text' and 'query' are required"
                )]
            
            # Use shared query logic (no logging for MCP)
            result = query_text(text, question, max_iterations, enable_logging=False)
            return [TextContent(type="text", text=result)]
        
        elif name == "query_file":
            file_path = arguments.get("file_path")
            question = arguments.get("query")
            max_iterations = arguments.get("max_iterations", 10)
            
            if not file_path or not question:
                return [TextContent(
                    type="text",
                    text="Error: Both 'file_path' and 'query' are required"
                )]
            
            # Use shared query logic (no logging for MCP)
            result = query_file(file_path, question, max_iterations, enable_logging=False)
            return [TextContent(type="text", text=result)]
        
        else:
            return [TextContent(
                type="text",
                text=f"Error: Unknown tool: {name}"
            )]
    
    except FileNotFoundError as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except ValueError as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="rlm",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
