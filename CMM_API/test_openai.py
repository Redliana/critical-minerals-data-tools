"""Test CMM API with OpenAI function calling."""

from __future__ import annotations

import json
import os

import httpx
from openai import OpenAI

API_BASE = "http://127.0.0.1:8000"

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def get_functions():
    """Fetch function definitions from CMM API."""
    resp = httpx.get(f"{API_BASE}/openai/functions")
    return resp.json()["functions"]


def call_api(function_name: str, arguments: dict) -> dict:
    """Call the CMM API based on function name."""
    endpoints = {
        "search_all_sources": (
            "/search",
            {
                "q": arguments.get("query"),
                "sources": arguments.get("sources", "CLAIMM,BGS"),
                "limit": arguments.get("limit", 20),
            },
        ),
        "get_bgs_production": ("/bgs/production", arguments),
        "get_commodity_ranking": (
            f"/bgs/ranking/{arguments.get('commodity', '')}",
            {"year": arguments.get("year"), "top_n": arguments.get("top_n", 15)},
        ),
        "search_claimm_datasets": (
            "/claimm/datasets",
            {
                "q": arguments.get("query"),
                "tags": arguments.get("tags"),
                "limit": arguments.get("limit", 20),
            },
        ),
        "get_claimm_dataset_details": (f"/claimm/datasets/{arguments.get('dataset_id', '')}", {}),
        "list_bgs_commodities": (
            "/bgs/commodities",
            {"critical_only": arguments.get("critical_only", False)},
        ),
        "get_data_overview": ("/overview", {}),
    }

    if function_name not in endpoints:
        return {"error": f"Unknown function: {function_name}"}

    endpoint, params = endpoints[function_name]
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}

    resp = httpx.get(f"{API_BASE}{endpoint}", params=params, timeout=60.0)
    return resp.json()


def ask_cmm(question: str) -> str:
    """Ask a question using OpenAI with CMM API tools."""
    functions = get_functions()

    messages = [
        {
            "role": "system",
            "content": "You are a critical minerals analyst. Use the available tools to answer questions about mineral production, supply chains, and datasets. Be concise.",
        },
        {"role": "user", "content": question},
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=[{"type": "function", "function": f} for f in functions],
        tool_choice="auto",
    )

    msg = response.choices[0].message

    # Handle tool calls
    while msg.tool_calls:
        messages.append(msg)

        for tool_call in msg.tool_calls:
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)

            print(f"  → Calling {func_name}({func_args})")
            result = call_api(func_name, func_args)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)[:8000],  # Truncate large responses
                }
            )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=[{"type": "function", "function": f} for f in functions],
            tool_choice="auto",
        )
        msg = response.choices[0].message

    return msg.content


def main():
    print("=" * 60)
    print("CMM API + OpenAI Integration Test")
    print("=" * 60)

    questions = [
        "What data sources are available and what do they contain?",
        "Who are the top 5 lithium producing countries?",
        "Search for rare earth datasets in CLAIMM",
        "Compare cobalt production - which countries dominate?",
    ]

    for i, q in enumerate(questions, 1):
        print(f"\n[{i}] {q}")
        print("-" * 50)
        try:
            answer = ask_cmm(q)
            print(f"\n{answer}")
        except Exception as e:
            print(f"Error: {e}")
        print()


if __name__ == "__main__":
    main()
