import json
import re
from typing import List, Dict, Any, Optional

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.tools.dynamic_registry import execute_dynamic_tool


class ReActAgent:
    """
    A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Implements the core loop logic and tool execution.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 7):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history: List[Dict[str, str]] = []

        self.tool_map = {}
        for tool in tools:
            name = tool.get("name")
            fn = tool.get("function")
            if name:
                self.tool_map[name] = fn

    def get_system_prompt(self) -> str:
        """
        System prompt that instructs the agent to follow ReAct.
        """
        import json
        tool_descriptions = ""
        for t in self.tools:
            tool_descriptions += f"- {t['name']}: {t['description']}\n"

        return f"""
You are an intelligent assistant. You must solve the user's request by calling out to tools.
You have access to the following tools:
{tool_descriptions}

CRITICAL: If any tool (like check_payment) returns an error (e.g. Error 500) or if you cannot satisfy the user, you MUST immediately call the 'escalate_to_human' tool to escalate the problem!

Always use the following exact format for your responses:
Thought: your line of reasoning. Look at the Observation and decide what to do next. If you need to use a tool, output 'Action: tool_name(arguments)' then stop generating and wait for the Observation.
Action: tool_name(arguments_in_JSON)
Observation: the result of the tool call

When you have the final answer, output:
Final Answer: your final response to the user.

If the user asks a question that is absolutely impossible to answer using the provided tools and cannot be resolved, you MUST end your Final Answer with exactly the tag: [OUT_OF_SCOPE].

Example:
Thought: I need to check the location.
Action: get_location({{}})
Observation: Quận 1, TP.HCM
Thought: I know the location now.
Final Answer: You are currently located at Quận 1, TP.HCM.
"""

    def run(self, user_input: str) -> str:
        """
        Implements the ReAct loop logic.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        
        current_prompt = f"User Request: {user_input}\n"
        steps = 0
        final_answer = None

        while steps < self.max_steps:
            logger.log_event("STEP_START", {"step": steps + 1})
            
            # Generate LLM response
            response = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
            result_text = response.get("content", "")
            
            # Extract Thought, Action, Final Answer
            thought_match = re.search(r"Thought:\s*(.*?)(?=(?:Action:|Final Answer:|$))", result_text, re.DOTALL)
            action_match = re.search(r"Action:\s*(\w+)\((.*?)\)", result_text, re.DOTALL)
            final_match = re.search(r"Final Answer:\s*(.*)", result_text, re.DOTALL)
            
            thought = thought_match.group(1).strip() if thought_match else "No thought found."
            logger.log_step("Agent", "Thought", thought)

            if final_match:
                final_answer = final_match.group(1).strip()
                logger.log_step("Agent", "Final Answer", final_answer)
                break
            
            if action_match:
                tool_name = action_match.group(1).strip()
                tool_args = action_match.group(2).strip()
                
                logger.log_step("Agent", "Action", f"{tool_name}({tool_args})")
                
                # Execute tool
                observation = self._execute_tool(tool_name, tool_args)
                logger.log_step("Tool", "Observation", observation)
                
                # Append to prompt
                current_prompt += f"\nThought: {thought}\nAction: {tool_name}({tool_args})\nObservation: {observation}\n"
            else:
                # Fallback if the agent doesn't output correct format but also doesn't output final answer.
                current_prompt += f"\nThought: {thought}\nObservation: Please use 'Action: tool_name(args)' or 'Final Answer: ...'\n"
            
            steps += 1
            
        if not final_answer:
            final_answer = "Max steps reached without a Final Answer."
            
        logger.log_event("AGENT_END", {"steps": steps, "final_answer": final_answer})
        return final_answer

    def _execute_tool(self, tool_name: str, args: str) -> str:
        """
        Helper method to execute tools.
        """
        # Add basic validation for tools
        valid_tools = [t['name'] for t in self.tools]
        if tool_name not in valid_tools:
            return f"Error: Tool {tool_name} is not available."
            
        return execute_dynamic_tool(tool_name, args)
