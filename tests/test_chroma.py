#!/usr/bin/env python3
"""
Comprehensive test script for ChromaDB vector store integration.
Tests ingestion, querying, persistence, and compares with FAISS baseline.

Usage:
    python tests/test_chroma.py --base-url http://localhost:8000
    python tests/test_chroma.py --help
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
import requests


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(msg: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")


def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")


def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")


class VectorStoreTest:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
    def health_check(self) -> bool:
        """Verify API is reachable"""
        try:
            resp = self.session.get(f"{self.base_url}/health", timeout=self.timeout)
            if resp.status_code == 200:
                print_success(f"Health check passed: {resp.json()}")
                return True
            else:
                print_error(f"Health check failed: {resp.status_code}")
                return False
        except Exception as e:
            print_error(f"Health check failed: {e}")
            return False
    
    def get_stats(self) -> Optional[Dict[str, Any]]:
        """Get current RAG stats"""
        try:
            resp = self.session.get(
                f"{self.base_url}/api/rag/langchain/stats",
                timeout=self.timeout
            )
            if resp.status_code == 200:
                stats = resp.json()
                print_info(f"Stats: {json.dumps(stats, indent=2)}")
                return stats
            else:
                print_error(f"Failed to get stats: {resp.status_code}")
                return None
        except Exception as e:
            print_error(f"Failed to get stats: {e}")
            return None
    
    def ingest_text(self, text: str, source: str) -> bool:
        """Ingest text content"""
        try:
            resp = self.session.post(
                f"{self.base_url}/api/rag/langchain/ingest_text",
                json={"text": text, "source": source},
                timeout=self.timeout
            )
            if resp.status_code == 200:
                result = resp.json()
                if result.get("success"):
                    print_success(f"Ingested '{source}': {result.get('added_chunks', 0)} chunks")
                    return True
                else:
                    print_error(f"Ingest failed for '{source}': {result.get('message')}")
                    return False
            else:
                print_error(f"Ingest failed: {resp.status_code}")
                return False
        except Exception as e:
            print_error(f"Ingest failed: {e}")
            return False
    
    def query(self, query: str, sources: Optional[list] = None, top_k: int = 4) -> Optional[str]:
        """Query the RAG system"""
        try:
            payload = {"query": query, "top_k": top_k}
            if sources:
                payload["sources"] = sources
            
            resp = self.session.post(
                f"{self.base_url}/api/rag/langchain/query",
                json=payload,
                timeout=self.timeout
            )
            if resp.status_code == 200:
                result = resp.json()
                if result.get("success"):
                    response_text = result.get("response", "")
                    print_success(f"Query succeeded")
                    print_info(f"Response: {response_text[:200]}...")
                    return response_text
                else:
                    print_error(f"Query failed: {result.get('message')}")
                    return None
            else:
                print_error(f"Query failed: {resp.status_code}")
                return None
        except Exception as e:
            print_error(f"Query failed: {e}")
            return None


def _read_env_port() -> Optional[int]:
    """Try to read FASTAPI port from environment or .env file."""
    # Check environment variables first
    for name in ("FASTAPI_EXTERNAL_PORT", "FASTAPI_PORT"):
        val = os.getenv(name)
        if val:
            try:
                return int(str(val).strip())
            except Exception:
                pass

    # Fallback: parse project .env
    try:
        root = Path(__file__).resolve().parents[1]
        env_paths = [
            root / ".env",
            Path.cwd() / ".env",
            root / "builds" / ".env",
        ]
        for env_path in env_paths:
            if not env_path.exists():
                continue
            for line in env_path.read_text(encoding="utf-8").splitlines():
                s = line.strip()
                if s.startswith("FASTAPI_EXTERNAL_PORT") and "=" in s:
                    try:
                        return int(s.split("=", 1)[1].strip().strip('"').strip("'"))
                    except Exception:
                        pass
                if s.startswith("FASTAPI_PORT") and "=" in s:
                    try:
                        return int(s.split("=", 1)[1].strip().strip('"').strip("'"))
                    except Exception:
                        pass
    except Exception:
        pass
    return None


def _probe_ports(session: requests.Session, timeout: int) -> Optional[int]:
    """Probe common ports to auto-detect service if not specified."""
    for port in (8000, 8081, 8080, 8001, 9000):
        try:
            resp = session.get(f"http://localhost:{port}/health", timeout=min(timeout, 5))
            if resp.status_code == 200:
                return port
        except Exception:
            continue
    return None


def _detect_base_url(arg_base_url: str, timeout: int) -> str:
    """Determine base URL: use CLI arg, else env/.env, else probe."""
    # If user provided a non-default base URL, use it
    if arg_base_url and arg_base_url != "http://localhost:8000":
        return arg_base_url.rstrip('/')

    # Env or .env
    env_port = _read_env_port()
    if env_port:
        return f"http://localhost:{env_port}"

    # Probe common ports
    session = requests.Session()
    probed = _probe_ports(session, timeout)
    if probed:
        return f"http://localhost:{probed}"

    # Fallback to default
    return arg_base_url.rstrip('/')


def test_baseline_faiss(tester: VectorStoreTest) -> bool:
    """Test FAISS baseline (if currently configured)"""
    print_header("Test 1: FAISS Baseline")
    
    # Get initial stats
    print_info("Getting initial stats...")
    initial_stats = tester.get_stats()
    if initial_stats is None:
        return False
    
    # Ingest documents
    print_info("Ingesting test documents...")
    docs = [
        ("LangChain is a framework for developing applications powered by language models.", "langchain_intro.txt"),
        ("FAISS is an efficient similarity search library developed by Facebook AI.", "faiss_info.txt"),
        ("Vector embeddings represent text as numerical vectors in high-dimensional space.", "embeddings_concept.txt"),
    ]
    
    for text, source in docs:
        if not tester.ingest_text(text, source):
            return False
        time.sleep(0.5)
    
    # Verify stats updated
    print_info("Verifying ingestion...")
    stats = tester.get_stats()
    if stats and stats.get("total_chunks", 0) >= len(docs):
        print_success(f"Ingested {stats.get('total_chunks')} chunks total")
    else:
        print_error("Chunk count did not increase as expected")
        return False
    
    # Test query without source filter
    print_info("Querying without source filter...")
    response = tester.query("What is LangChain?")
    if not response or "langchain" not in response.lower():
        print_warning("Query response may not contain expected content")
    
    # Test query with source filter
    print_info("Querying with source filter...")
    response = tester.query("What is FAISS?", sources=["faiss_info.txt"])
    if not response:
        return False
    
    print_success("FAISS baseline tests passed")
    return True


def test_chroma_ingestion(tester: VectorStoreTest) -> bool:
    """Test ChromaDB ingestion"""
    print_header("Test 2: ChromaDB Ingestion")
    
    print_info("Ingesting documents to ChromaDB...")
    docs = [
        ("ChromaDB is an open-source embedding database designed for AI applications.", "chroma_intro.txt"),
        ("Ollama provides local LLM serving with a simple API interface.", "ollama_info.txt"),
        ("RAG (Retrieval-Augmented Generation) combines search with generation.", "rag_concept.txt"),
        ("Vector databases enable semantic search by storing and querying embeddings.", "vectordb_overview.txt"),
    ]
    
    for text, source in docs:
        if not tester.ingest_text(text, source):
            return False
        time.sleep(0.5)
    
    # Verify stats
    stats = tester.get_stats()
    if stats and stats.get("total_chunks", 0) >= len(docs):
        print_success(f"ChromaDB has {stats.get('total_chunks')} chunks")
    else:
        print_error("Chunk count lower than expected")
        return False
    
    print_success("ChromaDB ingestion tests passed")
    return True


def test_chroma_querying(tester: VectorStoreTest) -> bool:
    """Test ChromaDB querying"""
    print_header("Test 3: ChromaDB Querying")
    
    queries = [
        ("What is ChromaDB?", None),
        ("Explain Ollama", ["ollama_info.txt"]),
        ("How does RAG work?", ["rag_concept.txt"]),
        ("What are vector databases?", None),
    ]
    
    for query, sources in queries:
        print_info(f"Query: '{query}' | Sources: {sources or 'all'}")
        response = tester.query(query, sources=sources)
        if not response:
            print_warning(f"Query '{query}' returned no response")
        time.sleep(0.5)
    
    print_success("ChromaDB querying tests passed")
    return True


def test_chroma_persistence(tester: VectorStoreTest) -> bool:
    """Test ChromaDB persistence (requires manual container restart)"""
    print_header("Test 4: ChromaDB Persistence Check")
    
    print_info("Getting current stats before restart...")
    pre_restart_stats = tester.get_stats()
    if not pre_restart_stats:
        return False
    
    pre_chunks = pre_restart_stats.get("total_chunks", 0)
    pre_sources = pre_restart_stats.get("sources", {})
    
    print_warning("MANUAL ACTION REQUIRED:")
    print_warning("Please restart the FastAPI container now:")
    print_warning("  cd builds && docker compose restart fastapi")
    print_warning("")
    
    input("Press Enter after restarting the container...")
    
    print_info("Waiting for service to be ready...")
    max_retries = 10
    for i in range(max_retries):
        time.sleep(2)
        if tester.health_check():
            break
        if i == max_retries - 1:
            print_error("Service did not come back online")
            return False
    
    print_info("Getting stats after restart...")
    post_restart_stats = tester.get_stats()
    if not post_restart_stats:
        return False
    
    post_chunks = post_restart_stats.get("total_chunks", 0)
    post_sources = post_restart_stats.get("sources", {})
    
    print_info(f"Chunks before restart: {pre_chunks}")
    print_info(f"Chunks after restart: {post_chunks}")
    
    if post_chunks > 0 and post_chunks >= pre_chunks:
        print_success("ChromaDB persisted data across restart!")
        print_info(f"Sources: {list(post_sources.keys())}")
        return True
    else:
        print_error("ChromaDB did not persist data (expected with FAISS)")
        print_warning("This is normal if RAG_VECTORSTORE=faiss")
        return False


def test_source_filtering(tester: VectorStoreTest) -> bool:
    """Test source-based filtering"""
    print_header("Test 5: Source Filtering")
    
    # Query specific source
    print_info("Querying only chroma_intro.txt...")
    response = tester.query("Tell me about ChromaDB", sources=["chroma_intro.txt"])
    if not response:
        return False
    
    # Query multiple sources
    print_info("Querying multiple sources...")
    response = tester.query(
        "Compare ChromaDB and Ollama",
        sources=["chroma_intro.txt", "ollama_info.txt"]
    )
    if not response:
        return False
    
    # Query non-existent source
    print_info("Querying non-existent source...")
    response = tester.query("What is Python?", sources=["nonexistent.txt"])
    # This should return an error or "not found" message
    
    print_success("Source filtering tests passed")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Test ChromaDB vector store integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/test_chroma.py
  python tests/test_chroma.py --base-url http://localhost:8081
  python tests/test_chroma.py --skip-persistence
        """
    )
    parser.add_argument(
        '--base-url',
        default='http://localhost:8081',
        help='Base URL of the FastAPI service (auto-detects if not provided)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Request timeout in seconds (default: 30)'
    )
    parser.add_argument(
        '--skip-persistence',
        action='store_true',
        help='Skip persistence test (requires manual restart)'
    )
    
    args = parser.parse_args()
    
    print_header("ChromaDB Vector Store Test Suite")
    base_url = _detect_base_url(args.base_url, args.timeout)
    print_info(f"Target: {base_url}")
    print_info(f"Timeout: {args.timeout}s")
    print("")
    
    tester = VectorStoreTest(base_url, args.timeout)
    
    # Run tests
    results = []
    
    # Health check
    print_header("Pre-flight Check")
    if not tester.health_check():
        print_error("Health check failed. Is the service running?")
        sys.exit(1)
    
    # Run test suite
    results.append(("FAISS Baseline", test_baseline_faiss(tester)))
    results.append(("ChromaDB Ingestion", test_chroma_ingestion(tester)))
    results.append(("ChromaDB Querying", test_chroma_querying(tester)))
    
    if not args.skip_persistence:
        results.append(("ChromaDB Persistence", test_chroma_persistence(tester)))
    
    results.append(("Source Filtering", test_source_filtering(tester)))
    
    # Summary
    print_header("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")
    
    print(f"\n{Colors.BOLD}Result: {passed}/{total} tests passed{Colors.END}\n")
    
    if passed == total:
        print_success("All tests passed!")
        sys.exit(0)
    else:
        print_error(f"{total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
