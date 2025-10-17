"""
Simple Recursive Language Model (RLM) with REPL environment.
"""

from typing import Dict, List, Optional, Any 

from rlm import RLM
from rlm.repl import REPLEnv
from rlm.utils.llm import OpenAIClient
from rlm.utils.prompts import DEFAULT_QUERY, next_action_prompt, build_system_prompt
import rlm.utils.utils as utils

from rlm.logger.root_logger import ColorfulLogger
from rlm.logger.repl_logger import REPLEnvLogger


class RLM_REPL(RLM):
    """
    LLM Client that can handle long contexts by recursively calling itself.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model: str = "gpt-5",
                 recursive_model: str = "gpt-5",
                 max_iterations: int = 20,
                 depth: int = 0,
                 enable_logging: bool = False,
                 ):
        self.api_key = api_key
        self.model = model
        self.recursive_model = recursive_model
        self.llm = OpenAIClient(api_key, model) # Replace with other client
        
        # Track recursive call depth to prevent infinite loops
        self.repl_env = None
        self.depth = depth # Unused in this version.
        self._max_iterations = max_iterations
        
        # Initialize colorful logger
        self.logger = ColorfulLogger(enabled=enable_logging)
        self.repl_env_logger = REPLEnvLogger(enabled=enable_logging)
        
        self.messages = [] # Initialize messages list
        self.query = None
    
    def setup_context(self, context: List[str] | str | List[Dict[str, str]], query: Optional[str] = None):
        """
        Setup the context for the RLMClient.

        Args:
            context: The large context to analyze in the form of a list of messages, string, or Dict
            query: The user's question
        """
        if query is None:
            query = DEFAULT_QUERY

        self.query = query
        self.logger.log_query_start(query)

        # Initialize the conversation with the REPL prompt
        self.messages = build_system_prompt()
        self.logger.log_initial_messages(self.messages)
        
        # Initialize REPL environment with context data
        context_data, context_str = utils.convert_context_for_repl(context)
        
        self.repl_env = REPLEnv(
            context_json=context_data, 
            context_str=context_str, 
            recursive_model=self.recursive_model,
        )
        
        return self.messages

    def completion(
        self, 
        context: List[str] | str | List[Dict[str, str]], 
        query: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        tool_results: Optional[List[Dict]] = None
    ) -> str | Dict:
        """
        Given a query and a (potentially long) context, recursively call the LM
        to explore the context and provide an answer using a REPL environment.
        
        Now supports external tool calling:
        - If tools provided, LLM can return tool calls to caller
        - If tool_results provided, continues execution after tool calls
        
        Args:
            context: The context to analyze
            query: The user's query
            tools: Optional list of external tool definitions
            tool_results: Optional tool results to continue execution
            
        Returns:
            If tool calls detected: Dict with 'type': 'tool_calls'
            Otherwise: String with final answer (backward compatible)
        """
        # Setup or restore state
        if tool_results is None:
            # New execution - setup context
            self.messages = self.setup_context(context, query)
        else:
            # Continuing from tool calls - append tool results to messages
            self.messages.extend(tool_results)
        
        # Main loop runs for fixed # of root LM iterations
        for iteration in range(self._max_iterations):
            
            # Query root LM to interact with REPL environment (with optional tools)
            response = self.llm.completion(
                self.messages + [next_action_prompt(query, iteration)],
                tools=tools
            )
            
            # PRIORITY 1: Check for external tool calls first
            if utils.has_tool_calls(response):
                # Log tool call response
                self.logger.log_model_response(
                    utils.extract_response_content(response), 
                    has_tool_calls=True
                )
                
                # Add assistant message with tool calls to history
                self.messages.append(utils.format_tool_call_message(response))
                
                # Return control to caller with tool calls
                return {
                    'type': 'tool_calls',
                    'tool_calls': response['tool_calls'],
                    'content': response.get('content'),
                    'state': 'paused',
                    'iteration': iteration
                }
            
            # PRIORITY 2: Check for internal REPL code blocks
            response_text = utils.extract_response_content(response)
            code_blocks = utils.find_code_blocks(response_text)
            self.logger.log_model_response(response_text, has_tool_calls=code_blocks is not None)
            
            # Process code execution or add assistant message
            if code_blocks is not None:
                self.messages = utils.process_code_execution(
                    response_text, self.messages, self.repl_env, 
                    self.repl_env_logger, self.logger
                )
            else:
                # Add assistant message when there are no code blocks
                assistant_message = {"role": "assistant", "content": "You responded with:\n" + response_text}
                self.messages.append(assistant_message)
            
            # PRIORITY 3: Check that model produced a final answer
            final_answer = utils.check_for_final_answer(
                response_text, self.repl_env, self.logger,
            )

            # In practice, you may need some guardrails here.
            if final_answer:
                self.logger.log_final_response(final_answer)
                return final_answer

            
        # If we reach here, no final answer was found in any iteration
        print("No final answer found in any iteration")
        self.messages.append(next_action_prompt(query, iteration, final_answer=True))
        final_response = self.llm.completion(self.messages, tools=None)  # No tools on final call
        final_answer = utils.extract_response_content(final_response)
        self.logger.log_final_response(final_answer)

        return final_answer
    
    def cost_summary(self) -> Dict[str, Any]:
        """Get the cost summary of the Root LM + Sub-RLM Calls."""
        raise NotImplementedError("Cost tracking not implemented for RLM REPL.")

    def reset(self):
        """Reset the (REPL) environment and message history."""
        self.repl_env = REPLEnv()
        self.messages = []
        self.query = None


if __name__ == "__main__":
    pass
