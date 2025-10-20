"""Small text utilities for Flowl."""

import time
from .settings import get_max_partial_words

# All configuration constants have been moved to settings.py
# Use the getter functions from settings.py instead

def filter_partial(text: str) -> str:
    """Trim a partial string to the last MAX_PARTIAL_WORDS words."""
    words = text.split()
    max_words = get_max_partial_words()
    if len(words) > max_words:
        text = " ".join(words[-max_words:])
    return text

def exec_time_wrap(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f'Function {func.__name__} took {end - start:.6f} seconds\n')
        return result
    return wrapper
 