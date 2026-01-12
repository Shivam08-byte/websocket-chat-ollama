"""
Tool definitions for Agent1
Demonstrates various tool types that agents can use
"""

import os
import json
from datetime import datetime
from typing import Any, Dict


class ToolRegistry:
    """Registry of available tools for the agent"""
    
    @staticmethod
    def get_tools() -> list:
        """Return list of available tools with their schemas"""
        return [
            {
                "name": "calculator",
                "description": "Perform mathematical calculations. Input should be a mathematical expression as a string.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate (e.g., '2 + 2', '15 * 8', 'sqrt(16)')"
                        }
                    },
                    "required": ["expression"]
                }
            },
            {
                "name": "get_current_time",
                "description": "Get the current date and time. No parameters needed.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_weather",
                "description": "Get weather information for a city. This is a mock tool for demonstration.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "Name of the city to get weather for"
                        }
                    },
                    "required": ["city"]
                }
            },
            {
                "name": "search_knowledge",
                "description": "Search for information in a knowledge base. Returns relevant facts.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to find information"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
    
    @staticmethod
    def execute_tool(tool_name: str, parameters: Dict[str, Any]) -> str:
        """Execute a tool with given parameters"""
        
        if tool_name == "calculator":
            return ToolRegistry._calculator(parameters.get("expression", ""))
        
        elif tool_name == "get_current_time":
            return ToolRegistry._get_current_time()
        
        elif tool_name == "get_weather":
            return ToolRegistry._get_weather(parameters.get("city", ""))
        
        elif tool_name == "search_knowledge":
            return ToolRegistry._search_knowledge(parameters.get("query", ""))
        
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    
    @staticmethod
    def _calculator(expression: str) -> str:
        """Calculator tool - evaluates mathematical expressions"""
        try:
            # Safe evaluation of mathematical expressions
            import math
            # Create a safe namespace with math functions
            safe_dict = {
                'sqrt': math.sqrt,
                'pow': math.pow,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'log': math.log,
                'pi': math.pi,
                'e': math.e,
                'abs': abs,
                'round': round,
                'min': min,
                'max': max,
            }
            
            # Evaluate expression safely
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            
            return json.dumps({
                "result": result,
                "expression": expression,
                "message": f"The result of {expression} is {result}"
            })
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "expression": expression,
                "message": f"Failed to evaluate: {str(e)}"
            })
    
    @staticmethod
    def _get_current_time() -> str:
        """Get current date and time"""
        now = datetime.now()
        return json.dumps({
            "datetime": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "day": now.strftime("%A"),
            "message": f"Current time is {now.strftime('%H:%M:%S')} on {now.strftime('%A, %B %d, %Y')}"
        })
    
    @staticmethod
    def _get_weather(city: str) -> str:
        """Mock weather tool - demonstrates external API calls"""
        # In a real implementation, this would call a weather API
        mock_weather = {
            "mumbai": {"temp": 28, "condition": "Partly Cloudy", "humidity": 75},
            "delhi": {"temp": 22, "condition": "Clear Sky", "humidity": 45},
            "bangalore": {"temp": 25, "condition": "Pleasant", "humidity": 60},
            "london": {"temp": 12, "condition": "Rainy", "humidity": 85},
            "new york": {"temp": 15, "condition": "Sunny", "humidity": 50},
        }
        
        city_lower = city.lower()
        weather = mock_weather.get(city_lower, {
            "temp": 25,
            "condition": "Unknown",
            "humidity": 50
        })
        
        return json.dumps({
            "city": city,
            "temperature": weather["temp"],
            "condition": weather["condition"],
            "humidity": weather["humidity"],
            "message": f"Weather in {city}: {weather['temp']}°C, {weather['condition']}, Humidity: {weather['humidity']}%"
        })
    
    @staticmethod
    def _search_knowledge(query: str) -> str:
        """Mock knowledge base search"""
        # In a real implementation, this would search a vector database or API
        knowledge_base = {
            "python": "Python is a high-level, interpreted programming language known for its simplicity and readability. Created by Guido van Rossum in 1991.",
            "machine learning": "Machine Learning is a subset of AI that enables systems to learn and improve from experience without being explicitly programmed.",
            "agents": "AI Agents are autonomous systems that can perceive their environment, make decisions, and take actions to achieve specific goals. They use tools and reasoning.",
            "fastapi": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints.",
            "ollama": "Ollama is a tool for running large language models locally on your machine. It supports various models like Llama, Gemma, and Phi.",
        }
        
        query_lower = query.lower()
        for key, value in knowledge_base.items():
            if key in query_lower:
                return json.dumps({
                    "query": query,
                    "result": value,
                    "source": "knowledge_base",
                    "message": f"Found information about {key}"
                })
        
        return json.dumps({
            "query": query,
            "result": "No specific information found in knowledge base.",
            "message": "Information not available"
        })
