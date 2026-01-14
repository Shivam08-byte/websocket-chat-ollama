#!/usr/bin/env python3
"""
Smoke tests for common endpoints: health, models, system switching.

Usage:
  python tests/test_health.py --base-url http://localhost:8081
"""

import argparse
import os
from pathlib import Path
import requests


def detect_base_url(default: str = "http://localhost:8081") -> str:
    # Prefer env or builds/.env
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

    # Health
    r = sess.get(f"{base}/health", timeout=20)
    print("Health:", r.status_code, r.json())

    # Models
    r = sess.get(f"{base}/api/models", timeout=30)
    print("Models:", r.status_code, list(r.json().get("available_models", {}).keys()))

    # Load a known model (idempotent)
    payload = {"model": r.json().get("current_model", "gemma:2b")}
    r = sess.post(f"{base}/api/models/load", json=payload, timeout=180)
    print("Load model:", r.status_code, r.json())

    # System switch
    for system in ("manual", "langchain"):
        r = sess.post(f"{base}/api/system/switch", json={"system": system}, timeout=20)
        print("Switch system:", system, r.status_code, r.json())
        r = sess.get(f"{base}/api/system/current", timeout=20)
        print("Current system:", r.status_code, r.json())

    print("Done: common endpoints OK")


if __name__ == "__main__":
    main()
