import re
import random
from typing import Dict, List, Tuple


class HumanizerService:
    def __init__(self):
        self.synonyms = {
            "demonstrated": ["exhibited", "displayed", "shown", "manifested", "evidenced"],
            "transformative": ["revolutionary", "groundbreaking", "innovative", "significant", "profound"],
            "comprehensive": ["thorough", "extensive", "complete", "all-encompassing", "wide-ranging"],
            "facilitate": ["enable", "support", "assist", "aid", "promote"],
            "subsequently": ["then", "afterward", "later", "thereafter", "following this"],
            "approximately": ["roughly", "about", "around", "nearly", "close to"],
            "utilize": ["use", "employ", "apply", "leverage", "make use of"],
            "demonstrate": ["show", "illustrate", "prove", "indicate", "reveal"],
            "implement": ["carry out", "execute", "apply", "put in place", "establish"],
            "endeavor": ["attempt", "try", "strive", "make an effort"],
            "regarding": ["about", "concerning", "pertaining to", "in relation to", "with respect to"],
            "additionally": ["also", "further", "moreover", "in addition", "besides"],
            "furthermore": ["moreover", "also", "in addition", "beyond that", "what's more"],
            "nevertheless": ["however", "still", "yet", "all the same", "even so"],
            "consequently": ["therefore", "as a result", "thus", "so", "hence"],
            "moreover": ["also", "furthermore", "in addition", "besides", "on top of that"],
            "significant": ["important", "notable", "considerable", "substantial", "meaningful"],
            "numerous": ["many", "several", "various", "countless", "a number of"],

            "prior to": ["before"],
            "in order to": ["to"],
            "it is important to note that": [""],
            "it should be noted that": [""],
            "it is worth noting that": [""],
            "due to the fact that": ["because"],
            "in spite of the fact that": ["although", "even though"],
            "for the purpose of": ["to", "for"],
            "at the present time": ["now", "currently"],
            "in the near future": ["soon"],
            "on a regular basis": ["regularly", "often", "frequently"],
            "in the majority of cases": ["usually", "in most cases", "generally"],
            "with regard to": ["about", "regarding", "concerning"],
            "in terms of": ["for", "regarding", "concerning"],
            "has the ability to": ["can"],
            "is able to": ["can"],
            "in contemporary society": ["today", "in today's world"],
            "in modern times": ["nowadays", "today", "currently"],
            "plays a vital role": ["is important", "is essential", "is crucial"],
            "plays a crucial role": ["is key", "is essential", "matters greatly"],
            "shed light on": ["explain", "clarify", "illuminate", "elucidate"],
            "give rise to": ["cause", "lead to", "result in", "produce"],
            "take into consideration": ["consider"],
            "bring about": ["cause", "create", "produce", "lead to"],
            "in conclusion": ["to sum up", "overall", "finally", "ultimately"],
            "to sum up": ["overall", "in short", "briefly"],
            "a large number of": ["many", "numerous"],
            "a significant amount of": ["a lot of", "much", "considerable"],
            "at this point in time": ["now", "currently"],
        }

        self.sentence_starters = [
            "Notably, ", "It is worth mentioning that ", "In particular, ",
            "Specifically, ", "In this context, ", "From this perspective, ",
            "This means that ", "In effect, ", "As a result, ",
            "Essentially, ", "Put differently, ", "In other words, ",
        ]

        self.passive_patterns = [
            (r'(\w+)\s+(is|are|was|were)\s+(\w+ed)\s+by\s+(.+)', r'\4 \2 \3 \1'),
        ]

    def humanize(self, text: str, mode: str = "standard") -> Dict:
        paragraphs = self._split_paragraphs(text)
        humanized_paragraphs = []

        for para in paragraphs:
            sentences = self._split_sentences(para)
            humanized_sentences = []

            for sent in sentences:
                if mode == "light":
                    humanized_sentences.append(self._light_edit(sent))
                elif mode == "aggressive":
                    humanized_sentences.append(self._aggressive_edit(sent))
                else:
                    humanized_sentences.append(self._standard_edit(sent))

            humanized_paragraphs.append(" ".join(humanized_sentences))

        result_text = "\n\n".join(humanized_paragraphs)
        meaning_score = self._verify_meaning(text, result_text)

        if meaning_score < 0.45:
            result_text = self._fallback_humanize(text)
            meaning_score = self._verify_meaning(text, result_text)

        return {
            "original_text": text,
            "humanized_text": result_text,
            "mode": mode,
            "meaning_similarity": round(meaning_score, 4),
        }

    def _light_edit(self, sentence: str) -> str:
        result = sentence

        for phrase, replacements in self.synonyms.items():
            if replacements and replacements[0]:
                match = re.search(re.escape(phrase), result, re.IGNORECASE)
                if match:
                    replacement = random.choice(replacements)
                    matched_text = match.group(0)
                    if matched_text.isupper():
                        replacement = replacement.upper()
                    elif matched_text[0].isupper():
                        replacement = replacement[0].upper() + replacement[1:]
                    result = result[:match.start()] + replacement + result[match.end():]

        return result

    def _standard_edit(self, sentence: str) -> str:
        result = self._light_edit(sentence)
        result = self._add_contraction(result)
        result = self._fix_casing(result)
        return result

    def _aggressive_edit(self, sentence: str) -> str:
        result = self._light_edit(sentence)
        result = self._restructure_if_complex(result)
        result = self._swap_clauses(result)
        result = self._change_perspective(result)
        result = self._add_contraction(result)
        result = self._vary_sentence_opening(result)
        result = self._fix_casing(result)
        return result

    def _restructure_if_complex(self, sentence: str) -> str:
        words = sentence.split()
        if len(words) < 14:
            return sentence

        if ", " in sentence:
            parts = sentence.split(", ", 1)
            if len(parts) == 2:
                left = parts[0].strip()
                right = parts[1].strip()
                left_words = left.split()
                right_words = right.split()
                if len(left_words) >= 5 and len(right_words) >= 5:
                    connector = random.choice(["which", "effectively", "meaning"])
                    right_start = right[0].upper() + right[1:]
                    left_lower = left[0].lower() + left[1:]
                    return f"{right_start} {connector} {left_lower}"

        return sentence

    def _swap_clauses(self, sentence: str) -> str:
        connectors = ["although", "because", "when", "while", "if", "since", "unless", "after", "before", "whereas"]
        lower = sentence.lower()
        for conn in connectors:
            pattern = f" {conn} "
            if pattern in lower:
                idx = lower.index(pattern)
                clause1 = sentence[:idx].strip().rstrip(".")
                clause2 = sentence[idx:].strip()
                return f"{clause2[0].upper()}{clause2[1:]}, {clause1.lower()}"
        return sentence

    def _change_perspective(self, sentence: str) -> str:
        for pattern, replacement in self.passive_patterns:
            new = re.sub(pattern, replacement, sentence, count=1)
            if new != sentence:
                return new[0].upper() + new[1:]
        return sentence

    def _vary_sentence_opening(self, sentence: str) -> str:
        if random.random() < 0.3:
            opener = random.choice(self.sentence_starters)
            if not sentence.startswith(opener):
                return f"{opener}{sentence[0].lower()}{sentence[1:]}"
        return sentence

    def _add_contraction(self, sentence: str) -> str:
        contractions = [
            (r'\bit is\b', "it's"),
            (r'\bthat is\b', "that's"),
            (r'\bthere is\b', "there's"),
            (r'\bwe are\b', "we're"),
            (r'\bthey are\b', "they're"),
            (r'\byou are\b', "you're"),
            (r'\bcannot\b', "can't"),
            (r'\bwill not\b', "won't"),
            (r'\bdo not\b', "don't"),
            (r'\bdoes not\b', "doesn't"),
            (r'\bdid not\b', "didn't"),
            (r'\bshould not\b', "shouldn't"),
            (r'\bwould not\b', "wouldn't"),
            (r'\bcould not\b', "couldn't"),
            (r'\bhas not\b', "hasn't"),
            (r'\bhave not\b', "haven't"),
            (r'\bhad not\b', "hadn't"),
            (r'\bwas not\b', "wasn't"),
            (r'\bwere not\b', "weren't"),
            (r'\bI am\b', "I'm"),
            (r'\bis not\b', "isn't"),
            (r'\bare not\b', "aren't"),
        ]
        result = sentence
        for pattern, replacement in contractions:
            result = re.sub(pattern, replacement, result, count=1)
        return result

    def _fix_casing(self, text: str) -> str:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        fixed = []
        for sent in sentences:
            s = sent.strip()
            if not s:
                continue
            if s[0].islower():
                s = s[0].upper() + s[1:]
            s = re.sub(r'\b[aA][iI]\b', 'AI', s)
            s = re.sub(r'(?<=[.!?]\s)([a-z])', lambda m: m.group(0).upper(), s)
            fixed.append(s)
        return " ".join(fixed)

    def _fallback_humanize(self, text: str) -> str:
        paragraphs = self._split_paragraphs(text)
        result = []
        for para in paragraphs:
            sentences = self._split_sentences(para)
            modified = []
            for sent in sentences:
                words = sent.split()
                if len(words) > 8:
                    new_sent = self._light_edit(sent)
                    new_sent = self._add_contraction(new_sent)
                    modified.append(new_sent)
                else:
                    modified.append(sent)
            result.append(" ".join(modified))
        return "\n\n".join(result)

    def _split_paragraphs(self, text: str) -> List[str]:
        paras = re.split(r'\n\s*\n', text.strip())
        return [p.strip() for p in paras if p.strip()]

    def _split_sentences(self, text: str) -> List[str]:
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def _verify_meaning(self, original: str, rewritten: str) -> float:
        orig_words = set(re.findall(r'\b\w+\b', original.lower()))
        rew_words = set(re.findall(r'\b\w+\b', rewritten.lower()))

        if not orig_words:
            return 0.0

        important_orig = {w for w in orig_words if len(w) > 3}
        important_rew = {w for w in rew_words if len(w) > 3}

        if important_orig:
            key_overlap = len(important_orig & important_rew) / len(important_orig)
        else:
            key_overlap = 1.0

        all_intersection = orig_words & rew_words
        all_union = orig_words | rew_words
        jaccard = len(all_intersection) / len(all_union) if all_union else 0.0

        orig_len = len(original.split())
        rew_len = len(rewritten.split())
        length_ratio = min(orig_len, rew_len) / max(orig_len, rew_len) if max(orig_len, rew_len) > 0 else 1.0

        return 0.5 * key_overlap + 0.3 * jaccard + 0.2 * length_ratio

    def humanize_file(self, text: str, mode: str = "standard") -> Dict:
        return self.humanize(text, mode)
