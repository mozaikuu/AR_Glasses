"""
Generic MCP Web Document Retrieval Tool
"""
import sys
from pathlib import Path
import re
import datetime
from urllib.parse import quote_plus
from urllib.parse import urlparse, parse_qs, unquote
from html import unescape

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from typing import List, Dict
import requests

try:
    from bs4 import BeautifulSoup  # type: ignore
    _BS4_AVAILABLE = True
except Exception:
    BeautifulSoup = None
    _BS4_AVAILABLE = False

try:
    from duckduckgo_search import DDGS as _DDGS  # type: ignore
except Exception:
    try:
        from ddgs import DDGS as _DDGS  # type: ignore
    except Exception:
        _DDGS = None


def search_web(query: str, max_results: int = 5) -> List[Dict]:
    results = []
    if _DDGS is None:
        return [{
            "title": "",
            "url": "",
            "snippet": "Search dependency missing: install `duckduckgo_search` or `ddgs`."
        }]

    try:
        with _DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                })
    except Exception as e:
        return [{
            "title": "",
            "url": "",
            "snippet": f"Search provider error: {e}"
        }]

    return results


def _instant_answer_fallback(query: str, max_results: int = 5) -> List[Dict]:
    """
    Fallback when DDGS is unavailable/empty.
    Uses DuckDuckGo instant answer endpoint (JSON) with lightweight parsing.
    """
    results: List[Dict] = []
    url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
    headers = {"User-Agent": "SmartGlasses-Search/1.0"}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    payload = r.json() if r.content else {}

    abstract = (payload.get("AbstractText") or "").strip()
    abstract_url = (payload.get("AbstractURL") or "").strip()
    heading = (payload.get("Heading") or "").strip() or query
    if abstract:
        results.append({
            "title": heading,
            "url": abstract_url,
            "snippet": abstract,
        })

    for topic in payload.get("RelatedTopics", []):
        if len(results) >= max_results:
            break
        if isinstance(topic, dict) and "Text" in topic:
            results.append({
                "title": topic.get("FirstURL", "") or topic.get("Text", "")[:80],
                "url": topic.get("FirstURL", ""),
                "snippet": topic.get("Text", ""),
            })
        elif isinstance(topic, dict) and "Topics" in topic:
            for sub in topic.get("Topics", []):
                if len(results) >= max_results:
                    break
                if isinstance(sub, dict) and "Text" in sub:
                    results.append({
                        "title": sub.get("FirstURL", "") or sub.get("Text", "")[:80],
                        "url": sub.get("FirstURL", ""),
                        "snippet": sub.get("Text", ""),
                    })
    return results[:max_results]


def _extract_ddg_redirect_url(raw_href: str) -> str:
    href = unescape((raw_href or "").strip())
    if href.startswith("//"):
        href = "https:" + href
    parsed = urlparse(href)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        qs = parse_qs(parsed.query)
        uddg = qs.get("uddg", [])
        if uddg:
            return unquote(uddg[0])
    return href


def _ddg_lite_fallback(query: str, max_results: int = 5) -> List[Dict]:
    """
    Fallback search using DuckDuckGo Lite HTML results.
    Works even when DDGS python clients are unavailable.
    """
    url = "https://lite.duckduckgo.com/lite/"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, params={"q": query}, headers=headers, timeout=12)
    r.raise_for_status()
    html = r.text or ""

    link_pattern = re.compile(
        r'<a\s+rel="nofollow"\s+href="([^"]+)"[^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    snippet_pattern = re.compile(
        r'<td[^>]*class="result-snippet"[^>]*>(.*?)</td>',
        re.IGNORECASE | re.DOTALL,
    )

    links = list(link_pattern.finditer(html))
    snippets = [re.sub(r"<[^>]+>", " ", s).strip() for s in snippet_pattern.findall(html)]

    results: List[Dict] = []
    for idx, m in enumerate(links[:max_results]):
        raw_href = m.group(1)
        raw_title = m.group(2)
        title = re.sub(r"<[^>]+>", " ", unescape(raw_title)).strip()
        href = _extract_ddg_redirect_url(raw_href)
        snippet = snippets[idx] if idx < len(snippets) else ""
        if href:
            results.append({
                "title": title,
                "url": href,
                "snippet": snippet,
            })
    return results


def fetch_page_text(url: str, timeout: int = 10, max_chars: int = 4000) -> str:
    headers = {"User-Agent": "MCP-Web-Context/1.0"}
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()

    html = r.text or ""
    if _BS4_AVAILABLE and BeautifulSoup is not None:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = " ".join(soup.get_text(separator=" ").split())
        return text[:max_chars]

    # Fallback parser when bs4 is unavailable
    text = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = " ".join(text.split())
    return text[:max_chars]


def retrieve_web_context(query: str) -> Dict:
    documents = []
    seen = set()
    errors = []

    q = (query or "").strip().lower()
    if q in {"what day is it today", "what is today's date", "today date", "current day", "today's date"}:
        now = datetime.datetime.now().astimezone()
        date_text = f"{now.strftime('%A, %B %d, %Y')} ({now.strftime('%Y-%m-%d')})"
        return {
            "type": "documents",
            "query": query,
            "documents": [{
                "title": "Local system date",
                "url": "",
                "content": f"Today is {date_text}.",
                "snippet": f"Today is {date_text}.",
            }],
            "result_count": 1,
            "errors": [],
            "bs4_available": _BS4_AVAILABLE,
        }

    search_results = search_web(query)
    dependency_missing = (
        len(search_results) == 1
        and not search_results[0].get("url")
        and "dependency missing" in (search_results[0].get("snippet", "").lower())
    )
    if dependency_missing:
        errors.append(search_results[0].get("snippet", "search dependency missing"))
        search_results = []

    if not search_results:
        try:
            search_results = _instant_answer_fallback(query)
        except Exception as e:
            errors.append(f"instant_answer_fallback: {e}")
    if not search_results:
        try:
            search_results = _ddg_lite_fallback(query)
        except Exception as e:
            errors.append(f"ddg_lite_fallback: {e}")
    for r in search_results:
        url = r["url"]
        if not url:
            if r.get("snippet"):
                errors.append(r["snippet"])
            continue
        if url in seen:
            continue

        try:
            content = fetch_page_text(url)
            if not content and r.get("snippet"):
                content = r.get("snippet", "")
            documents.append({
                "title": r["title"],
                "url": url,
                "content": content,
                "snippet": r.get("snippet", "")
            })
            seen.add(url)
        except Exception as e:
            # Preserve result with snippet even when full fetch fails.
            documents.append({
                "title": r.get("title", ""),
                "url": url,
                "content": r.get("snippet", "") or "",
                "snippet": r.get("snippet", ""),
                "error": f"fetch_failed: {e}",
            })
            seen.add(url)
            errors.append(f"{url}: {e}")

    # Guarantee non-empty signal when search itself returned something.
    if not documents and search_results:
        for r in search_results:
            if r.get("url"):
                documents.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("snippet", ""),
                    "snippet": r.get("snippet", ""),
                })

    # Last-resort fallback: return an explicit diagnostic document.
    if not documents and errors:
        documents.append({
            "title": "Search unavailable",
            "url": "",
            "content": errors[0],
            "snippet": errors[0],
            "error": "search_unavailable",
        })

    return {
        "type": "documents",
        "query": query,
        "documents": documents,
        "result_count": len(documents),
        "errors": errors[:10],
        "bs4_available": _BS4_AVAILABLE,
    }
