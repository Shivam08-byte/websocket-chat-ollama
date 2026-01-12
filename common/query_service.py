"""
Query service for routing between Manual and LangChain RAG systems
"""

import os
import httpx
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)

# Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))
RAG_ENABLED = os.getenv("RAG_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))
RAG_MAX_CHARS = int(os.getenv("RAG_MAX_CHARS", "2000"))


class QueryService:
    """Service for routing queries to appropriate RAG system"""
    
    def __init__(self, rag_store, langchain_rag, current_model: str):
        self.rag_store = rag_store
        self.langchain_rag = langchain_rag
        self.current_model = current_model
    
    async def query(
        self, 
        prompt: str, 
        sources: Optional[list] = None, 
        use_langchain: bool = False
    ) -> str:
        """
        Query Ollama API with appropriate RAG system
        
        Args:
            prompt: User's query
            sources: Optional list of source documents to filter RAG context
            use_langchain: If True, use LangChain system; otherwise use manual
            
        Returns:
            AI response string
        """
        
        # Route to LangChain system if requested
        if use_langchain:
            return await self._query_langchain(prompt, sources)
        
        # Route to manual system
        return await self._query_manual(prompt, sources)
    
    async def _query_langchain(self, prompt: str, sources: Optional[list]) -> str:
        """Query using LangChain RAG system"""
        try:
            if sources and RAG_ENABLED:
                return await self.langchain_rag.query_with_rag(
                    prompt, 
                    sources=sources, 
                    top_k=RAG_TOP_K
                )
            else:
                return await self.langchain_rag.query_without_rag(prompt)
        except Exception as e:
            logging.exception(f"[QueryService] LangChain query failed: {e}")
            return f"Error: {str(e)}"
    
    async def _query_manual(self, prompt: str, sources: Optional[list]) -> str:
        """Query using Manual RAG system"""
        try:
            # Base system prompt
            system_prompt = (
                "You are a helpful AI assistant. Provide clear, concise, and accurate responses. "
                "Prefer factual, sourced answers when context is provided."
            )

            # Optional RAG context
            context_block = ""
            if RAG_ENABLED and sources:
                try:
                    context_block = await self.rag_store.build_context(
                        prompt,
                        top_k=RAG_TOP_K,
                        max_chars=RAG_MAX_CHARS,
                        sources=sources,
                    )
                except Exception:
                    context_block = ""
            
            logging.info(
                "[QueryService] RAG context %s | system=manual | sources=%s | context_chars=%s",
                "ENABLED" if context_block else "DISABLED",
                sources,
                len(context_block) if context_block else 0,
            )

            # Build prompt
            if context_block:
                full_prompt = (
                    f"{system_prompt}\n\n"
                    f"You are given retrieved context from a knowledge base. "
                    f"Use it to answer the question.\n"
                    f"If the answer isn't in the context, say you don't know.\n\n"
                    f"Context:\n{context_block}\n\n"
                    f"User: {prompt}\nAssistant:"
                )
            else:
                full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:"
            
            # Query Ollama
            async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
                response = await client.post(
                    f"{OLLAMA_HOST}/api/generate",
                    json={
                        "model": self.current_model,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "top_k": 40,
                            "num_predict": 200,
                            "stop": ["\nUser:", "User:", "\n\n\n"]
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "No response from model")
                    response_text = response_text.strip()
                    return response_text if response_text else "I'm sorry, I couldn't generate a proper response."
                else:
                    return f"Error: Received status code {response.status_code}"
                    
        except httpx.ConnectError:
            return "Error: Cannot connect to Ollama. Make sure Ollama service is running."
        except Exception as e:
            logging.exception(f"[QueryService] Manual query failed: {e}")
            return f"Error: {str(e)}"
