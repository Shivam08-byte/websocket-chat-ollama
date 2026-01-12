"""
WebSocket connection manager and handler
"""

import json
import logging
from typing import List
from fastapi import WebSocket, WebSocketDisconnect

logging.basicConfig(level=logging.INFO)


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        """Send message to a specific WebSocket"""
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            await connection.send_text(message)


class WebSocketHandler:
    """Handles WebSocket chat messages and routes to query service"""
    
    def __init__(self, connection_manager: ConnectionManager, query_service):
        self.manager = connection_manager
        self.query_service = query_service
    
    async def handle_connection(self, websocket: WebSocket):
        """
        Handle a WebSocket connection lifecycle
        
        Args:
            websocket: FastAPI WebSocket instance
        """
        await self.manager.connect(websocket)
        
        try:
            # Send welcome message
            await self.manager.send_message(
                json.dumps({
                    "type": "system",
                    "message": "Connected to chat server. Type your message to chat with the AI."
                }),
                websocket
            )
            
            # Message loop
            while True:
                data = await websocket.receive_text()
                await self._process_message(data, websocket)
                
        except WebSocketDisconnect:
            self.manager.disconnect(websocket)
            logging.info("[WebSocket] Client disconnected")
        except Exception as e:
            logging.exception(f"[WebSocket] Error: {e}")
            self.manager.disconnect(websocket)
    
    async def _process_message(self, data: str, websocket: WebSocket):
        """Process incoming WebSocket message"""
        try:
            message_data = json.loads(data)
            user_message = message_data.get("message", "")
            sources = message_data.get("sources")
            use_langchain = message_data.get("useLangchain", False)
            
            # Validate and clean sources
            if isinstance(sources, list):
                sources = [str(s) for s in sources if isinstance(s, (str, bytes))]
            else:
                sources = None
            
            system_type = "LangChain" if use_langchain else "Manual"
            logging.info(
                "[WebSocket] Message received | system=%s | sources=%s | text_preview=%s", 
                system_type, sources, user_message[:80]
            )
            
            if not user_message.strip():
                return
            
            # Echo user message
            await self.manager.send_message(
                json.dumps({
                    "type": "user",
                    "message": user_message
                }),
                websocket
            )
            
            # Send typing indicator
            await self.manager.send_message(
                json.dumps({
                    "type": "typing",
                    "message": f"AI is typing... ({system_type} system)"
                }),
                websocket
            )
            
            # Get AI response
            ai_response = await self.query_service.query(
                user_message, 
                sources=sources, 
                use_langchain=use_langchain
            )
            
            # Send AI response
            await self.manager.send_message(
                json.dumps({
                    "type": "ai",
                    "message": ai_response
                }),
                websocket
            )
            
        except json.JSONDecodeError:
            await self.manager.send_message(
                json.dumps({
                    "type": "error",
                    "message": "Invalid message format"
                }),
                websocket
            )
        except Exception as e:
            logging.exception(f"[WebSocket] Message processing error: {e}")
            await self.manager.send_message(
                json.dumps({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                }),
                websocket
            )
