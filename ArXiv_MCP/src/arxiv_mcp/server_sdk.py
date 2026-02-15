"""
ArXiv MCP Server with LLM Integration (Using Official SDKs)

This is an alternative implementation that uses the official OpenAI and Anthropic
Python SDKs instead of direct API calls. This approach is often cleaner and
provides better error handling and type safety.

Author: MCP Tutorial
License: MIT
"""

from __future__ import annotations

import logging
import os
import xml.etree.ElementTree as ET
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# Import LLM SDKs
try:
    import openai
    from openai import OpenAI

    OpenAIAPIError = openai.APIError
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAIAPIError = Exception  # type: ignore[assignment,misc]
    OPENAI_AVAILABLE = False

try:
    import anthropic
    from anthropic import Anthropic

    AnthropicAPIError = anthropic.APIError
    ANTHROPIC_AVAILABLE = True
except ImportError:
    AnthropicAPIError = Exception  # type: ignore[assignment,misc]
    ANTHROPIC_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("arxiv-search-sdk")

# Constants
ARXIV_API_BASE = "https://export.arxiv.org/api/query"
ARXIV_NAMESPACE = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
USER_AGENT = "arxiv-mcp-server/1.0"

# Initialize LLM clients
openai_client = None
anthropic_client = None

if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    logger.info("OpenAI client initialized")

if ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
    anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    logger.info("Anthropic client initialized")


async def make_arxiv_request(url: str) -> str | None:
    """Make a request to the ArXiv API."""
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Making request to ArXiv API: {url}")
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            logger.error(f"Error occurred: {e}")
            return None


def parse_arxiv_entry(entry: ET.Element) -> dict[str, Any]:
    """Parse a single ArXiv entry from the Atom feed."""
    title = entry.find("atom:title", ARXIV_NAMESPACE)
    title_text = title.text.strip().replace("\n", " ") if title is not None else "Unknown"

    entry_id = entry.find("atom:id", ARXIV_NAMESPACE)
    arxiv_id = entry_id.text.split("/abs/")[-1] if entry_id is not None else "Unknown"

    authors = []
    for author in entry.findall("atom:author", ARXIV_NAMESPACE):
        name = author.find("atom:name", ARXIV_NAMESPACE)
        if name is not None:
            authors.append(name.text)

    summary = entry.find("atom:summary", ARXIV_NAMESPACE)
    summary_text = summary.text.strip().replace("\n", " ") if summary is not None else ""

    published = entry.find("atom:published", ARXIV_NAMESPACE)
    published_date = published.text if published is not None else "Unknown"

    categories = []
    for category in entry.findall("atom:category", ARXIV_NAMESPACE):
        term = category.get("term")
        if term:
            categories.append(term)

    pdf_link = None
    for link in entry.findall("atom:link", ARXIV_NAMESPACE):
        if link.get("title") == "pdf":
            pdf_link = link.get("href")
            break

    return {
        "id": arxiv_id,
        "title": title_text,
        "authors": authors,
        "summary": summary_text,
        "published": published_date,
        "categories": categories,
        "pdf_url": pdf_link or f"http://arxiv.org/pdf/{arxiv_id}.pdf",
    }


def summarize_with_openai_sdk(paper_info: str, model: str = "gpt-4") -> str | None:
    """
    Generate a summary using the OpenAI SDK.

    This uses the official OpenAI Python SDK which provides better error handling,
    automatic retries, and type safety compared to direct API calls.
    """
    if not openai_client:
        return None

    try:
        prompt = f"""Please provide a concise summary of the following research paper. 
Focus on:
1. The main research question or problem
2. The key methodology or approach
3. The main findings or contributions
4. The significance of the work

Paper details:
{paper_info}

Please provide a clear, structured summary in 3-4 paragraphs."""

        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful research assistant that summarizes academic papers clearly and concisely.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1000,
        )

        return response.choices[0].message.content

    except (OpenAIAPIError, KeyError, ValueError) as e:
        logger.error(f"OpenAI SDK error: {e}")
        return None


def summarize_with_anthropic_sdk(
    paper_info: str, model: str = "claude-3-5-sonnet-20241022"
) -> str | None:
    """
    Generate a summary using the Anthropic SDK.

    This uses the official Anthropic Python SDK for Claude API access.
    """
    if not anthropic_client:
        return None

    try:
        prompt = f"""Please provide a concise summary of the following research paper. 
Focus on:
1. The main research question or problem
2. The key methodology or approach
3. The main findings or contributions
4. The significance of the work

Paper details:
{paper_info}

Please provide a clear, structured summary in 3-4 paragraphs."""

        message = anthropic_client.messages.create(
            model=model, max_tokens=1000, messages=[{"role": "user", "content": prompt}]
        )

        return message.content[0].text

    except (AnthropicAPIError, KeyError, ValueError) as e:
        logger.error(f"Anthropic SDK error: {e}")
        return None


@mcp.tool()
async def search_arxiv(query: str, max_results: int = 10, sort_by: str = "relevance") -> str:
    """
    Search ArXiv for papers matching a query.

    Args:
        query: Search query string (supports field prefixes like "ti:", "au:", "abs:")
        max_results: Maximum number of results (default: 10, max: 100)
        sort_by: Sort order - "relevance", "lastUpdatedDate", or "submittedDate"

    Returns:
        Formatted string with paper metadata
    """
    max_results = min(max_results, 100)

    valid_sort_options = ["relevance", "lastUpdatedDate", "submittedDate"]
    if sort_by not in valid_sort_options:
        sort_by = "relevance"

    params = {
        "search_query": f"all:{query}" if ":" not in query else query,
        "start": 0,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": "descending",
    }

    param_str = "&".join([f"{k}={v}" for k, v in params.items()])
    url = f"{ARXIV_API_BASE}?{param_str}"

    xml_response = await make_arxiv_request(url)
    if not xml_response:
        return "Error: Failed to fetch results from ArXiv API."

    try:
        root = ET.fromstring(xml_response)
        entries = root.findall("atom:entry", ARXIV_NAMESPACE)

        if not entries:
            return f"No papers found matching query: '{query}'"

        papers = [parse_arxiv_entry(entry) for entry in entries]

        result_lines = [f"Found {len(papers)} papers matching '{query}':\n"]
        result_lines.append("=" * 80)

        for i, paper in enumerate(papers, 1):
            authors_str = ", ".join(paper["authors"][:3])
            if len(paper["authors"]) > 3:
                authors_str += " et al."

            result_lines.append(f"""
{i}. Title: {paper["title"]}
   ArXiv ID: {paper["id"]}
   Authors: {authors_str}
   Published: {paper["published"]}
   PDF: {paper["pdf_url"]}
   Abstract: {paper["summary"][:200]}...
""")
            result_lines.append("-" * 80)

        return "\n".join(result_lines)

    except (ET.ParseError, ValueError, KeyError, AttributeError) as e:
        logger.error(f"Error processing results: {e}")
        return "Error: Failed to parse ArXiv API response."


@mcp.tool()
async def get_paper_details(arxiv_id: str) -> str:
    """
    Get detailed information about a specific ArXiv paper.

    Args:
        arxiv_id: The ArXiv ID (e.g., "2301.07041")

    Returns:
        Detailed paper information including full abstract
    """
    clean_id = arxiv_id.split("v")[0]
    url = f"{ARXIV_API_BASE}?id_list={clean_id}"

    xml_response = await make_arxiv_request(url)
    if not xml_response:
        return f"Error: Failed to fetch paper {arxiv_id}"

    try:
        root = ET.fromstring(xml_response)
        entries = root.findall("atom:entry", ARXIV_NAMESPACE)

        if not entries:
            return f"Paper not found: {arxiv_id}"

        paper = parse_arxiv_entry(entries[0])
        authors_str = ", ".join(paper["authors"])

        return f"""
Title: {paper["title"]}
ArXiv ID: {paper["id"]}
Authors: {authors_str}
Published: {paper["published"]}
Categories: {", ".join(paper["categories"])}
PDF: {paper["pdf_url"]}

Abstract:
{paper["summary"]}
"""

    except (ET.ParseError, ValueError, KeyError, AttributeError) as e:
        logger.error(f"Error: {e}")
        return f"Error: Failed to retrieve paper {arxiv_id}"


@mcp.tool()
async def summarize_paper(arxiv_id: str, llm_provider: str = "openai", model: str = "auto") -> str:
    """
    Summarize an ArXiv paper using a commercial LLM (via official SDKs).

    Args:
        arxiv_id: The ArXiv ID to summarize
        llm_provider: "openai" or "anthropic"
        model: Specific model or "auto" for default

    Returns:
        LLM-generated summary of the paper
    """
    paper_info = await get_paper_details(arxiv_id)

    if paper_info.startswith("Error:") or paper_info.startswith("Paper not found:"):
        return paper_info

    summary = None

    if llm_provider.lower() == "openai":
        if model == "auto":
            model = "gpt-4"
        summary = summarize_with_openai_sdk(paper_info, model)
    elif llm_provider.lower() == "anthropic":
        if model == "auto":
            model = "claude-3-5-sonnet-20241022"
        summary = summarize_with_anthropic_sdk(paper_info, model)
    else:
        return f"Error: Unknown provider '{llm_provider}'"

    if not summary:
        return f"Error: Failed to generate summary. Check that {llm_provider} SDK is installed and API key is set."

    return f"""
Summary of ArXiv Paper: {arxiv_id}
Generated using: {llm_provider} ({model})

{summary}

---
Original paper: http://arxiv.org/abs/{arxiv_id}
"""


def main():
    """Main entry point."""
    logger.info("Starting ArXiv MCP Server (SDK version)...")
    logger.info(f"OpenAI SDK available: {OPENAI_AVAILABLE}")
    logger.info(f"Anthropic SDK available: {ANTHROPIC_AVAILABLE}")
    logger.info(f"OpenAI client initialized: {openai_client is not None}")
    logger.info(f"Anthropic client initialized: {anthropic_client is not None}")

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
