#!/usr/bin/env python3
"""Test BGS REST API with Ollama (local LLM)."""

from __future__ import annotations

import json

import httpx

# Configuration
BGS_API_URL = "http://127.0.0.1:8000"
OLLAMA_URL = "http://127.0.0.1:11434"
MODEL = "phi4"  # or "llama3.2", "mistral", "qwen2.5", etc.


def get_bgs_tools():
    """Get tool definitions for Ollama (same format as OpenAI)."""
    response = httpx.get(f"{BGS_API_URL}/openai/functions")
    response.raise_for_status()
    functions = response.json()

    # Convert to Ollama tool format
    tools = []
    for f in functions:
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": f["name"],
                    "description": f["description"],
                    "parameters": f["parameters"],
                },
            }
        )
    return tools


def call_bgs_api(function_name: str, arguments: dict) -> dict:
    """Call the appropriate BGS API endpoint."""
    endpoint_map = {
        "search_mineral_production": "/production/search",
        "get_top_producers": "/production/ranking",
        "get_production_time_series": "/production/timeseries",
        "compare_country_production": "/production/compare",
        "list_critical_minerals": "/commodities",
    }

    endpoint = endpoint_map.get(function_name)
    if not endpoint:
        return {"error": f"Unknown function: {function_name}"}

    # Map function arguments to API parameters
    params = {}
    if function_name == "search_mineral_production":
        params = {
            "commodity": arguments.get("commodity"),
            "country": arguments.get("country"),
            "year_from": arguments.get("year_from"),
            "year_to": arguments.get("year_to"),
            "limit": 15,
        }
    elif function_name == "get_top_producers":
        params = {
            "commodity": arguments.get("commodity"),
            "year": arguments.get("year"),
            "top_n": arguments.get("top_n", 10),
        }
    elif function_name == "get_production_time_series":
        params = {
            "commodity": arguments.get("commodity"),
            "country": arguments.get("country"),
        }
    elif function_name == "compare_country_production":
        params = {
            "commodity": arguments.get("commodity"),
            "countries": arguments.get("countries"),
        }
    elif function_name == "list_critical_minerals":
        params = {"critical_only": True}

    params = {k: v for k, v in params.items() if v is not None}

    response = httpx.get(f"{BGS_API_URL}{endpoint}", params=params, timeout=30.0)
    response.raise_for_status()
    return response.json()


def chat_with_ollama(user_message: str) -> str:
    """Chat with Ollama using tool calling."""
    tools = get_bgs_tools()

    print(f"\n{'=' * 60}")
    print(f"User: {user_message}")
    print("=" * 60)

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant with access to BGS World Mineral Statistics. "
            "Use the provided tools to answer questions about mineral production. "
            "Always call a tool when asked about mineral data.",
        },
        {"role": "user", "content": user_message},
    ]

    # First call to Ollama
    response = httpx.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": MODEL,
            "messages": messages,
            "tools": tools,
            "stream": False,
        },
        timeout=120.0,
    )
    response.raise_for_status()
    result = response.json()

    assistant_message = result.get("message", {})
    tool_calls = assistant_message.get("tool_calls", [])

    if tool_calls:
        print(f"\nOllama requested {len(tool_calls)} tool call(s):")

        messages.append(assistant_message)

        for tool_call in tool_calls:
            function = tool_call.get("function", {})
            function_name = function.get("name", "")
            arguments = function.get("arguments", {})

            print(f"\n  Tool: {function_name}")
            print(f"  Args: {json.dumps(arguments, indent=2)}")

            # Call BGS API
            api_result = call_bgs_api(function_name, arguments)

            # Truncate for display
            result_str = json.dumps(api_result)
            if len(result_str) > 400:
                print(f"  Result: {result_str[:400]}...")
            else:
                print(f"  Result: {result_str}")

            # Add tool response
            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(api_result),
                }
            )

        # Get final response
        final_response = httpx.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL,
                "messages": messages,
                "stream": False,
            },
            timeout=120.0,
        )
        final_response.raise_for_status()
        final_result = final_response.json()
        final_answer = final_result.get("message", {}).get("content", "No response")
    else:
        final_answer = assistant_message.get("content", "No response")

    print(f"\n{'=' * 60}")
    print("Assistant Response:")
    print("=" * 60)
    print(final_answer)

    return final_answer


def simple_query(user_message: str) -> str:
    """Simple approach: fetch data first, then ask LLM to summarize."""
    print(f"\n{'=' * 60}")
    print(f"User: {user_message}")
    print("=" * 60)

    # Determine what data to fetch based on keywords
    data = None
    context = ""

    if "lithium" in user_message.lower():
        print("\nFetching lithium data from BGS API...")
        response = httpx.get(
            f"{BGS_API_URL}/production/ranking",
            params={"commodity": "lithium minerals", "top_n": 10},
            timeout=30.0,
        )
        data = response.json()
        context = f"Lithium production data (2023):\n{json.dumps(data['rankings'], indent=2)}"

    elif "cobalt" in user_message.lower():
        print("\nFetching cobalt data from BGS API...")
        response = httpx.get(
            f"{BGS_API_URL}/production/ranking",
            params={"commodity": "cobalt, mine", "top_n": 10},
            timeout=30.0,
        )
        data = response.json()
        context = f"Cobalt production data (2023):\n{json.dumps(data['rankings'], indent=2)}"

    elif "rare earth" in user_message.lower():
        print("\nFetching rare earth data from BGS API...")
        response = httpx.get(
            f"{BGS_API_URL}/production/ranking",
            params={"commodity": "rare earth minerals", "top_n": 10},
            timeout=30.0,
        )
        data = response.json()
        context = f"Rare earth production data:\n{json.dumps(data['rankings'], indent=2)}"

    elif "critical" in user_message.lower() or "available" in user_message.lower():
        print("\nFetching commodity list from BGS API...")
        response = httpx.get(
            f"{BGS_API_URL}/commodities",
            params={"critical_only": True},
            timeout=30.0,
        )
        data = response.json()
        context = f"Critical minerals available:\n{json.dumps(data['categories'], indent=2)}"

    else:
        context = "No specific mineral data requested."

    # Ask Ollama to summarize
    prompt = f"""Based on the following BGS World Mineral Statistics data, answer the user's question.

Data:
{context}

User question: {user_message}

Provide a clear, concise answer based on the data above."""

    print("\nAsking Ollama to summarize...")
    response = httpx.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        timeout=120.0,
    )
    response.raise_for_status()
    result = response.json()
    answer = result.get("message", {}).get("content", "No response")

    print(f"\n{'=' * 60}")
    print("Assistant Response:")
    print("=" * 60)
    print(answer)

    return answer


def main():
    """Run tests."""
    print("\n" + "=" * 60)
    print(f"BGS REST API + Ollama ({MODEL}) Test")
    print("=" * 60)

    # Check if Ollama is running
    try:
        response = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5.0)
        response.raise_for_status()
        print(
            f"Ollama is running with models: {[m['name'] for m in response.json().get('models', [])]}"
        )
    except (httpx.HTTPStatusError, httpx.ConnectError, ConnectionError):
        print("Error: Ollama not running. Start with: ollama serve")
        return

    # Check if BGS API is running
    try:
        response = httpx.get(f"{BGS_API_URL}/", timeout=5.0)
        response.raise_for_status()
        print("BGS API is running")
    except (httpx.HTTPStatusError, httpx.ConnectError, ConnectionError):
        print("Error: BGS API not running. Start with: uv run bgs-api")
        return

    print("\n" + "-" * 60)
    print("Testing with tool calling (if supported by model)...")
    print("-" * 60)

    queries = [
        "What are the top 5 lithium producing countries?",
        "Show me the top cobalt producers",
    ]

    # Try tool calling first
    try:
        for query in queries[:1]:  # Just one query for tool calling test
            chat_with_ollama(query)
    except Exception as e:  # noqa: BLE001
        print(f"\nTool calling failed: {e}")
        print("Falling back to simple query approach...")

    print("\n" + "-" * 60)
    print("Testing with simple query approach (always works)...")
    print("-" * 60)

    for query in queries:
        try:
            simple_query(query)
        except Exception as e:  # noqa: BLE001
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
