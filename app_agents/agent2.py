"""
Agent2 - Plan-and-Execute Agent
Demonstrates: Planning, Execution, Tool use, Multi-step reasoning
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional

from .tools import ToolRegistry

logging.basicConfig(level=logging.INFO)

class Agent2:
    """
    Plan-and-Execute Agent
    - First creates a plan (list of steps)
    - Executes each step, using tools if needed
    - Maintains memory and conversation history
    """
    def __init__(self, ollama_host: str, model: str = "gemma:2b"):
        self.ollama_host = ollama_host
        self.model = model
        self.tools = ToolRegistry.get_tools()
        self.conversation_history: List[Dict[str, str]] = []
        logging.info(f"[Agent2] Initialized with model={model}, tools={len(self.tools)}")

    def get_system_prompt(self) -> str:
        tools_description = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in self.tools
        ])
        return f"""You are a helpful AI agent with access to tools. You use a Plan-and-Execute approach.\n\nAvailable Tools:\n{tools_description}\n\nWhen you receive a user query, first create a PLAN as a numbered list of steps.\nThen, for each step, decide if you need to use a tool.\nIf you use a tool, respond in this format:\nTHOUGHT: [Explain your reasoning]\nACTION: [tool_name]\nACTION_INPUT: {{"parameter": "value"}}\n\nAfter executing all steps, respond with:\nTHOUGHT: [Final reasoning]\nFINAL_ANSWER: [Your complete answer]\n"""

    async def run(self, user_message: str) -> Dict[str, Any]:
        import httpx
        self.conversation_history.append({"role": "user", "content": user_message})
        steps = []
        tools_used = []
        # 1. Get a plan from the LLM
        plan_prompt = self.get_system_prompt() + f"\nUser: {user_message}\n\nPLAN:"
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": plan_prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 300}
                }
            )
        if response.status_code != 200:
            return {"answer": f"Error: LLM returned status {response.status_code}", "steps": steps, "tools_used": tools_used}
        plan_text = response.json().get("response", "").strip()
        steps.append({"type": "plan", "content": plan_text})
        # 2. For each step, execute if tool is needed
        import re
        plan_steps = re.findall(r"\d+\. (.+)", plan_text)
        for step in plan_steps:
            # Ask LLM if a tool is needed for this step
            tool_prompt = self.get_system_prompt() + f"\nUser: {user_message}\nPLAN: {plan_text}\nCURRENT_STEP: {step}\n\nShould I use a tool? If yes, reply in ACTION/ACTION_INPUT format. If not, reply with THOUGHT and FINAL_ANSWER."
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": tool_prompt,
                        "stream": False,
                        "options": {"temperature": 0.1, "num_predict": 300}
                    }
                )
            if response.status_code != 200:
                continue
            agent_response = response.json().get("response", "").strip()
            if "ACTION:" in agent_response and "ACTION_INPUT:" in agent_response:
                action_part = agent_response.split("ACTION:")[1].split("ACTION_INPUT:")
                tool_name = action_part[0].strip()
                tool_input_str = action_part[1].strip()
                try:
                    tool_input = json.loads(tool_input_str)
                except:
                    import re
                    json_match = re.search(r'\{.*\}', tool_input_str, re.DOTALL)
                    if json_match:
                        tool_input = json.loads(json_match.group())
                    else:
                        tool_input = {}
                tool_result = ToolRegistry.execute_tool(tool_name, tool_input)
                steps.append({"type": "tool_call", "step": step, "tool": tool_name, "input": tool_input, "result": tool_result})
                tools_used.append(tool_name)
            else:
                steps.append({"type": "thought", "step": step, "content": agent_response})
        # 3. Get final answer
        final_prompt = self.get_system_prompt() + f"\nUser: {user_message}\nPLAN: {plan_text}\nSTEPS_EXECUTED: {steps}\n\nWhat is the final answer?"
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": final_prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 300}
                }
            )
        if response.status_code != 200:
            return {"answer": f"Error: LLM returned status {response.status_code}", "steps": steps, "tools_used": tools_used}
        final_answer = response.json().get("response", "").strip()
        steps.append({"type": "final", "content": final_answer})
        return {"answer": final_answer, "steps": steps, "tools_used": tools_used}

    def reset_history(self):
        self.conversation_history = []
        logging.info("[Agent2] Conversation history cleared")

    def get_tools_info(self) -> List[Dict]:
        return self.tools
