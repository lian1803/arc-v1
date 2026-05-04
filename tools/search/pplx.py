"""Web search tool powered by Perplexity API."""
import os
import sys
import json
import time
from pathlib import Path

import requests

# Allow `python tools/search/pplx.py "query"` from ARC root.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.cost.cost_log import log_call


def search(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the web using Perplexity API.

    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 5)

    Returns:
        List of dicts with keys: title, url, snippet

    Raises:
        ValueError: If PERPLEXITY_API_KEY is not set
        requests.RequestException: On network or API errors
        requests.HTTPError: On 4xx/5xx responses
    """
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise ValueError(
            "PERPLEXITY_API_KEY not found in environment. "
            "Set it in .env or as environment variable."
        )

    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Search for: {query}\n\n"
                    f"Return results as JSON array with fields: title, url, snippet. "
                    f"Maximum {max_results} results. JSON only, no markdown."
                ),
            }
        ],
    }

    t0 = time.time()
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise requests.RequestException("Perplexity API request timed out")
    except requests.exceptions.ConnectionError as e:
        raise requests.RequestException(f"Connection error: {e}")
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            raise requests.RequestException("Perplexity API rate limit exceeded")
        elif response.status_code in (401, 403):
            raise requests.RequestException("Perplexity API authentication failed")
        else:
            raise requests.RequestException(f"HTTP {response.status_code}: {e}")

    try:
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Try to extract JSON from response
        results = json.loads(content)
        if not isinstance(results, list):
            results = [results]

        # Validate schema
        for result in results[:max_results]:
            if not all(k in result for k in ["title", "url", "snippet"]):
                raise ValueError("Invalid result schema")

        log_call(
            tool="search",
            model="perplexity:sonar-pro",
            metadata={
                "query": query[:200],
                "max_results": max_results,
                "result_count": len(results[:max_results]),
                "duration_ms": int((time.time() - t0) * 1000),
                "status_code": response.status_code,
            },
        )
        return results[:max_results]

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse Perplexity response as JSON: {e}")
    except (KeyError, TypeError) as e:
        raise ValueError(f"Unexpected API response structure: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python search.py '<query>'")
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    try:
        results = search(query)
        print(json.dumps(results, indent=2))
    except (ValueError, requests.RequestException) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
