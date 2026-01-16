"""
Generic MCP Web Document Retrieval Tool
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS


def search_web(query: str, max_results: int = 5) -> List[Dict]:
    results = []

    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", "")
            })

    return results


def fetch_page_text(url: str, timeout: int = 10, max_chars: int = 4000) -> str:
    headers = {"User-Agent": "MCP-Web-Context/1.0"}
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = " ".join(soup.get_text(separator=" ").split())
    return text[:max_chars]


def retrieve_web_context(query: str) -> Dict:
    documents = []
    seen = set()

    for r in search_web(query):
        url = r["url"]
        if not url or url in seen:
            continue

        try:
            documents.append({
                "title": r["title"],
                "url": url,
                "content": fetch_page_text(url)
            })
            seen.add(url)
        except Exception:
            continue

    return {
        "type": "documents",
        "query": query,
        "documents": documents
    }

