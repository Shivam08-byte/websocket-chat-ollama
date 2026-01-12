"""
Agent1 - Simple ReAct Agent for Learning
Demonstrates: Function calling, Tool use, Reasoning, Planning
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional

from .tools import ToolRegistry

logging.basicConfig(level=logging.INFO)


class Agent1:
    """
    Simple ReAct (Reasoning + Acting) Agent
    
    Key Concepts Demonstrated:
    1. Tool Selection - Agent decides which tool to use
    2. Function Calling - Agent can call external functions
    3. Reasoning - Agent explains its thinking
    4. Memory - Agent maintains conversation history
    5. Planning - Agent breaks down complex tasks
    """
    
    def __init__(self, ollama_host: str, model: str = "gemma:2b"):
        self.ollama_host = ollama_host
        self.model = model
        self.tools = ToolRegistry.get_tools()
        self.conversation_history: List[Dict[str, str]] = []
        self.max_iterations = 5  # Prevent infinite loops
        
        logging.info(f"[Agent1] Initialized with model={model}, tools={len(self.tools)}")
    
    def get_system_prompt(self) -> str:
        """System prompt that teaches the agent how to use tools"""
        tools_description = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in self.tools
        ])
        
        return f"""You are a helpful AI agent with access to tools. You can use tools to help answer questions.

Available Tools:
{tools_description}

When you need to use a tool, respond in this EXACT format:
THOUGHT: [Explain your reasoning about what you need to do]
ACTION: [tool_name]
ACTION_INPUT: {{"parameter": "value"}}

When you have the final answer, respond in this format:
THOUGHT: [Explain your final reasoning]
FINAL_ANSWER: [Your complete answer to the user]

Important Rules:
1. ALWAYS start with THOUGHT to explain your reasoning
2. Use ACTION when you need a tool
3. Use FINAL_ANSWER when you're done
4. Be clear and concise
5. If a tool gives an error, try a different approach

Example:
User: What is 25 + 17?
THOUGHT: I need to calculate 25 + 17, I'll use the calculator tool.
ACTION: calculator
ACTION_INPUT: {{"expression": "25 + 17"}}

[After getting tool result]
THOUGHT: The calculator returned 42. This is the answer.
FINAL_ANSWER: 25 + 17 equals 42.
"""
    
    async def run(self, user_message: str, use_tools: bool = True) -> Dict[str, Any]:
        """
        Run the agent with a user message
        
        Returns:
            Dictionary with:
            - answer: Final answer string
            - steps: List of reasoning steps
            - tools_used: List of tools that were called
        """
        import httpx
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        steps = []
        tools_used = []
        iteration = 0
        
        # Agent loop (ReAct pattern)
        while iteration < self.max_iterations:
            iteration += 1
            
            # Build prompt with history
            prompt = self._build_prompt()
            
            logging.info(f"[Agent1] Iteration {iteration}/{self.max_iterations}")
            
            # Get LLM response
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # Low temperature for consistent reasoning
                            "num_predict": 300,
                        }
                    }
                )
                
                if response.status_code != 200:
                    return {
                        "answer": f"Error: LLM returned status {response.status_code}",
                        "steps": steps,
                        "tools_used": tools_used
                    }
                
                result = response.json()
                agent_response = result.get("response", "").strip()
            
            logging.info(f"[Agent1] Response: {agent_response[:200]}...")
            
            # Parse agent response
            if "FINAL_ANSWER:" in agent_response:
                # Agent is done
                final_answer = agent_response.split("FINAL_ANSWER:")[1].strip()
                steps.append({
                    "type": "final",
                    "content": agent_response
                })
                
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_answer
                })
                
                return {
                    "answer": final_answer,
                    "steps": steps,
                    "tools_used": tools_used
                }
            
            elif "ACTION:" in agent_response and "ACTION_INPUT:" in agent_response:
                # Agent wants to use a tool
                thought = ""
                if "THOUGHT:" in agent_response:
                    thought = agent_response.split("ACTION:")[0].replace("THOUGHT:", "").strip()
                
                action_part = agent_response.split("ACTION:")[1].split("ACTION_INPUT:")
                tool_name = action_part[0].strip()
                tool_input_str = action_part[1].strip()
                
                # Parse tool input
                try:
                    tool_input = json.loads(tool_input_str)
                except:
                    # Try to extract JSON from the string
                    import re
                    json_match = re.search(r'\{.*\}', tool_input_str, re.DOTALL)
                    if json_match:
                        tool_input = json.loads(json_match.group())
                    else:
                        tool_input = {}
                
                logging.info(f"[Agent1] Using tool: {tool_name} with input: {tool_input}")
                
                # Execute tool
                tool_result = ToolRegistry.execute_tool(tool_name, tool_input)
                
                steps.append({
                    "type": "tool_call",
                    "thought": thought,
                    "tool": tool_name,
                    "input": tool_input,
                    "result": tool_result
                })
                
                tools_used.append(tool_name)
                
                # Add tool result to context
                self.conversation_history.append({
                    "role": "assistant",
                    "content": f"ACTION: {tool_name}\nACTION_INPUT: {json.dumps(tool_input)}"
                })
                self.conversation_history.append({
                    "role": "tool",
                    "content": f"TOOL_RESULT: {tool_result}"
                })
                
                # Continue to next iteration
                continue
            
            else:
                # Agent didn't follow the format, treat as final answer
                steps.append({
                    "type": "final",
                    "content": agent_response
                })
                
                return {
                    "answer": agent_response,
                    "steps": steps,
                    "tools_used": tools_used
                }
        
        # Max iterations reached
        return {
            "answer": "I apologize, but I wasn't able to complete the task within the allowed steps. Please try rephrasing your question.",
            "steps": steps,
            "tools_used": tools_used
        }
    
    def _build_prompt(self) -> str:
        """Build prompt with system message and conversation history"""
        prompt = self.get_system_prompt() + "\n\n"
        
        for msg in self.conversation_history:
            if msg["role"] == "user":
                prompt += f"User: {msg['content']}\n\n"
            elif msg["role"] == "assistant":
                prompt += f"Assistant: {msg['content']}\n\n"
            elif msg["role"] == "tool":
                prompt += f"{msg['content']}\n\n"
        
        prompt += "Assistant: "
        return prompt
    
    def reset_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logging.info("[Agent1] Conversation history cleared")
    
    def get_tools_info(self) -> List[Dict]:
        """Get information about available tools"""
        return self.tools
