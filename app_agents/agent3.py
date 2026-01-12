"""
Agent3 - Tree-of-Thought Agent
Demonstrates: Tree-of-Thoughts (ToT) reasoning, multi-path exploration, tool use
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional

from .tools import ToolRegistry

logging.basicConfig(level=logging.INFO)

class Agent3:
    """
    Tree-of-Thought Agent
    - Explores multiple reasoning paths (thoughts) in a tree structure
    - Selects the best path based on evaluation
    - Can use tools at each node
    - Maintains memory and conversation history
    """
    def __init__(self, ollama_host: str, model: str = "gemma:2b"):
        self.ollama_host = ollama_host
        self.model = model
        self.tools = ToolRegistry.get_tools()
        self.conversation_history: List[Dict[str, str]] = []
        self.max_branches = 3
        self.max_depth = 3
        logging.info(f"[Agent3] Initialized with model={model}, tools={len(self.tools)})")

    def get_system_prompt(self) -> str:
        tools_description = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in self.tools
        ])
        return f"""You are a Tree-of-Thoughts (ToT) agent. You solve problems by exploring multiple reasoning paths (thoughts) as a tree.\n\nAvailable Tools:\n{tools_description}\n\nFor each user query:\n1. Generate up to {self.max_branches} possible thoughts for the first step.\n2. For each thought, expand up to {self.max_branches} next thoughts (up to depth {self.max_depth}).\n3. At each node, you may use a tool.\n4. After exploring, select the best path and provide the final answer.\n\nUse this format:\nTHOUGHT: [Your reasoning]\nACTION: [tool_name] (if needed)\nACTION_INPUT: {{"parameter": "value"}} (if needed)\n\nAfter all, respond with:\nTHOUGHT: [Final reasoning]\nFINAL_ANSWER: [Your complete answer]\n"""

    async def run(self, user_message: str) -> Dict[str, Any]:
        import httpx
        self.conversation_history.append({"role": "user", "content": user_message})
        steps = []
        tools_used = []
        # 1. Generate initial thoughts (branches)
        prompt = self.get_system_prompt() + f"\nUser: {user_message}\n\nGenerate {self.max_branches} possible first thoughts as a numbered list."
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 300}
                }
            )
        if response.status_code != 200:
            return {"answer": f"Error: LLM returned status {response.status_code}", "steps": steps, "tools_used": tools_used}
        thoughts_text = response.json().get("response", "").strip()
        steps.append({"type": "thoughts", "content": thoughts_text})
        import re
        branches = re.findall(r"\d+\. (.+)", thoughts_text)
        tree = []
        # 2. Expand each branch up to max_depth
        for branch in branches[:self.max_branches]:
            path = [branch]
            for depth in range(1, self.max_depth):
                expand_prompt = self.get_system_prompt() + f"\nUser: {user_message}\nCurrent path: {' -> '.join(path)}\nExpand the next thought."
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        f"{self.ollama_host}/api/generate",
                        json={
                            "model": self.model,
                            "prompt": expand_prompt,
                            "stream": False,
                            "options": {"temperature": 0.3, "num_predict": 300}
                        }
                    )
                if response.status_code != 200:
                    break
                next_thought = response.json().get("response", "").strip()
                path.append(next_thought)
            tree.append(path)
        steps.append({"type": "tree", "content": tree})
        # 3. Evaluate and select best path
        eval_prompt = self.get_system_prompt() + f"\nUser: {user_message}\nHere are the reasoning paths: {tree}\nWhich path is best and why? Provide FINAL_ANSWER."
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": eval_prompt,
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
        logging.info("[Agent3] Conversation history cleared")

    def get_tools_info(self) -> List[Dict]:
        return self.tools
