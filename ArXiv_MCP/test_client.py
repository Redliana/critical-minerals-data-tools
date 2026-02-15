"""
Simple Test Client for ArXiv MCP Server

This script demonstrates how to test the ArXiv MCP server locally
using the MCP Inspector or a simple client.
"""

from __future__ import annotations

import asyncio
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_arxiv_server():
    """
    Test the ArXiv MCP server by connecting to it and calling tools.
    """
    # Server parameters - adjust path as needed
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "arxiv-mcp"],
        env=os.environ.copy(),  # Inherit environment variables from shell
    )

    print("Connecting to ArXiv MCP Server...")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            print("✓ Connected to server\n")

            # list available tools
            print("Available tools:")
            tools_result = await session.list_tools()
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")
            print()

            # Test 1: Search ArXiv
            print("=" * 80)
            print("Test 1: Searching ArXiv for 'transformer attention'...")
            print("=" * 80)

            search_result = await session.call_tool(
                "search_arxiv",
                arguments={
                    "query": "transformer attention",
                    "max_results": 3,
                    "sort_by": "relevance",
                },
            )

            print(search_result.content[0].text)
            print()

            # Test 2: Get specific paper
            print("=" * 80)
            print("Test 2: Getting details for paper 1706.03762 (Attention Is All You Need)...")
            print("=" * 80)

            paper_result = await session.call_tool(
                "get_arxiv_paper", arguments={"arxiv_id": "1706.03762"}
            )

            print(paper_result.content[0].text)
            print()

            # Test 3: Summarize with LLM (if API key is set)
            print("=" * 80)
            print("Test 3: Summarizing paper with LLM...")
            print("=" * 80)
            print("Note: This requires OPENAI_API_KEY or ANTHROPIC_API_KEY to be set")

            try:
                summary_result = await session.call_tool(
                    "summarize_paper_with_llm",
                    arguments={"arxiv_id": "1706.03762", "llm_provider": "openai"},
                )
                print(summary_result.content[0].text)
            except Exception as e:
                print(f"Error: {e}")
                print("Make sure your API keys are set in environment variables")

            print()
            print("=" * 80)
            print("Tests completed!")
            print("=" * 80)


async def main():
    """Main entry point."""
    try:
        await test_arxiv_server()
    except Exception as e:
        print(f"Error running tests: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
