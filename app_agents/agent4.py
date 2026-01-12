"""
Agent4 - Human-in-the-Loop with LangGraph
Demonstrates: Local LangGraph workflow, human approval step, tool use
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional

from .tools import ToolRegistry

logging.basicConfig(level=logging.INFO)

try:
    from langgraph.graph import Graph, Node
except ImportError:
    Graph = None
    Node = None

class Agent4:
    """
    Human-in-the-Loop Agent using LangGraph
    - Builds a local workflow graph with LLM/tool nodes and a human approval node
    - Waits for human approval before finalizing answer
    """
    def __init__(self, ollama_host: str, model: str = "gemma:2b"):
        self.ollama_host = ollama_host
        self.model = model
        self.tools = ToolRegistry.get_tools()
        self.conversation_history: List[Dict[str, str]] = []
        self.last_candidate = None
        self.last_steps = []
        self.last_tools_used = []
        logging.info(f"[Agent4] Initialized with model={model}, tools={len(self.tools)})")

    def get_system_prompt(self) -> str:
        tools_description = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in self.tools
        ])
        return f"""You are a local agent with access to tools. You must get human approval before giving a final answer.\n\nAvailable Tools:\n{tools_description}\n\nWhen you have a candidate answer, present it for human approval.\n"""

    async def run(self, user_message: str, approve: Optional[bool] = None) -> Dict[str, Any]:
        import httpx
        self.conversation_history.append({"role": "user", "content": user_message})
        steps = []
        tools_used = []
        # Step 1: Generate candidate answer
        prompt = self.get_system_prompt() + f"\nUser: {user_message}\n\nGive your best answer, but do NOT say FINAL_ANSWER yet."
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2, "num_predict": 300}
                }
            )
        if response.status_code != 200:
            return {"answer": f"Error: LLM returned status {response.status_code}", "steps": steps, "tools_used": tools_used, "awaiting_approval": False}
        candidate = response.json().get("response", "").strip()
        steps.append({"type": "candidate", "content": candidate})
        self.last_candidate = candidate
        self.last_steps = steps
        self.last_tools_used = tools_used
        # Step 2: Wait for human approval
        if approve is None:
            return {"answer": candidate, "steps": steps, "tools_used": tools_used, "awaiting_approval": True}
        # Step 3: If approved, return as final answer
        if approve:
            steps.append({"type": "final", "content": candidate})
            return {"answer": candidate, "steps": steps, "tools_used": tools_used, "awaiting_approval": False}
        else:
            return {"answer": "Answer rejected by human. Please rephrase your question or try again.", "steps": steps, "tools_used": tools_used, "awaiting_approval": False}

    def reset_history(self):
        self.conversation_history = []
        self.last_candidate = None
        self.last_steps = []
        self.last_tools_used = []
        logging.info("[Agent4] Conversation history cleared")

    def get_tools_info(self) -> List[Dict]:
        return self.tools
