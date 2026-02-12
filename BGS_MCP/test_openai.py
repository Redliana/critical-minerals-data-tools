#!/usr/bin/env python3
"""Test BGS REST API with OpenAI function calling."""

from __future__ import annotations

import json
import os

import httpx
from openai import OpenAI

# Configuration
BGS_API_URL = "http://127.0.0.1:8000"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


def get_openai_functions():
    """Fetch function definitions from BGS API."""
    response = httpx.get(f"{BGS_API_URL}/openai/functions")
    response.raise_for_status()
    return response.json()


def call_bgs_api(function_name: str, arguments: dict) -> dict:
    """Call the appropriate BGS API endpoint based on function name."""
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
            "limit": 20,
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

    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}

    response = httpx.get(f"{BGS_API_URL}{endpoint}", params=params, timeout=30.0)
    response.raise_for_status()
    return response.json()


def chat_with_tools(user_message: str) -> str:
    """Send a message to OpenAI and handle tool calls."""
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Get function definitions from BGS API
    functions = get_openai_functions()
    tools = [{"type": "function", "function": f} for f in functions]

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant with access to BGS World Mineral Statistics data. "
            "Use the available tools to answer questions about mineral production worldwide. "
            "Always provide specific data when available.",
        },
        {"role": "user", "content": user_message},
    ]

    print(f"\n{'=' * 60}")
    print(f"User: {user_message}")
    print("=" * 60)

    # First API call
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    assistant_message = response.choices[0].message

    # Check if the model wants to call tools
    if assistant_message.tool_calls:
        print(f"\nOpenAI requested {len(assistant_message.tool_calls)} tool call(s):")

        # Process each tool call
        messages.append(assistant_message)

        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            print(f"\n  Tool: {function_name}")
            print(f"  Args: {json.dumps(arguments, indent=2)}")

            # Call the BGS API
            result = call_bgs_api(function_name, arguments)

            # Truncate large results for display
            result_str = json.dumps(result)
            if len(result_str) > 500:
                print(f"  Result: {result_str[:500]}...")
            else:
                print(f"  Result: {result_str}")

            # Add tool result to messages
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )

        # Get final response with tool results
        final_response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )

        final_answer = final_response.choices[0].message.content
    else:
        final_answer = assistant_message.content

    print(f"\n{'=' * 60}")
    print("Assistant Response:")
    print("=" * 60)
    print(final_answer)

    return final_answer


def main():
    """Run test queries."""
    print("\n" + "=" * 60)
    print("BGS REST API + OpenAI Function Calling Test")
    print("=" * 60)

    # Test queries
    queries = [
        "What are the top 5 lithium producing countries?",
        "Compare cobalt production between DRC, Australia, and Russia",
        "What critical minerals are available in the database?",
    ]

    for query in queries:
        try:
            chat_with_tools(query)
        except Exception as e:  # noqa: BLE001
            print(f"Error: {e}")
        print("\n")


if __name__ == "__main__":
    main()
