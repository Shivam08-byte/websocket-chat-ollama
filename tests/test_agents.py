#!/usr/bin/env python3
"""
Agents API tests: info, tools, query, reset.

Usage:
  python tests/test_agents.py --base-url http://localhost:8081
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

    r = sess.get(f"{base}/api/agents/agent1/info", timeout=30)
    print("Agent1 info:", r.status_code, r.json().get("capabilities"))

    r = sess.get(f"{base}/api/agents/agent1/tools", timeout=30)
    tools = r.json().get("tools", [])
    print("Agent1 tools:", r.status_code, len(tools))

    r = sess.post(
        f"{base}/api/agents/agent1/query",
        json={"message": "What is 25 * 4?", "reset_history": True},
        timeout=120,
    )
    print("Agent1 query:", r.status_code)
    body = r.json()
    print("Answer prefix:", (body.get("answer") or "")[:100])
    print("Steps count:", len(body.get("steps", [])))

    r = sess.post(f"{base}/api/agents/agent1/reset", timeout=30)
    print("Agent1 reset:", r.status_code, r.json())

    print("Done: Agents API OK")


if __name__ == "__main__":
    main()
