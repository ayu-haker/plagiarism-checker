import re
from typing import List, Dict


class TextProcessor:
    def __init__(self):
        pass

    def chunk_text(self, text: str, chunk_size: int = 240, overlap: int = 60) -> List[Dict]:
        words = text.split()
        chunks = []
        start = 0
        idx = 0

        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)
            char_start = len(" ".join(words[:start]))
            char_end = len(" ".join(words[:end]))

            chunks.append({
                "text": chunk_text,
                "word_start": start,
                "word_end": end,
                "char_start": char_start,
                "char_end": char_end,
                "index": idx,
            })
            start += chunk_size - overlap
            idx += 1

        return chunks

    def split_sentences(self, text: str) -> List[Dict]:
        raw_sents = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = []
        offset = 0
        for s in raw_sents:
            s = s.strip()
            if s:
                sentences.append({
                    "text": s,
                    "start": offset,
                    "end": offset + len(s),
                })
            offset += len(s) + 1
        return sentences

    def extract_search_queries(self, text: str) -> List[str]:
        sentences = self.split_sentences(text)
        queries = []

        for sent in sentences:
            words = sent["text"].split()
            if len(words) >= 8:
                queries.append(" ".join(words[:15]))
            if len(words) >= 15:
                queries.append(" ".join(words[5:20]))

        paragraphs = re.split(r'\n\s*\n', text)
        for para in paragraphs:
            words = para.split()
            if len(words) >= 20:
                queries.append(" ".join(words[:12]))
            if len(words) >= 30:
                queries.append(" ".join(words[10:25]))

        words = text.split()
        if len(words) >= 10:
            queries.append(" ".join(words[:10]))
        if len(words) >= 20:
            queries.append(" ".join(words[:15]))
        if len(words) >= 30:
            queries.append(" ".join(words[10:25]))

        seen = set()
        unique = []
        for q in queries:
            key = q.lower().strip()
            if key not in seen and len(key.split()) >= 5:
                seen.add(key)
                unique.append(q)

        return unique[:10]

    def normalize(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
