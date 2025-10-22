"""Small text utilities for Flowl."""

import time
from .logger import logger

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
 