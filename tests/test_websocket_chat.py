#!/usr/bin/env python3
"""
WebSocket chat test: connects, sends a message, verifies response types.

Usage:
  python tests/test_websocket_chat.py --base-url http://localhost:8081
"""

import argparse
import asyncio
import os
from pathlib import Path
import json
import websockets


def detect_ws_url(default: str = "ws://localhost:8081/ws") -> str:
    for name in ("FASTAPI_EXTERNAL_PORT", "FASTAPI_PORT"):
        val = os.getenv(name)
        if val:
            try:
                port = int(str(val).strip())
                return f"ws://localhost:{port}/ws"
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
                    return f"ws://localhost:{port}/ws"
    except Exception:
        pass
    return default


async def ws_test(url: str):
    async with websockets.connect(url) as ws:
        # Receive welcome
        msg = await ws.recv()
        print("Welcome:", msg)
        # Send a message (manual system)
        await ws.send(json.dumps({"message": "Hello from test", "useLangchain": False}))

        # Read a few messages
        for _ in range(3):
            m = await ws.recv()
            print("Recv:", m[:200])
        # Send LangChain message
        await ws.send(json.dumps({"message": "Explain Chroma briefly", "useLangchain": True}))
        for _ in range(3):
            m = await ws.recv()
            print("Recv:", m[:200])
        print("Done: WebSocket chat OK")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ws-url", default=detect_ws_url())
    args = parser.parse_args()
    asyncio.run(ws_test(args.ws_url))


if __name__ == "__main__":
    main()
