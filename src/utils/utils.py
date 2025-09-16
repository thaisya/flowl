"""Runtime configuration and small text utilities for Flowl."""

import argparse
import time


# TODO min, max validation (not necessary for now)

def get_args() -> argparse.Namespace:
    """Parse CLI arguments for audio rates, throttling and language settings."""
    parser = argparse.ArgumentParser(description="Flowl - a real-time lightweight offline translator",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--rate", type=int, default=16000, help = "Audio rate Hz")
    parser.add_argument("--frames-per-buffer", type=int, default=1024, help="How many frames processed at once")
    parser.add_argument("--throttle-ms", type=int, default=200, help="Interval for PARTIAL-output")
    parser.add_argument("--max-part-words", type=int, default=20, help="Max words to buildup in partial")
    parser.add_argument("--min-part-words", type=int, default=1, help="Min words to translate at once (NOT recommended to change)")
    parser.add_argument("--min-part-chars", type=int, default=1, help="Min chars to translate at once (NOT recommended to change)")
    parser.add_argument("--from-code", choices=["en", "ru"], default="en", help="From language")
    parser.add_argument("--to-code", choices=["en", "ru"], default="ru", help="To language")
    parser.add_argument("--use-mic", action="store_true", help="Use microphone as input device")
    return parser.parse_args()

arguments = get_args()

AUDIO_RATE = arguments.rate
FRAMES_PER_BUFFER = arguments.frames_per_buffer
THROTTLE_MS = arguments.throttle_ms
MAX_PARTIAL_WORDS = arguments.max_part_words
MIN_PARTIAL_CHARS = arguments.min_part_chars
MIN_PARTIAL_WORDS = arguments.min_part_words
FROM_CODE = arguments.from_code
TO_CODE = arguments.to_code
MODEL_PATH = r"C:\Users\nikit\Desktop\Flowl_necessary_files\vosk-en" if arguments.from_code == "en" else r"C:\Users\nikit\Desktop\Flowl_necessary_files\vosk-ru"
MT_MODEL_PATH = "Helsinki-NLP/opus-mt-en-ru" if arguments.from_code == "en" else "Helsinki-NLP/opus-mt-ru-en"
MIC_MODE = arguments.use_mic


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
        print(f'Function {func.__name__} took {end - start:.6f} seconds')
        return result
    return wrapper