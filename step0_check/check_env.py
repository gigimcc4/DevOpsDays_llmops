"""
Prework verification — run BEFORE the workshop.

This script checks that every piece of the stack is installed and reachable:
  * Python version
  * Docker daemon
  * Langfuse container reachable on localhost:3000
  * Ollama reachable on localhost:11434
  * Required models pulled (llama3.2:1b, all-minilm)
  * Python deps importable

If anything fails, the message tells you exactly what to do.
Run: python step0_check/check_env.py
"""
from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
import urllib.error
import urllib.request


GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
END = "\033[0m"


def ok(msg: str) -> None:
    print(f"  {GREEN}[OK]{END}   {msg}")


def warn(msg: str, fix: str) -> None:
    print(f"  {YELLOW}[WARN]{END} {msg}")
    print(f"         fix: {fix}")


def fail(msg: str, fix: str) -> None:
    print(f"  {RED}[FAIL]{END} {msg}")
    print(f"         fix: {fix}")


def header(msg: str) -> None:
    print(f"\n{BOLD}{msg}{END}")


def check_python() -> bool:
    header("Python")
    v = sys.version_info
    if v >= (3, 10):
        ok(f"Python {v.major}.{v.minor}.{v.micro}")
        return True
    fail(
        f"Python {v.major}.{v.minor} is too old (need 3.10+)",
        "install Python 3.10 or newer (https://www.python.org/downloads/)",
    )
    return False


def check_docker() -> bool:
    header("Docker")
    if not shutil.which("docker"):
        fail("docker CLI not found", "install Docker Desktop: https://www.docker.com/products/docker-desktop")
        return False
    try:
        r = subprocess.run(
            ["docker", "info"], capture_output=True, text=True, timeout=10
        )
        if r.returncode != 0:
            fail("Docker daemon not running", "start Docker Desktop and wait for the whale icon to stop animating")
            return False
        ok("Docker daemon is running")
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        fail(f"could not talk to docker: {e}", "start Docker Desktop")
        return False


def check_langfuse() -> bool:
    header("Langfuse (http://localhost:3000)")
    try:
        with urllib.request.urlopen("http://localhost:3000/api/public/health", timeout=5) as r:
            if r.status == 200:
                ok("Langfuse is up")
                return True
            fail(f"Langfuse responded {r.status}", "docker compose up -d")
            return False
    except (urllib.error.URLError, TimeoutError) as e:
        fail(f"Langfuse not reachable: {e}", "from the repo root: docker compose up -d")
        return False


def check_ollama() -> bool:
    header("Ollama (http://localhost:11434)")
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5) as r:
            import json

            data = json.loads(r.read().decode())
    except (urllib.error.URLError, TimeoutError) as e:
        fail(f"Ollama not reachable: {e}", "install and start Ollama: https://ollama.com/download")
        return False
    ok("Ollama is reachable")

    names = {m["name"].split(":")[0] + ":" + m["name"].split(":")[1] if ":" in m["name"] else m["name"]
             for m in data.get("models", [])}
    # Simpler: flatten
    raw_names = {m["name"] for m in data.get("models", [])}

    need_llm = any(n.startswith("llama3.2:1b") for n in raw_names)
    need_emb = any(n.startswith("all-minilm") for n in raw_names)

    if need_llm:
        ok("llama3.2:1b is pulled")
    else:
        fail("llama3.2:1b is not pulled", "ollama pull llama3.2:1b")
    if need_emb:
        ok("all-minilm is pulled")
    else:
        fail("all-minilm is not pulled", "ollama pull all-minilm")

    return need_llm and need_emb


def check_python_deps() -> bool:
    header("Python packages")
    all_good = True
    for pkg, import_name in [
        ("ollama", "ollama"),
        ("chromadb", "chromadb"),
        ("langfuse", "langfuse"),
        ("opentelemetry-api", "opentelemetry"),
        ("python-dotenv", "dotenv"),
        ("rich", "rich"),
    ]:
        try:
            importlib.import_module(import_name)
            ok(f"{pkg}")
        except ImportError:
            fail(f"{pkg} not installed", "pip install -r requirements.txt")
            all_good = False
    return all_good


def main() -> int:
    print(f"{BOLD}LLMOps Workshop — Prework Verification{END}")
    print("Checking your environment is ready for the 90-minute build.\n")

    results = [
        check_python(),
        check_docker(),
        check_python_deps(),
        check_langfuse(),
        check_ollama(),
    ]

    print()
    if all(results):
        print(f"{GREEN}{BOLD}All checks passed.{END} You're ready for the workshop.\n")
        return 0
    print(f"{RED}{BOLD}Some checks failed.{END} Fix the items above and re-run.\n")
    print("If stuck, see PREWORK.md or post in the workshop Slack channel.\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
