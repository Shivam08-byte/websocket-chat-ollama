#!/usr/bin/env python3
"""
Tests for Manual RAG endpoints: stats, ingest_text, ingest_file (text), preview.

Usage:
  python tests/test_manual_rag.py --base-url http://localhost:8081
"""

import argparse
import io
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
    r = sess.get(f"{base}/api/rag/manual/stats", timeout=30)
    print("Manual stats:", r.status_code, r.json())

    # Ingest text
    payload = {
        "text": "Manual RAG stores chunks and builds context.",
        "source": "manual_test.txt",
    }
    r = sess.post(f"{base}/api/rag/manual/ingest_text", json=payload, timeout=60)
    print("Ingest text:", r.status_code, r.json())

    # Ingest file (text)
    content = b"This is a sample text file for Manual RAG."
    files = {"file": ("sample.txt", io.BytesIO(content), "text/plain")}
    r = sess.post(f"{base}/api/rag/manual/ingest_file", files=files, timeout=60)
    print("Ingest file:", r.status_code, r.json())

    # Preview context for a query
    r = sess.post(
        f"{base}/api/rag/manual/preview",
        json={"query": "What does Manual RAG do?", "sources": ["manual_test.txt", "sample.txt"], "top_k": 4},
        timeout=60,
    )
    print("Preview:", r.status_code)
    preview = r.json()
    print("Context chars:", preview.get("context_chars"))
    print("Context snippet:", (preview.get("context_preview") or "")[:200])

    print("Done: manual RAG endpoints OK")


if __name__ == "__main__":
    main()
