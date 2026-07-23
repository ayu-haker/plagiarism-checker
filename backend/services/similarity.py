import math
import re
from collections import Counter
from typing import List, Dict, Tuple


class SimilarityService:
    def __init__(self):
        pass

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\b\w+\b', text.lower())

    def _char_ngrams(self, text: str, n: int = 3) -> List[str]:
        text = re.sub(r'\s+', ' ', text.lower().strip())
        return [text[i:i+n] for i in range(max(0, len(text) - n + 1))]

    def _word_ngrams(self, text: str, n: int = 3) -> List[Tuple[str, ...]]:
        words = self._tokenize(text)
        return [tuple(words[i:i+n]) for i in range(max(0, len(words) - n + 1))]

    def tfidf_similarity(self, text1: str, text2: str) -> float:
        tokens1 = self._tokenize(text1)
        tokens2 = self._tokenize(text2)
        if not tokens1 or not tokens2:
            return 0.0

        all_tokens = [tokens1, tokens2]
        n = len(all_tokens)
        doc_freq = Counter()
        for tokens in all_tokens:
            for w in set(tokens):
                doc_freq[w] += 1

        idf = {w: math.log((n + 1) / (f + 1)) + 1 for w, f in doc_freq.items()}

        def make_vec(tokens):
            tf = Counter(tokens)
            total = len(tokens)
            return {w: (c / total) * idf.get(w, 1.0) for w, c in tf.items()}

        v1 = make_vec(tokens1)
        v2 = make_vec(tokens2)

        common = set(v1.keys()) & set(v2.keys())
        dot = sum(v1[w] * v2[w] for w in common)
        n1 = math.sqrt(sum(x**2 for x in v1.values())) or 1.0
        n2 = math.sqrt(sum(x**2 for x in v2.values())) or 1.0
        return dot / (n1 * n2)

    def char_ngram_similarity(self, text1: str, text2: str, n: int = 3) -> float:
        ng1 = Counter(self._char_ngrams(text1, n))
        ng2 = Counter(self._char_ngrams(text2, n))
        if not ng1 or not ng2:
            return 0.0
        common = set(ng1.keys()) & set(ng2.keys())
        dot = sum(ng1[g] * ng2[g] for g in common)
        n1 = math.sqrt(sum(v**2 for v in ng1.values())) or 1.0
        n2 = math.sqrt(sum(v**2 for v in ng2.values())) or 1.0
        return dot / (n1 * n2)

    def word_ngram_overlap(self, text1: str, text2: str, n: int = 3) -> float:
        ng1 = set(self._word_ngrams(text1, n))
        ng2 = set(self._word_ngrams(text2, n))
        if not ng1 or not ng2:
            return 0.0
        return len(ng1 & ng2) / len(ng1 | ng2)

    def exact_phrase_score(self, text1: str, text2: str) -> float:
        words1 = self._tokenize(text1)
        words2 = self._tokenize(text2)
        if not words1 or not words2:
            return 0.0

        max_phrase = 0
        for length in range(min(len(words1), len(words2), 15), 2, -1):
            for i in range(len(words1) - length + 1):
                phrase = tuple(words1[i:i+length])
                text2_str = " ".join(words2)
                phrase_str = " ".join(phrase)
                if phrase_str in text2_str:
                    max_phrase = max(max_phrase, length)

        shorter = min(len(words1), len(words2))
        return max_phrase / shorter if shorter > 0 else 0.0

    def combined_score(self, text1: str, text2: str) -> float:
        if not text1.strip() or not text2.strip():
            return 0.0

        tfidf = self.tfidf_similarity(text1, text2)
        char_ng = self.char_ngram_similarity(text1, text2, 3)
        char_ng5 = self.char_ngram_similarity(text1, text2, 5)
        word_ng = self.word_ngram_overlap(text1, text2, 2)
        exact = self.exact_phrase_score(text1, text2)

        combined = (
            tfidf * 0.20 +
            char_ng * 0.15 +
            char_ng5 * 0.15 +
            word_ng * 0.25 +
            exact * 0.25
        )

        return min(combined, 1.0)

    def compute_jaccard(self, text1: str, text2: str, n: int = 3) -> float:
        words1 = text1.lower().split()
        words2 = text2.lower().split()
        ngrams1 = set(tuple(words1[i:i+n]) for i in range(max(0, len(words1) - n + 1)))
        ngrams2 = set(tuple(words2[i:i+n]) for i in range(max(0, len(words2) - n + 1)))
        if not ngrams1 or not ngrams2:
            return 0.0
        return len(ngrams1 & ngrams2) / len(ngrams1 | ngrams2)

    def find_best_matches(
        self, query_chunks: List[str], source_chunks: List[str], threshold: float = 0.15
    ) -> List[Tuple[int, int, float]]:
        results = []
        for i, qc in enumerate(query_chunks):
            for j, sc in enumerate(source_chunks):
                score = self.combined_score(qc, sc)
                if score >= threshold:
                    results.append((i, j, score))
        results.sort(key=lambda x: x[2], reverse=True)
        return results
