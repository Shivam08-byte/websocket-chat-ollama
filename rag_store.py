import os
import json
import uuid
from typing import List, Dict, Any, Tuple

import numpy as np
import httpx


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


class RAGStore:
    def __init__(self, ollama_host: str, embed_model: str = "nomic-embed-text", store_path: str = "rag_store.json"):
        self.ollama_host = ollama_host.rstrip('/')
        self.embed_model = embed_model
        self.store_path = store_path
        self.chunks: List[Dict[str, Any]] = []
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.embed_model = data.get("embed_model", self.embed_model)
                    self.chunks = data.get("chunks", [])
            except Exception:
                # Corrupt or incompatible; start fresh
                self.chunks = []
        self._loaded = True

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.store_path) or '.', exist_ok=True)
        data = {
            "embed_model": self.embed_model,
            "chunks": self.chunks,
        }
        with open(self.store_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

    @staticmethod
    def _split_text(text: str, chunk_size: int = 800, overlap: int = 200) -> List[str]:
        text = text.replace('\r\n', '\n')
        # Simple character-based splitter with overlap
        chunks: List[str] = []
        start = 0
        n = len(text)
        # Normalize whitespace a bit
        text = '\n'.join([line.strip() for line in text.split('\n')])
        while start < n:
            end = min(start + chunk_size, n)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end == n:
                break
            start = max(0, end - overlap)
        return chunks

    async def _embed(self, client: httpx.AsyncClient, text: str) -> List[float]:
        resp = await client.post(
            f"{self.ollama_host}/api/embeddings",
            json={"model": self.embed_model, "prompt": text}
        )
        resp.raise_for_status()
        data = resp.json()
        emb = data.get("embedding")
        if not isinstance(emb, list):
            raise RuntimeError("Invalid embedding response from Ollama")
        return emb

    async def add_text(self, text: str, source: str = "uploaded", chunk_size: int = 800, overlap: int = 200) -> int:
        self._load()
        chunks = self._split_text(text, chunk_size=chunk_size, overlap=overlap)
        if not chunks:
            return 0
        added = 0
        async with httpx.AsyncClient(timeout=120.0) as client:
            for ch in chunks:
                emb = await self._embed(client, ch)
                self.chunks.append({
                    "id": str(uuid.uuid4()),
                    "text": ch,
                    "source": source,
                    "embedding": emb,
                })
                added += 1
        self._save()
        return added

    def stats(self) -> Dict[str, Any]:
        self._load()
        sources = {}
        for c in self.chunks:
            s = c.get("source", "unknown")
            sources[s] = sources.get(s, 0) + 1
        return {"chunks": len(self.chunks), "sources": sources, "embed_model": self.embed_model}

    async def retrieve(self, query: str, top_k: int = 4, sources: List[str] | None = None) -> List[Dict[str, Any]]:
        self._load()
        if not self.chunks:
            return []
        async with httpx.AsyncClient(timeout=60.0) as client:
            q_emb = await self._embed(client, query)
        q_vec = np.array(q_emb, dtype=np.float32)
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for c in self.chunks:
            if sources and c.get("source") not in sources:
                continue
            v = np.array(c["embedding"], dtype=np.float32)
            score = _cosine_sim(q_vec, v)
            scored.append((score, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[: max(1, top_k)]]

    async def build_context(self, query: str, top_k: int = 4, max_chars: int = 2000, sources: List[str] | None = None) -> str:
        matches = await self.retrieve(query, top_k=top_k, sources=sources)
        if not matches:
            return ""
        parts: List[str] = []
        total = 0
        for m in matches:
            block = f"Source: {m.get('source','unknown')}\n{m['text']}"
            if total + len(block) > max_chars:
                remaining = max_chars - total
                if remaining <= 0:
                    break
                block = block[:remaining]
            parts.append(block)
            total += len(block)
            if total >= max_chars:
                break
        return "\n\n---\n\n".join(parts)
