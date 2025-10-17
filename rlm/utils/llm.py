"""
OpenAI Client wrapper specifically for GPT-5 models.
"""

import os
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class OpenAIClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-5"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.model = model
        self.client = OpenAI(api_key=self.api_key)

        # Implement cost tracking logic here.
    
    def completion(
        self,
        messages: list[dict[str, str]] | str,
        tools: Optional[list] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> dict | str:
        """
        Generate completion from OpenAI API.
        
        Args:
            messages: Input messages
            tools: Optional list of tool definitions
            max_tokens: Maximum tokens to generate
            **kwargs: Additional API parameters
            
        Returns:
            If tools provided: dict with 'content', 'tool_calls', 'role'
            If no tools: string (backward compatible)
        """
        try:
            if isinstance(messages, str):
                messages = [{"role": "user", "content": messages}]
            elif isinstance(messages, dict):
                messages = [messages]

            # Build API call parameters
            api_params = {
                "model": self.model,
                "messages": messages,
                "max_completion_tokens": max_tokens,
                **kwargs
            }
            
            # Only add tools if provided
            if tools is not None:
                api_params["tools"] = tools

            response = self.client.chat.completions.create(**api_params)
            message = response.choices[0].message
            
            # If tools were provided, return full response dict
            if tools is not None:
                return {
                    'content': message.content,
                    'tool_calls': message.tool_calls if hasattr(message, 'tool_calls') else None,
                    'role': 'assistant'
                }
            
            # Backward compatible: return just content if no tools
            return message.content

        except Exception as e:
            raise RuntimeError(f"Error generating completion: {str(e)}")