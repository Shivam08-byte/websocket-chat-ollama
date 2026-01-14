"""
LangChain-based RAG implementation for comparison with manual implementation.
Uses the same Ollama models but with LangChain framework.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS, Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document


class LangChainRAGSystem:
    """LangChain-based RAG system using local Ollama models"""
    
    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        ollama_model: str = "gemma:2b",
        embed_model: str = "nomic-embed-text",
        chunk_size: int = 800,
        chunk_overlap: int = 200,
        vectorstore_path: str = "/app/data/langchain_vectorstore",
        vectorstore_type: str = "faiss",
    ):
        self.ollama_host = ollama_host
        self.ollama_model = ollama_model
        self.embed_model = embed_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.vectorstore_path = vectorstore_path
        self.vectorstore_type = (vectorstore_type or "faiss").lower()
        
        # Initialize LLM
        self.llm = Ollama(
            model=ollama_model,
            base_url=ollama_host,
            temperature=0.7
            # Note: top_p, top_k, num_predict are set in generation, not initialization
        )
        
        # Initialize embeddings
        self.embeddings = OllamaEmbeddings(
            model=embed_model,
            base_url=ollama_host
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Vector store (lazy loaded)
        self.vectorstore: Optional[Any] = None
        self.source_docs: Dict[str, List[Document]] = {}  # Track docs by source
        
        logging.info(f"[LangChain] Initialized with model={ollama_model}, embed={embed_model}")

        # If using Chroma, attempt to load existing persisted store
        if self.vectorstore_type == "chroma":
            try:
                p = Path(self.vectorstore_path)
                if p.exists():
                    self.vectorstore = Chroma(persist_directory=self.vectorstore_path, embedding_function=self.embeddings)
                    logging.info(f"[LangChain] Loaded existing Chroma vectorstore at {self.vectorstore_path}")
            except Exception:
                self.vectorstore = None
    
    def add_documents(self, text: str, source: str) -> int:
        """
        Add documents to the vector store using LangChain's text splitter.
        
        Args:
            text: Raw text to chunk and embed
            source: Source identifier (filename)
            
        Returns:
            Number of chunks added
        """
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            
            if not chunks:
                return 0
            
            # Create Document objects with metadata
            documents = [
                Document(
                    page_content=chunk,
                    metadata={"source": source, "chunk_id": i}
                )
                for i, chunk in enumerate(chunks)
            ]
            
            # Store documents for this source
            if source not in self.source_docs:
                self.source_docs[source] = []
            self.source_docs[source].extend(documents)
            
            # Add to vector store
            if self.vectorstore is None:
                if self.vectorstore_type == "chroma":
                    # Create persistent Chroma store
                    self.vectorstore = Chroma.from_documents(
                        documents,
                        self.embeddings,
                        persist_directory=self.vectorstore_path,
                    )
                    # Ensure persistence after creation
                    try:
                        self.vectorstore.persist()
                    except Exception:
                        pass
                    logging.info(f"[LangChain] Created new Chroma vectorstore at {self.vectorstore_path} with {len(documents)} docs from {source}")
                else:
                    # Default to FAISS
                    self.vectorstore = FAISS.from_documents(documents, self.embeddings)
                    logging.info(f"[LangChain] Created new FAISS vectorstore with {len(documents)} docs from {source}")
            else:
                # Add to existing vector store
                self.vectorstore.add_documents(documents)
                # Persist for Chroma
                if self.vectorstore_type == "chroma":
                    try:
                        self.vectorstore.persist()
                    except Exception:
                        pass
                logging.info(f"[LangChain] Added {len(documents)} docs from {source} to existing vectorstore")
            
            return len(documents)
            
        except Exception as e:
            logging.exception(f"[LangChain] Failed to add documents: {e}")
            return 0
    
    async def query_with_rag(self, query: str, sources: Optional[List[str]] = None, top_k: int = 4) -> str:
        """
        Query the LLM with RAG context from vector store.
        
        Args:
            query: User question
            sources: Optional list of source filenames to filter by
            top_k: Number of chunks to retrieve
            
        Returns:
            LLM response
        """
        try:
            if self.vectorstore is None:
                return "No documents have been indexed yet. Please upload a document first."
            
            # Filter documents by source if specified
            if sources:
                # Get all documents matching the sources
                relevant_docs = []
                for source in sources:
                    if source in self.source_docs:
                        relevant_docs.extend(self.source_docs[source])
                
                if not relevant_docs:
                    return f"No documents found for sources: {sources}"
                
                # Create a temporary vectorstore with only relevant docs
                # Using FAISS for temp store is fine even if primary is Chroma.
                temp_vectorstore = FAISS.from_documents(relevant_docs, self.embeddings)
                retriever = temp_vectorstore.as_retriever(search_kwargs={"k": top_k})
                logging.info(f"[LangChain] Filtering by sources: {sources}, docs: {len(relevant_docs)}")
            else:
                # Use all documents
                retriever = self.vectorstore.as_retriever(search_kwargs={"k": top_k})
                logging.info(f"[LangChain] Using all documents in vectorstore")
            
            # Create custom prompt template
            template = """You are a helpful AI assistant. Use the following context to answer the question.
If the answer is not in the context, say "I don't have enough information to answer that."

Context:
{context}

Question: {question}

Answer:"""
            
            prompt = PromptTemplate(
                input_variables=["context", "question"],
                template=template
            )
            
            # Create RetrievalQA chain
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",  # "stuff" means put all docs into context
                retriever=retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": prompt}
            )
            
            # Execute query
            result = qa_chain.invoke({"query": query})
            
            # Log retrieved sources
            source_names = [doc.metadata.get("source", "unknown") for doc in result.get("source_documents", [])]
            logging.info(f"[LangChain] Retrieved {len(result.get('source_documents', []))} chunks from: {set(source_names)}")
            
            return result["result"]
            
        except Exception as e:
            logging.exception(f"[LangChain] Query with RAG failed: {e}")
            return f"Error processing RAG query: {str(e)}"
    
    async def query_without_rag(self, query: str) -> str:
        """
        Query the LLM directly without RAG context.
        
        Args:
            query: User question
            
        Returns:
            LLM response
        """
        try:
            prompt = f"""You are a helpful AI assistant. Provide clear, concise, and accurate responses.

User: {query}
Assistant:"""
            
            response = self.llm.invoke(prompt)
            logging.info(f"[LangChain] Direct query (no RAG): {query[:50]}")
            return response.strip()
            
        except Exception as e:
            logging.exception(f"[LangChain] Direct query failed: {e}")
            return f"Error processing query: {str(e)}"
    
    def stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        if self.vectorstore is None:
            return {
                "total_chunks": 0,
                "sources": {},
                "embed_model": self.embed_model,
                "system": "langchain"
            }
        
        sources = {}
        for source, docs in self.source_docs.items():
            sources[source] = len(docs)
        
        total_chunks = sum(sources.values())
        
        return {
            "total_chunks": total_chunks,
            "sources": sources,
            "embed_model": self.embed_model,
            "llm_model": self.ollama_model,
            "system": "langchain"
        }
    
    def clear_source(self, source: str) -> bool:
        """Remove all documents from a specific source"""
        if source in self.source_docs:
            del self.source_docs[source]
            # Rebuild vectorstore without this source
            if self.source_docs:
                all_docs = []
                for docs in self.source_docs.values():
                    all_docs.extend(docs)
                if self.vectorstore_type == "chroma":
                    self.vectorstore = Chroma.from_documents(all_docs, self.embeddings, persist_directory=self.vectorstore_path)
                    try:
                        self.vectorstore.persist()
                    except Exception:
                        pass
                else:
                    self.vectorstore = FAISS.from_documents(all_docs, self.embeddings)
            else:
                self.vectorstore = None
            logging.info(f"[LangChain] Cleared source: {source}")
            return True
        return False
