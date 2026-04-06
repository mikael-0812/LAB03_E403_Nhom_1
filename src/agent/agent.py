import json
import re
from typing import List, Dict, Any, Optional

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger


class ReActAgent:
    """
    A ReAct-style Agent that follows the Thought-Action-Observation loop.

    Expected tool format:
    tools = [
        {
            "name": "tool_name",
            "description": "What the tool does",
            "function": callable
        }
    ]

    The callable should accept keyword arguments, for example:
        def get_course_info(course_code: str) -> dict: ...
    """

    ACTION_REGEX = re.compile(
        r"Action:\s*([a-zA-Z_][a-zA-Z0-9_]*)\((.*?)\)",
        re.DOTALL
    )
    FINAL_REGEX = re.compile(
        r"Final Answer:\s*(.*)",
        re.DOTALL
    )
    THOUGHT_REGEX = re.compile(
        r"Thought:\s*(.*?)(?:Action:|Final Answer:|$)",
        re.DOTALL
    )

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
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
        System prompt for ReAct behavior.
        Includes:
        1. Available tools and descriptions.
        2. Output format instructions.
        3. Safety / stopping boundaries.
        """
        tool_descriptions = "\n".join(
            [f"- {t['name']}: {t['description']}" for t in self.tools]
        )

        return f"""
You are an academic assistant agent that follows the ReAct pattern.

You have access to the following tools:
{tool_descriptions}

Your job:
- Reason step by step when necessary.
- Use tools only when needed.
- Use exactly one tool at a time.
- If enough information is already available, give the final answer directly.
- If the user's question is missing required information, ask for clarification in the final answer.
- Do not invent tool names.
- Do not invent tool results.
- Stop once you have enough information to answer.

Use one of the following exact formats:

Format 1:
Thought: your reasoning
Action: tool_name({{"arg1": "value1", "arg2": "value2"}})

Format 2:
Thought: your reasoning
Final Answer: your final response

Important rules:
- The Action line must contain exactly one valid tool call.
- The argument part inside Action must be a valid JSON object.
- Do not write Observation yourself. The system will provide Observation after the tool runs.
- After receiving an Observation, continue reasoning and either use another tool or provide Final Answer.
""".strip()

    def run(self, user_input: str) -> str:
        """
        ReAct loop:
        1. Generate Thought + Action or Final Answer.
        2. Parse Action and execute Tool.
        3. Append Observation to conversation and repeat until Final Answer.
        """
        logger.log_event("AGENT_START", {
            "input": user_input,
            "model": getattr(self.llm, "model_name", "unknown"),
            "max_steps": self.max_steps
        })

        self.history = [{"role": "user", "content": user_input}]
        steps = 0
        final_answer = None
        stop_reason = "max_steps_reached"

        while steps < self.max_steps:
            steps += 1

            prompt = self._build_prompt()

            try:
                result = self.llm.generate(
                    prompt,
                    system_prompt=self.get_system_prompt()
                )
            except Exception as e:
                logger.log_event("LLM_ERROR", {
                    "step": steps,
                    "error": str(e)
                })
                final_answer = (
                    "I encountered an internal error while generating a response. "
                    "Please try again or contact academic support."
                )
                stop_reason = "llm_error"
                break

            logger.log_event("LLM_RESPONSE", {
                "step": steps,
                "response": result
            })

            thought = self._extract_thought(result)
            if thought:
                logger.log_event("THOUGHT", {
                    "step": steps,
                    "thought": thought
                })

            final_answer = self._parse_final_answer(result)
            if final_answer is not None:
                logger.log_event("FINAL_ANSWER_FOUND", {
                    "step": steps,
                    "final_answer": final_answer
                })
                stop_reason = "final_answer"
                break

            action = self._parse_action(result)
            if action is None:
                logger.log_event("PARSE_ERROR", {
                    "step": steps,
                    "response": result,
                    "error": "Could not parse Action or Final Answer."
                })
                final_answer = (
                    "I could not complete the reasoning process because the action format was invalid. "
                    "Please try rephrasing your question."
                )
                stop_reason = "parse_error"
                break

            tool_name, args_json_str = action

            logger.log_event("ACTION_PARSED", {
                "step": steps,
                "tool_name": tool_name,
                "raw_args": args_json_str
            })

            observation = self._execute_tool(tool_name, args_json_str)

            logger.log_event("OBSERVATION", {
                "step": steps,
                "tool_name": tool_name,
                "observation": observation
            })

            self.history.append({"role": "assistant", "content": result})
            self.history.append({"role": "user", "content": f"Observation: {observation}"})

        if final_answer is None:
            final_answer = (
                "I could not complete the task within the maximum number of steps. "
                "Please contact the academic office for help."
            )

        logger.log_event("AGENT_END", {
            "steps": steps,
            "stop_reason": stop_reason,
            "final_answer": final_answer
        })

        return final_answer

    def _build_prompt(self) -> str:
        """
        Convert conversation history into a single prompt string.
        This keeps the agent logic compatible with simple provider interfaces.
        """
        lines = []
        for msg in self.history:
            role = msg["role"].capitalize()
            content = msg["content"]
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _extract_thought(self, text: str) -> Optional[str]:
        match = self.THOUGHT_REGEX.search(text)
        if match:
            return match.group(1).strip()
        return None

    def _parse_final_answer(self, text: str) -> Optional[str]:
        match = self.FINAL_REGEX.search(text)
        if match:
            return match.group(1).strip()
        return None

    def _parse_action(self, text: str) -> Optional[tuple[str, str]]:
        """
        Expected format:
            Action: tool_name({"arg": "value"})
        Returns:
            (tool_name, args_json_str) or None
        """
        match = self.ACTION_REGEX.search(text)
        if not match:
            return None

        tool_name = match.group(1).strip()
        args_str = match.group(2).strip()

        return tool_name, args_str

    def _execute_tool(self, tool_name: str, args: str) -> str:
        """
        Execute tool by name.

        Expected action format example:
            Action: get_course_info({"course_code": "CS201"})
        """
        if tool_name not in self.tool_map:
            return json.dumps({
                "error": f"Tool '{tool_name}' not found."
            }, ensure_ascii=False)

        tool_fn = self.tool_map[tool_name]
        if tool_fn is None:
            return json.dumps({
                "error": f"Tool '{tool_name}' has no bound function."
            }, ensure_ascii=False)

        try:
            parsed_args = json.loads(args)
        except json.JSONDecodeError as e:
            return json.dumps({
                "error": "Invalid JSON arguments.",
                "details": str(e)
            }, ensure_ascii=False)

        if not isinstance(parsed_args, dict):
            return json.dumps({
                "error": "Tool arguments must be a JSON object."
            }, ensure_ascii=False)

        try:
            result = tool_fn(**parsed_args)
        except TypeError as e:
            return json.dumps({
                "error": f"Invalid arguments for tool '{tool_name}'.",
                "details": str(e)
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                "error": f"Tool '{tool_name}' execution failed.",
                "details": str(e)
            }, ensure_ascii=False)

        if isinstance(result, (dict, list)):
            return json.dumps(result, ensure_ascii=False)
        return str(result)