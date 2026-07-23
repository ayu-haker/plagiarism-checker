import httpx
from typing import List, Dict
import xml.etree.ElementTree as ET


class AcademicSearchService:
    def __init__(self):
        self.openalex_url = "https://api.openalex.org/works"
        self.arxiv_url = "http://export.arxiv.org/api/query"

    async def search_semantic_scholar(self, query: str, limit: int = 5) -> List[Dict]:
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,abstract,url,externalIds",
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.semanticscholar.org/graph/v1/paper/search",
                    params=params,
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return [
                        {
                            "title": p.get("title", ""),
                            "abstract": p.get("abstract", ""),
                            "url": p.get("url", ""),
                        }
                        for p in data.get("data", [])
                        if p.get("abstract")
                    ]
        except Exception:
            pass
        return []

    async def search_crossref(self, query: str, limit: int = 5) -> List[Dict]:
        params = {"query": query, "rows": limit}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.crossref.org/works", params=params, timeout=15
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return [
                        {
                            "title": " ".join(item.get("title", [""])),
                            "url": item.get("URL", ""),
                            "abstract": item.get("abstract", ""),
                        }
                        for item in data.get("message", {}).get("items", [])
                        if item.get("abstract")
                    ]
        except Exception:
            pass
        return []

    async def search_openalex(self, query: str, limit: int = 5) -> List[Dict]:
        params = {
            "search": query,
            "per_page": limit,
            "select": "title,doi,open_access,abstract_inverted_index",
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.openalex_url, params=params, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    for work in data.get("results", []):
                        abstract = self._reconstruct_abstract(
                            work.get("abstract_inverted_index", {})
                        )
                        if abstract:
                            results.append({
                                "title": work.get("title", ""),
                                "url": work.get("doi", ""),
                                "abstract": abstract,
                            })
                    return results
        except Exception:
            pass
        return []

    async def search_arxiv(self, query: str, limit: int = 5) -> List[Dict]:
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": limit,
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.arxiv_url, params=params, timeout=15)
                if resp.status_code == 200:
                    return self._parse_arxiv_xml(resp.text)
        except Exception:
            pass
        return []

    def _parse_arxiv_xml(self, xml_text: str) -> List[Dict]:
        results = []
        try:
            root = ET.fromstring(xml_text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns):
                title = entry.findtext("atom:title", "", ns).strip().replace("\n", " ")
                summary = entry.findtext("atom:summary", "", ns).strip().replace("\n", " ")
                link = ""
                for l in entry.findall("atom:link", ns):
                    if l.get("type") == "text/html":
                        link = l.get("href", "")
                        break
                if not link:
                    id_text = entry.findtext("atom:id", "", ns)
                    link = id_text if id_text else ""
                if title and summary:
                    results.append({"title": title, "url": link, "abstract": summary})
        except Exception:
            pass
        return results

    def _reconstruct_abstract(self, inverted_index: dict) -> str:
        if not inverted_index:
            return ""
        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
        word_positions.sort(key=lambda x: x[0])
        return " ".join(w for _, w in word_positions)
