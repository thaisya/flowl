from dataclasses import dataclass
from typing import List, Tuple
from utils.utils import longest_common_prefix

@dataclass
class Segment:
    text: str
    state: int
    score: int

class TriStateBuffer:
    """
    Manages ASR partials by tracking the stability of individual words.
    
    States:
    - HARD (Score 3+): Fixated context, awaiting punctuation commit.
    - SOFT (Score 1-2): Semistable, surviving partial updates.
    - TAIL (Score 0): Brand new words.
    """
    
    def __init__(self):
        # List of dictionaries: {"text": str, "score": int}
        self.words = []
        self.HARD_THRESHOLD = 3
        
    def update(self, partial_text: str) -> None:
        """Calculates new word scores using Longest Common Prefix."""
        if not partial_text.strip():
            self.words = []
            return

        new_texts = partial_text.split()
        old_texts = [w["text"] for w in self.words]
        
        # Find Longest Common Prefix
        lcp = longest_common_prefix(old_texts, new_texts)
        lcp_len = len(lcp)
        
        updated_words = []
        
        # 1. Update scores for words in LCP
        for i in range(lcp_len):
            old_score = self.words[i]["score"]
            # Increment score, capped at 4
            new_score = min(old_score + 1, 4)
            updated_words.append({"text": new_texts[i], "score": new_score})
            
        # 2. Append remaining new words as TAIL
        for i in range(lcp_len, len(new_texts)):
            updated_words.append({"text": new_texts[i], "score": 0})
            
        self.words = updated_words

    def extract_committed(self) -> str:
        """
        Scans for the LAST word that is HARD and punctuated.
        Pops the buffer up to that point and returns the committed string.
        """
        commit_idx = -1
        punctuation_marks = {'.', '?', '!', '。', '？', '！', '؟', '।', ';'}
        
        for i, w in enumerate(self.words):
            text = w["text"]
            score = w["score"]
            
            # Check if word ends with punctuation and is HARD
            has_punct = len(text) > 0 and text[-1] in punctuation_marks
            is_hard = score >= self.HARD_THRESHOLD
            
            if is_hard and has_punct:
                commit_idx = i
                
            # If we hit a soft/tail word, stop looking ahead. 
            # (Contiguous rule implies everything after is soft/tail)
            if score < self.HARD_THRESHOLD:
                break
                
        if commit_idx != -1:
            committed_texts = [w["text"] for w in self.words[:commit_idx + 1]]
            # Pop committed words
            self.words = self.words[commit_idx + 1:]
            return " ".join(committed_texts)
            
        return ""

    def get_all_text(self) -> str:
        """Returns all currently buffered words (Active Translation Window)."""
        return " ".join(w["text"] for w in self.words)

    def get_active_segments(self) -> Tuple[str, str]:
        """Returns (stable_text, tail_text). Stable is HARD+SOFT (score > 0)."""
        stable = [w["text"] for w in self.words if w["score"] > 0]
        tail = [w["text"] for w in self.words if w["score"] == 0]
        return " ".join(stable), " ".join(tail)

    def reset(self):
        """Clear history (call on Final result)."""
        self.words = []