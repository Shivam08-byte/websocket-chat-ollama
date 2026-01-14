#!/usr/bin/env python3
"""
Basic tests for LangChain RAG endpoints: stats, ingest_text, query.

Usage:
  python tests/test_langchain_rag_basic.py --base-url http://localhost:8081
"""

import argparse
import os
from pathlib import Path
import requests


def detect_base_url(default: str = "http://localhost:8081") -> str:
    for name in ("FASTAPI_EXTERNAL_PORT", "FASTAPI_PORT"):
        val = os.getenv(name)
        if val:
            try:
                port = int(str(val).strip())
                return f"http://localhost:{port}"
            except Exception:
                pass
    try:
        root = Path(__file__).resolve().parents[1]
        env_path = root / "builds" / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                s = line.strip()
                if s.startswith("FASTAPI_EXTERNAL_PORT") and "=" in s:
                    port = int(s.split("=", 1)[1].strip().strip('"').strip("'"))
                    return f"http://localhost:{port}"
    except Exception:
        pass
    return default


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=detect_base_url())
    args = parser.parse_args()
    base = args.base_url.rstrip('/')
    sess = requests.Session()

    # Stats
    r = sess.get(f"{base}/api/rag/langchain/stats", timeout=30)
    print("LangChain stats:", r.status_code, r.json())

    # Ingest text
    payload = {
        "text": "Chroma stores embeddings persistently; FAISS stores in-memory.",
        "source": "lc_test.txt",
    }
    r = sess.post(f"{base}/api/rag/langchain/ingest_text", json=payload, timeout=60)
    print("LC ingest:", r.status_code, r.json())

    # Query
    r = sess.post(
        f"{base}/api/rag/langchain/query",
        json={"query": "What is Chroma?", "sources": ["lc_test.txt"], "top_k": 4},
        timeout=60,
    )
    print("LC query:", r.status_code)
    print("Response:", (r.json().get("response") or "")[:200])

    print("Done: LangChain RAG basic OK")


if __name__ == "__main__":
    main()
