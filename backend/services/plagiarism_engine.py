import asyncio
from typing import List, Dict
from services.similarity import SimilarityService
from services.web_search import WebSearchService
from services.academic_search import AcademicSearchService
from utils.text_processing import TextProcessor


class PlagiarismEngine:
    def __init__(self):
        self.similarity = SimilarityService()
        self.web_search = WebSearchService()
        self.academic_search = AcademicSearchService()
        self.text_processor = TextProcessor()

    async def scan_document(self, text: str) -> Dict:
        queries = self.text_processor.extract_search_queries(text)
        sentences = self.text_processor.split_sentences(text)

        web_results, academic_results = await asyncio.gather(
            self._search_web(queries),
            self._search_academic(queries),
        )

        all_matches = []

        all_matches.extend(self._score_against_sources(text, sentences, web_results, "web"))
        all_matches.extend(self._score_against_sources(text, sentences, academic_results, "academic"))

        all_matches = self._remove_subsumed(all_matches)
        all_matches.sort(key=lambda x: x["score"], reverse=True)
        all_matches = all_matches[:30]

        overall_score = self._calculate_overall_score(all_matches, len(sentences))

        return {
            "overall_score": overall_score,
            "web_matches_count": len([m for m in all_matches if m["type"] == "web"]),
            "academic_matches_count": len([m for m in all_matches if m["type"] == "academic"]),
            "matches": all_matches,
        }

    async def _search_web(self, queries: List[str]) -> List[Dict]:
        all_results = []
        unique_urls = set()

        tasks = []
        for q in queries[:6]:
            tasks.append(self.web_search.search_and_fetch(q, count=5))
        results_per_query = await asyncio.gather(*tasks, return_exceptions=True)

        for results in results_per_query:
            if isinstance(results, Exception):
                continue
            for r in results:
                url = r.get("url", "")
                if url and url not in unique_urls:
                    unique_urls.add(url)
                    all_results.append(r)

        return all_results

    async def _search_academic(self, queries: List[str]) -> List[Dict]:
        all_results = []
        unique_titles = set()

        tasks = []
        for q in queries[:4]:
            tasks.append(asyncio.gather(
                self.academic_search.search_openalex(q, limit=3),
                self.academic_search.search_arxiv(q, limit=3),
                return_exceptions=True,
            ))
        results_per_query = await asyncio.gather(*tasks, return_exceptions=True)

        for results_tuple in results_per_query:
            if isinstance(results_tuple, Exception):
                continue
            for results in results_tuple:
                if isinstance(results, Exception):
                    continue
                for r in results:
                    title = r.get("title", "")[:100].lower()
                    if title and title not in unique_titles:
                        unique_titles.add(title)
                        all_results.append(r)

        return all_results

    def _score_against_sources(
        self, full_text: str, sentences: List[Dict], sources: List[Dict], match_type: str
    ) -> List[Dict]:
        matches = []

        for source in sources:
            source_text = source.get("full_text", "") or source.get("abstract", "") or source.get("snippet", "")
            source_title = source.get("title", "")
            source_url = source.get("url", "")

            if not source_text or len(source_text) < 30:
                continue

            best_score = 0.0
            best_sentence = None
            best_source_segment = None

            for sent in sentences:
                sent_text = sent["text"]
                if len(sent_text.split()) < 5:
                    continue

                score = self.similarity.combined_score(sent_text, source_text)

                source_segments = self._find_best_segment(sent_text, source_text)
                if source_segments:
                    seg_score = self.similarity.combined_score(sent_text, source_segments)
                    score = max(score, seg_score)

                if score > best_score:
                    best_score = score
                    best_sentence = sent
                    best_source_segment = source_text[:500]

            if best_score >= 0.12 and best_sentence:
                matches.append({
                    "chunk_text": best_sentence["text"],
                    "source_text": best_source_segment or source_text[:500],
                    "source_url": source_url,
                    "source_title": source_title,
                    "score": round(min(best_score, 1.0), 4),
                    "type": match_type,
                    "start_position": best_sentence["start"],
                    "end_position": best_sentence["end"],
                })

        return matches

    def _find_best_segment(self, query: str, source: str, window: int = 50) -> str:
        source_words = source.split()
        if len(source_words) <= window:
            return source

        query_words = set(query.lower().split())
        best_score = 0.0
        best_segment = ""

        for i in range(0, len(source_words) - window + 1, window // 2):
            segment = " ".join(source_words[i:i+window])
            seg_words = set(segment.lower().split())
            overlap = len(query_words & seg_words) / max(len(query_words), 1)
            if overlap > best_score:
                best_score = overlap
                best_segment = segment

        return best_segment

    def _remove_subsumed(self, matches: List[Dict]) -> List[Dict]:
        if not matches:
            return matches

        result = []
        for m in matches:
            subsumed = False
            for existing in result:
                if (m["start_position"] >= existing["start_position"] and
                    m["end_position"] <= existing["end_position"] and
                    m["score"] <= existing["score"] * 1.1):
                    subsumed = True
                    break
                if (existing["start_position"] >= m["start_position"] and
                    existing["end_position"] <= m["end_position"] and
                    existing["score"] <= m["score"]):
                    result.remove(existing)
                    break
            if not subsumed:
                result.append(m)
        return result

    def _calculate_overall_score(self, matches: List[Dict], total_sentences: int) -> float:
        if not matches or total_sentences == 0:
            return 0.0

        covered_chars = set()
        for m in matches:
            for c in range(m["start_position"], m["end_position"]):
                covered_chars.add(c)

        coverage = len(covered_chars) / max(len("".join(m["chunk_text"] for m in matches)), 1)

        if not matches:
            return 0.0

        best_scores = {}
        for m in matches:
            key = m["chunk_text"][:60]
            if key not in best_scores or m["score"] > best_scores[key]:
                best_scores[key] = m["score"]

        avg_score = sum(best_scores.values()) / len(best_scores)
        combined = (avg_score * 0.5 + min(coverage * 2, 1.0) * 0.5) * 100

        return round(min(combined, 100.0), 2)

    def _empty_result(self) -> Dict:
        return {
            "overall_score": 0.0,
            "web_matches_count": 0,
            "academic_matches_count": 0,
            "matches": [],
        }
