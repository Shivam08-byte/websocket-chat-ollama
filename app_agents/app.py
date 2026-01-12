"""
FastAPI router for Agent endpoints
"""

import os
import logging
from fastapi import APIRouter
from typing import Dict

from .agent1 import Agent1
from .tools import ToolRegistry

# Create router for agent endpoints
router = APIRouter(prefix="/api/agents", tags=["agents"])

# Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:2b")

# Initialize Agent1
agent1 = Agent1(ollama_host=OLLAMA_HOST, model=OLLAMA_MODEL)

logging.basicConfig(level=logging.INFO)
logging.info(f"[Agents] Agent1 initialized with model={OLLAMA_MODEL}")


@router.get("/agent1/info")
async def agent1_info():
    """Get information about Agent1 and its capabilities"""
    return {
        "name": "Agent1",
        "description": "Simple ReAct agent with tool use",
        "model": OLLAMA_MODEL,
        "capabilities": [
            "Function calling",
            "Tool use",
            "Reasoning (ReAct pattern)",
            "Multi-step planning",
            "Conversation memory"
        ],
        "tools": agent1.get_tools_info(),
        "max_iterations": agent1.max_iterations
    }


@router.get("/agent1/tools")
async def agent1_tools():
    """Get list of available tools"""
    return {
        "tools": agent1.get_tools_info(),
        "count": len(agent1.get_tools_info())
    }


@router.post("/agent1/query")
async def agent1_query(payload: Dict):
    """
    Query Agent1 with a message
    
    Body:
    {
        "message": "What is 25 * 8 + 17?",
        "reset_history": false  // Optional: Clear conversation history
    }
    """
    try:
        message = payload.get("message", "").strip()
        reset_history = payload.get("reset_history", False)
        
        if not message:
            return {"success": False, "error": "No message provided"}
        
        if reset_history:
            agent1.reset_history()
        
        # Run agent
        result = await agent1.run(message)
        
        return {
            "success": True,
            "answer": result["answer"],
            "steps": result["steps"],
            "tools_used": result["tools_used"],
            "iterations": len(result["steps"])
        }
        
    except Exception as e:
        logging.exception(f"[Agents] Error in agent1_query: {e}")
        return {"success": False, "error": str(e)}


@router.post("/agent1/reset")
async def agent1_reset():
    """Reset Agent1 conversation history"""
    agent1.reset_history()
    return {
        "success": True,
        "message": "Agent1 conversation history reset"
    }


def get_agent1():
    """Get the initialized Agent1 instance"""
    return agent1
