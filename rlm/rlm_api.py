"""
OpenAI-compatible API wrapper for RLM with external tool calling support.

This module provides a stateful API that handles massive contexts internally
while exposing a standard tool calling interface to external callers.
"""

from typing import List, Dict, Optional, Any
from rlm.rlm_repl import RLM_REPL


class RLMToolCallingAPI:
    """
    OpenAI-compatible API wrapper for RLM with external tool calling support.
    
    This wrapper:
    - Handles massive contexts internally via REPL/recursion
    - Exposes standard OpenAI-style tool calling to callers
    - Maintains session state across tool call boundaries
    - Provides seamless continuation when tool results are provided
    
    Example:
        >>> api = RLMToolCallingAPI(model="gpt-5-nano", recursive_model="gpt-5")
        >>> 
        >>> # First call with tools
        >>> response = api.chat_completion(
        ...     messages=[{"role": "user", "content": "Find X in massive doc"}],
        ...     tools=[{...tool_def...}]
        ... )
        >>> 
        >>> # If tool calls returned, execute and continue
        >>> if response['choices'][0]['finish_reason'] == 'tool_calls':
        ...     tool_results = execute_tools(...)
        ...     response = api.chat_completion(
        ...         messages=[...previous_messages..., tool_results],
        ...         tools=tools
        ...     )
    """
    
    def __init__(self, 
                 model: str = "gpt-5",
                 recursive_model: str = "gpt-5",
                 max_iterations: int = 20,
                 enable_logging: bool = False,
                 **kwargs):
        """
        Initialize RLM Tool Calling API.
        
        Args:
            model: Model for outer LLM (manages conversation)
            recursive_model: Model for recursive sub-calls (handles chunks)
            max_iterations: Maximum iterations in outer loop
            enable_logging: Whether to enable colorful logging
            **kwargs: Additional arguments passed to RLM_REPL
        """
        self.rlm = RLM_REPL(
            model=model,
            recursive_model=recursive_model,
            max_iterations=max_iterations,
            enable_logging=enable_logging,
            **kwargs
        )
        
        # Session state for tool calling continuations
        self.current_context = None
        self.current_query = None
        self.current_tools = None
        self.conversation_messages = []
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        OpenAI-compatible chat completion with tool calling support.
        
        This method handles both initial requests and continuations with tool results.
        It automatically detects if messages contain tool results and continues execution.
        
        Args:
            messages: List of conversation messages (OpenAI format)
            tools: Optional list of tool definitions (OpenAI format)
            
        Returns:
            Response dict matching OpenAI format:
            {
                'choices': [{
                    'message': {
                        'role': 'assistant',
                        'content': str,
                        'tool_calls': Optional[List]
                    },
                    'finish_reason': 'stop' | 'tool_calls'
                }],
                'model': str
            }
        """
        # Check if this is a continuation (has tool results)
        if self._has_tool_results(messages):
            # Extract tool results from messages
            tool_results = self._extract_tool_results(messages)
            
            # Continue RLM execution with tool results
            result = self.rlm.completion(
                context=self.current_context,
                query=self.current_query,
                tools=self.current_tools,
                tool_results=tool_results
            )
        else:
            # New conversation - extract context and query
            self.current_context = self._extract_context(messages)
            self.current_query = self._extract_query(messages)
            self.current_tools = tools
            self.conversation_messages = messages.copy()
            
            # Start RLM execution
            result = self.rlm.completion(
                context=self.current_context,
                query=self.current_query,
                tools=tools
            )
        
        # Format response based on result type
        if isinstance(result, dict) and result.get('type') == 'tool_calls':
            # Tool calls detected - return to caller for execution
            return {
                'choices': [{
                    'message': {
                        'role': 'assistant',
                        'content': result.get('content'),
                        'tool_calls': result['tool_calls']
                    },
                    'finish_reason': 'tool_calls',
                    'index': 0
                }],
                'model': self.rlm.model,
                'object': 'chat.completion'
            }
        else:
            # Final answer - return as regular completion
            return {
                'choices': [{
                    'message': {
                        'role': 'assistant',
                        'content': result
                    },
                    'finish_reason': 'stop',
                    'index': 0
                }],
                'model': self.rlm.model,
                'object': 'chat.completion'
            }
    
    def _extract_context(self, messages: List[Dict[str, str]]) -> Any:
        """
        Extract massive context from messages.
        
        Strategy:
        1. Look for system message with context
        2. Otherwise, use all messages except last user message
        
        Args:
            messages: Conversation messages
            
        Returns:
            Context to pass to RLM (string, list, or dict)
        """
        # Check for system message (likely contains context)
        system_messages = [m for m in messages if m.get('role') == 'system']
        if system_messages:
            # If multiple system messages, concatenate them
            if len(system_messages) == 1:
                return system_messages[0]['content']
            else:
                return [m['content'] for m in system_messages]
        
        # Otherwise, use all messages except the last user message as context
        if len(messages) > 1:
            context_messages = messages[:-1]
            return context_messages
        
        # No context, just the query
        return ""
    
    def _extract_query(self, messages: List[Dict[str, str]]) -> str:
        """
        Extract user query from messages.
        
        Args:
            messages: Conversation messages
            
        Returns:
            The user's query string
        """
        # Find the last user message
        for message in reversed(messages):
            if message.get('role') == 'user':
                return message['content']
        
        # Fallback: use last message
        if messages:
            return messages[-1].get('content', '')
        
        return ""
    
    def _has_tool_results(self, messages: List[Dict[str, str]]) -> bool:
        """
        Check if messages contain tool results (continuation).
        
        Args:
            messages: Conversation messages
            
        Returns:
            True if tool results are present
        """
        # Check for tool role messages OR assistant messages with tool_calls
        # followed by new user messages (OpenAI format for tool results)
        has_tool_role = any(m.get('role') == 'tool' for m in messages)
        
        # Also check if we have existing session state (indicates continuation)
        has_session = self.current_context is not None
        
        return has_tool_role or (has_session and len(messages) > len(self.conversation_messages))
    
    def _extract_tool_results(self, messages: List[Dict[str, str]]) -> List[Dict]:
        """
        Extract tool result messages from conversation.
        
        Args:
            messages: Conversation messages including tool results
            
        Returns:
            List of tool result messages formatted for RLM
        """
        # Find messages with role='tool' (OpenAI format)
        tool_messages = [m for m in messages if m.get('role') == 'tool']
        
        if tool_messages:
            return tool_messages
        
        # Alternative: look for new user messages after our last known message
        # (some implementations use user role for tool results)
        if self.conversation_messages:
            new_messages = messages[len(self.conversation_messages):]
            # Update conversation history
            self.conversation_messages = messages.copy()
            return new_messages
        
        return []
    
    def reset(self):
        """
        Reset session state and RLM environment.
        
        Call this to start a completely new conversation.
        """
        self.current_context = None
        self.current_query = None
        self.current_tools = None
        self.conversation_messages = []
        self.rlm.reset()
    
    def get_session_state(self) -> Dict[str, Any]:
        """
        Get current session state for debugging/monitoring.
        
        Returns:
            Dict with session information
        """
        return {
            'has_context': self.current_context is not None,
            'query': self.current_query,
            'num_tools': len(self.current_tools) if self.current_tools else 0,
            'conversation_length': len(self.conversation_messages),
            'rlm_iterations': getattr(self.rlm, '_max_iterations', 0)
        }


# Convenience function for simple use cases
def create_rlm_client(model: str = "gpt-5-nano", 
                     recursive_model: str = "gpt-5",
                     **kwargs) -> RLMToolCallingAPI:
    """
    Create an RLM client with sensible defaults.
    
    Args:
        model: Model for outer LLM (faster model recommended)
        recursive_model: Model for sub-calls (can be more capable)
        **kwargs: Additional RLM configuration
        
    Returns:
        RLMToolCallingAPI instance
    """
    return RLMToolCallingAPI(
        model=model,
        recursive_model=recursive_model,
        **kwargs
    )


if __name__ == "__main__":
    # Example usage
    api = create_rlm_client(
        model="gpt-5-nano",
        recursive_model="gpt-5",
        enable_logging=True
    )
    
    print("RLM Tool Calling API ready!")
    print("Usage:")
    print("  response = api.chat_completion(messages=[...], tools=[...])")
