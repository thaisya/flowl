"""Utilities for Flowl."""

import time
from typing import Sequence
from .logger import logger

def longest_common_prefix(seq1: Sequence, seq2: Sequence) -> Sequence:
    """Return the longest common prefix of two sequences (strings, lists, etc)."""
    min_len = min(len(seq1), len(seq2))
    for i in range(min_len):
        if seq1[i] != seq2[i]:
            return seq1[:i]
    return seq1[:min_len]

def filter_partial(text: str, max_words: int) -> str:
    """Trim a partial string to the last max_words words."""
    words = text.split()
    if len(words) > max_words:
        text = " ".join(words[-max_words:])
    return text

def exec_time_wrap(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        logger.debug(f'Function {func.__name__} took {end - start:.6f} seconds', "PERF")
        return result
    return wrapper
 
