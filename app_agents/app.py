"""
FastAPI router for Agent endpoints
"""

import os
import logging
from fastapi import APIRouter
from typing import Dict

from .agent1 import Agent1
from .agent2 import Agent2
from .agent3 import Agent3
from .agent4 import Agent4
from .guardrails import check_guardrails
from .tools import ToolRegistry

# Create router for agent endpoints
router = APIRouter(prefix="/api/agents", tags=["agents"])

# Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:2b")


# Initialize Agent1, Agent2, Agent3, and Agent4
agent1 = Agent1(ollama_host=OLLAMA_HOST, model=OLLAMA_MODEL)
agent2 = Agent2(ollama_host=OLLAMA_HOST, model=OLLAMA_MODEL)
agent3 = Agent3(ollama_host=OLLAMA_HOST, model=OLLAMA_MODEL)
agent4 = Agent4(ollama_host=OLLAMA_HOST, model=OLLAMA_MODEL)
# ------------------- AGENT4 ENDPOINTS -------------------
@router.get("/agent4/info")
async def agent4_info():
    """Get information about Agent4 and its capabilities"""
    try:
        message = payload.get("message", "").strip()
        reset_history = payload.get("reset_history", False)
        if not message:
            return {"success": False, "error": "No message provided"}
        is_blocked, block_msg = check_guardrails(message)
        if is_blocked:
            return {"success": False, "error": block_msg}
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
    }

@router.post("/agent4/query")
async def agent4_query(payload: Dict):
    """
    Query Agent4 with a message. If awaiting approval, set approve=true/false in the body.
    Body:
    {
        "message": "What is the capital of France?",
        "approve": true, // Optional: Approve or reject the candidate answer
        "reset_history": false  // Optional: Clear conversation history
    }
    """
    try:
        message = payload.get("message", "").strip()
        approve = payload.get("approve", None)
        reset_history = payload.get("reset_history", False)
        if not message:
            return {"success": False, "error": "No message provided"}
        if reset_history:
            agent4.reset_history()
        result = await agent4.run(message, approve=approve)
        return {
            "success": True,
            "answer": result["answer"],
            "steps": result["steps"],
            "tools_used": result["tools_used"],
            "awaiting_approval": result["awaiting_approval"],
            "iterations": len(result["steps"])
        }
    except Exception as e:
        logging.exception(f"[Agents] Error in agent4_query: {e}")
        return {"success": False, "error": str(e)}

@router.post("/agent4/reset")
async def agent4_reset():
    """Reset Agent4 conversation history"""
    agent4.reset_history()
    return {
        "success": True,
        "message": "Agent4 conversation history reset"
    }
# ------------------- AGENT3 ENDPOINTS -------------------
@router.get("/agent3/info")
async def agent3_info():
    """Get information about Agent3 and its capabilities"""
    return {
        "name": "Agent3",
        "description": "Tree-of-Thought agent with multi-path reasoning and tool use",
        "model": OLLAMA_MODEL,
        "capabilities": [
            "Tree-of-Thoughts reasoning",
            "Tool use",
            "Multi-path exploration",
            "Conversation memory"
        ],
        "tools": agent3.get_tools_info(),
    }

@router.get("/agent3/tools")
async def agent3_tools():
    """Get list of available tools for Agent3"""
    return {
        "tools": agent3.get_tools_info(),
        "count": len(agent3.get_tools_info())
    }

@router.post("/agent3/query")
async def agent3_query(payload: Dict):
    """
    Query Agent3 with a message
    Body:
    {
        "message": "How do I solve this problem?",
        "reset_history": false  // Optional: Clear conversation history
    }
    """
    try:
        message = payload.get("message", "").strip()
        reset_history = payload.get("reset_history", False)
        if not message:
            return {"success": False, "error": "No message provided"}
        if reset_history:
            agent3.reset_history()
        result = await agent3.run(message)
        return {
            "success": True,
            "answer": result["answer"],
            "steps": result["steps"],
            "tools_used": result["tools_used"],
            "iterations": len(result["steps"])
        }
    except Exception as e:
        logging.exception(f"[Agents] Error in agent3_query: {e}")
        return {"success": False, "error": str(e)}

@router.post("/agent3/reset")
async def agent3_reset():
    """Reset Agent3 conversation history"""
    agent3.reset_history()
    return {
        "success": True,
        "message": "Agent3 conversation history reset"
    }

# ------------------- AGENT2 ENDPOINTS -------------------
@router.get("/agent2/info")
async def agent2_info():
    """Get information about Agent2 and its capabilities"""
    return {
        "name": "Agent2",
        "description": "Plan-and-Execute agent with multi-step planning and tool use",
        "model": OLLAMA_MODEL,
        "capabilities": [
            "Planning (Plan-and-Execute)",
            "Tool use",
            "Multi-step reasoning",
            "Conversation memory"
        ],
        "tools": agent2.get_tools_info(),
    }

@router.get("/agent2/tools")
async def agent2_tools():
    """Get list of available tools for Agent2"""
    return {
        "tools": agent2.get_tools_info(),
        "count": len(agent2.get_tools_info())
    }

@router.post("/agent2/query")
async def agent2_query(payload: Dict):
    """
    Query Agent2 with a message
    Body:
    {
        "message": "How do I plan a trip to Mumbai?",
        "reset_history": false  // Optional: Clear conversation history
    }
    """
    try:
        message = payload.get("message", "").strip()
        reset_history = payload.get("reset_history", False)
        if not message:
            return {"success": False, "error": "No message provided"}
        is_blocked, block_msg = check_guardrails(message)
        if is_blocked:
            return {"success": False, "error": block_msg}
        if reset_history:
            agent2.reset_history()
        result = await agent2.run(message)
        return {
            "success": True,
            "answer": result["answer"],
            "steps": result["steps"],
            "tools_used": result["tools_used"],
            "iterations": len(result["steps"])
        }
    except Exception as e:
        logging.exception(f"[Agents] Error in agent2_query: {e}")
        return {"success": False, "error": str(e)}

@router.post("/agent2/reset")
async def agent2_reset():
    """Reset Agent2 conversation history"""
    agent2.reset_history()
    try:
        message = payload.get("message", "").strip()
        reset_history = payload.get("reset_history", False)
        if not message:
            return {"success": False, "error": "No message provided"}
        is_blocked, block_msg = check_guardrails(message)
        if is_blocked:
            return {"success": False, "error": block_msg}
        if reset_history:
            agent3.reset_history()
        result = await agent3.run(message)
        return {
            "success": True,
            "answer": result["answer"],
            "steps": result["steps"],
            "tools_used": result["tools_used"],
            "iterations": len(result["steps"])
        }
    except Exception as e:
        logging.exception(f"[Agents] Error in agent3_query: {e}")
        return {"success": False, "error": str(e)}
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
    try:
        message = payload.get("message", "").strip()
        approve = payload.get("approve", None)
        reset_history = payload.get("reset_history", False)
        if not message:
            return {"success": False, "error": "No message provided"}
        is_blocked, block_msg = check_guardrails(message)
        if is_blocked:
            return {"success": False, "error": block_msg}
        if reset_history:
            agent4.reset_history()
        result = await agent4.run(message, approve=approve)
        return {
            "success": True,
            "answer": result["answer"],
            "steps": result["steps"],
            "tools_used": result["tools_used"],
            "awaiting_approval": result["awaiting_approval"],
            "iterations": len(result["steps"])
        }
    except Exception as e:
        logging.exception(f"[Agents] Error in agent4_query: {e}")
        return {"success": False, "error": str(e)}
        
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
