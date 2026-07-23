try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS
from typing import List, Dict
import httpx
import re
import asyncio


class WebSearchService:
    def __init__(self):
        pass

    async def search(self, query: str, count: int = 10) -> List[Dict]:
        results = []

        ddg_results = self._ddg_search(query, count)
        results.extend(ddg_results)

        wiki_results = await self._wikipedia_search(query, 2)
        results.extend(wiki_results)

        return results[:count]

    async def search_and_fetch(self, query: str, count: int = 8) -> List[Dict]:
        results = await self.search(query, count)

        async def _empty() -> str:
            return ""

        fetch_tasks = []
        for r in results[:4]:
            url = r.get("url", "")
            if url:
                fetch_tasks.append(self._fetch_and_extract(url))
            else:
                fetch_tasks.append(_empty())

        fetched = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        for r, content in zip(results[:4], fetched):
            if isinstance(content, str) and len(content) > 100:
                r["full_text"] = content[:3000]
            else:
                r["full_text"] = r.get("snippet", "")

        for r in results[4:]:
            r["full_text"] = r.get("snippet", "")

        return results[:count]

    def _ddg_search(self, query: str, count: int) -> List[Dict]:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=count))
                return [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                        "full_text": r.get("body", ""),
                    }
                    for r in results
                    if r.get("body")
                ]
        except Exception:
            return []

    async def _wikipedia_search(self, query: str, count: int) -> List[Dict]:
        try:
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": count,
                "format": "json",
            }
            async with httpx.AsyncClient() as client:
                resp = await client.get("https://en.wikipedia.org/w/api.php", params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    for item in data.get("query", {}).get("search", []):
                        title = item.get("title", "")
                        snippet = re.sub(r'<[^>]+>', '', item.get("snippet", ""))
                        results.append({
                            "title": title,
                            "url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                            "snippet": snippet,
                            "full_text": snippet,
                        })
                    return results
        except Exception:
            pass
        return []

    async def _fetch_and_extract(self, url: str) -> str:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=8, follow_redirects=True, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; PlagiarismChecker/1.0)"
                })
                if resp.status_code == 200:
                    return self._extract_text(resp.text)
        except Exception:
            pass
        return ""

    def _extract_text(self, html: str) -> str:
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<nav[^>]*>.*?</nav>', '', text, flags=re.DOTALL)
        text = re.sub(r'<header[^>]*>.*?</header>', '', text, flags=re.DOTALL)
        text = re.sub(r'<footer[^>]*>.*?</footer>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'&[a-zA-Z]+;', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text[:3000]
