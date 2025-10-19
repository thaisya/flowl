"""Small text utilities for Flowl."""

import time
from typing import Final
from .settings import get_settings

# Get settings instance
settings = get_settings()

# Audio configuration constants (for backward compatibility)
AUDIO_RATE: Final[int] = settings.rate
FRAMES_PER_BUFFER: Final[int] = settings.frames_per_buffer
THROTTLE_MS: Final[int] = settings.throttle_ms
MAX_PARTIAL_WORDS: Final[int] = settings.max_part_words
MIN_PARTIAL_CHARS: Final[int] = settings.min_part_chars
MIN_PARTIAL_WORDS: Final[int] = settings.min_part_words

# Language configuration constants (for backward compatibility)
FROM_CODE: Final[str] = settings.from_code
TO_CODE: Final[str] = settings.to_code

# Model paths (for backward compatibility)
MODEL_PATH: Final[str] = settings.model_path
MT_MODEL_PATH: Final[str] = settings.mt_model_path

# Mode flags (for backward compatibility)
MIC_MODE: Final[bool] = settings.use_mic
CONSOLE_MODE: Final[bool] = settings.console_mode

def filter_partial(text: str) -> str:
    """Trim a partial string to the last MAX_PARTIAL_WORDS words."""
    words = text.split()
    if len(words) > MAX_PARTIAL_WORDS:
        text = " ".join(words[-MAX_PARTIAL_WORDS:])
    return text

def exec_time_wrap(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f'Function {func.__name__} took {end - start:.6f} seconds\n')
        return result
    return wrapper
 