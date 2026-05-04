"""Single URL browser tool for ARC parts."""
import os
import sys
import re
import time
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

# Allow `python tools/search/browse.py "url"` from ARC root.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.cost.cost_log import log_call


def browse(url: str, timeout: int = 10) -> dict:
    """
    Fetch and parse a single URL.

    Args:
        url: Full URL to fetch
        timeout: Request timeout in seconds (default: 10)

    Returns:
        Dict with keys: url, title, text, links

    Raises:
        ValueError: If URL is invalid or Instagram URL detected
        requests.RequestException: On network or HTTP errors
    """
    # Validate URL
    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            url = "https://" + url
        if not parsed.netloc and not url.startswith("https://"):
            url = "https://" + url
    except Exception as e:
        raise ValueError(f"Invalid URL: {e}")

    # Check for Instagram — delegate to specialized tool
    if "instagram.com" in url.lower():
        raise ValueError(
            "Instagram URLs require specialized handler. "
            "Use utils/insta_browse.py instead."
        )

    # Fetch page
    t0 = time.time()
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

    except requests.exceptions.Timeout:
        raise requests.RequestException(f"Request to {url} timed out after {timeout}s")
    except requests.exceptions.ConnectionError as e:
        raise requests.RequestException(f"Connection error: {e}")
    except requests.exceptions.HTTPError as e:
        status = response.status_code
        if status in (404, 410):
            raise requests.RequestException(f"URL not found: {status}")
        elif status in (401, 403):
            raise requests.RequestException(f"Access denied: {status}")
        else:
            raise requests.RequestException(f"HTTP {status}: {e}")

    # Parse HTML
    try:
        soup = BeautifulSoup(response.content, "html.parser")
    except Exception as e:
        raise ValueError(f"Parse error: {e}")

    # Extract title
    title = (soup.title.string if soup.title else "") or ""
    if not title:
        og_title = soup.find("meta", property="og:title")
        title = og_title.get("content", "") if og_title else ""

    # Extract main text (remove scripts, styles)
    for script in soup(["script", "style"]):
        script.decompose()

    text = soup.get_text(separator=" ", strip=True)
    # Clean up whitespace
    text = re.sub(r"\s+", " ", text)[:5000]  # Truncate to 5000 chars

    # Extract links
    links = []
    for a in soup.find_all("a", href=True)[:20]:
        href = a.get("href", "").strip()
        if href and not href.startswith(("#", "javascript://")):
            if href.startswith("/"):
                parsed = urlparse(url)
                href = f"{parsed.scheme}://{parsed.netloc}{href}"
            elif not href.startswith("http"):
                href = url.rstrip("/") + "/" + href.lstrip("/")
            links.append({"text": a.get_text(strip=True)[:50], "url": href})

    log_call(
        tool="browse",
        model="browse:http",
        metadata={
            "url": url[:300],
            "final_url": response.url[:300],
            "status_code": response.status_code,
            "duration_ms": int((time.time() - t0) * 1000),
            "link_count": len(links),
            "text_chars": len(text),
        },
    )
    return {"url": response.url, "title": title, "text": text, "links": links}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python browse.py '<url>'")
        sys.exit(1)

    url = sys.argv[1]

    try:
        result = browse(url)
        import json
        print(json.dumps(result, indent=2))
    except (ValueError, requests.RequestException) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
