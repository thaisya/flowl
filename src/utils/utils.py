"""Runtime configuration and small text utilities for Flowl."""

import argparse
import time
from typing import Final


# TODO min, max validation (not necessary for now)

def get_args() -> argparse.Namespace:
    """Parse CLI arguments for audio rates, throttling and language settings."""
    parser = argparse.ArgumentParser(description="Flowl - a real-time lightweight offline translator",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--rate", type=int, default=16000, help = "Audio rate Hz")
    parser.add_argument("--frames-per-buffer", type=int, default=2048, help="How many frames processed at once")
    parser.add_argument("--throttle-ms", type=int, default=50, help="Interval for PARTIAL-output")
    parser.add_argument("--max-part-words", type=int, default=16, help="Max words to buildup in partial")
    parser.add_argument("--min-part-words", type=int, default=1, help="Min words to translate at once (NOT recommended to change)")
    parser.add_argument("--min-part-chars", type=int, default=1, help="Min chars to translate at once (NOT recommended to change)")
    parser.add_argument("--from-code", choices=["en", "ru"], default="en", help="From language")
    parser.add_argument("--to-code", choices=["en", "ru"], default="ru", help="To language")
    parser.add_argument("--use-mic", action="store_true", help="Use microphone as input device")
    return parser.parse_args()

arguments = get_args()

# Audio configuration constants
AUDIO_RATE: Final[int] = arguments.rate
FRAMES_PER_BUFFER: Final[int] = arguments.frames_per_buffer
THROTTLE_MS: Final[int] = arguments.throttle_ms
MAX_PARTIAL_WORDS: Final[int] = arguments.max_part_words
MIN_PARTIAL_CHARS: Final[int] = arguments.min_part_chars
MIN_PARTIAL_WORDS: Final[int] = arguments.min_part_words

# Language configuration constants
FROM_CODE: Final[str] = arguments.from_code
TO_CODE: Final[str] = arguments.to_code

# Model paths
MODEL_PATH: Final[str] = r"C:\Users\nikit\Desktop\Flowl_necessary_files\vosk-en" if arguments.from_code == "en" else r"C:\Users\nikit\Desktop\Flowl_necessary_files\vosk-ru"
MT_MODEL_PATH: Final[str] = "Helsinki-NLP/opus-mt-en-ru" if arguments.from_code == "en" else "Helsinki-NLP/opus-mt-ru-en"

# Mode flags
MIC_MODE: Final[bool] = arguments.use_mic


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
 