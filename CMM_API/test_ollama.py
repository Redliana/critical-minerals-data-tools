"""Test CMM API with Ollama (local LLM).

Uses simple query approach since tool calling isn't reliable with all models.
"""

import json

import httpx

API_BASE = "http://127.0.0.1:8000"
OLLAMA_BASE = "http://127.0.0.1:11434"
MODEL = "phi4"


def fetch_data(endpoint: str, params: dict = None) -> dict:
    """Fetch data from CMM API."""
    resp = httpx.get(f"{API_BASE}{endpoint}", params=params, timeout=60.0)
    return resp.json()


def ask_ollama(prompt: str, data: dict) -> str:
    """Ask Ollama to analyze the data."""
    messages = [
        {
            "role": "system",
            "content": "You are a critical minerals analyst. Analyze the provided data and answer concisely.",
        },
        {"role": "user", "content": f"{prompt}\n\nData:\n{json.dumps(data, indent=2)[:6000]}"},
    ]

    resp = httpx.post(
        f"{OLLAMA_BASE}/api/chat",
        json={"model": MODEL, "messages": messages, "stream": False},
        timeout=120.0,
    )
    return resp.json()["message"]["content"]


def main():
    print("=" * 60)
    print("CMM API + Ollama (phi4) Integration Test")
    print("=" * 60)

    # Test 1: Data Overview
    print("\n[1] What data sources are available?")
    print("-" * 50)
    data = fetch_data("/overview")
    answer = ask_ollama("Summarize the available data sources and what they contain.", data)
    print(answer)

    # Test 2: Lithium Rankings (BGS)
    print("\n[2] Top lithium producing countries")
    print("-" * 50)
    data = fetch_data("/bgs/ranking/lithium minerals", {"top_n": 5})
    answer = ask_ollama("Who are the top lithium producers and what's their market share?", data)
    print(answer)

    # Test 3: CLAIMM Datasets
    print("\n[3] Search for cobalt datasets in CLAIMM")
    print("-" * 50)
    data = fetch_data("/claimm/datasets", {"q": "cobalt", "limit": 5})
    answer = ask_ollama(
        "What cobalt-related datasets are available? List their titles and what data they contain.",
        data,
    )
    print(answer)

    # Test 4: Unified Search
    print("\n[4] Unified search for rare earth data")
    print("-" * 50)
    data = fetch_data("/search", {"q": "rare earth", "limit": 5})
    answer = ask_ollama(
        "Summarize the rare earth data available from both CLAIMM and BGS sources.", data
    )
    print(answer)

    # Test 5: Cobalt Rankings (BGS)
    print("\n[5] Cobalt supply chain analysis")
    print("-" * 50)
    data = fetch_data("/bgs/ranking/cobalt, mine", {"top_n": 10})
    answer = ask_ollama(
        "Analyze the cobalt supply chain. Which countries dominate? What are the supply chain risks?",
        data,
    )
    print(answer)

    print("\n" + "=" * 60)
    print("Test complete!")


if __name__ == "__main__":
    main()
