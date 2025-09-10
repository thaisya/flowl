"""Runtime configuration and small text utilities for Flowl."""

import argparse

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
    return parser.parse_args()

args = get_args()

AUDIO_RATE = args.rate
FRAMES_PER_BUFFER = args.frames_per_buffer
THROTTLE_MS = args.throttle_ms
MAX_PARTIAL_WORDS = args.max_part_words
MIN_PARTIAL_CHARS = args.min_part_chars
MIN_PARTIAL_WORDS = args.min_part_words
FROM_CODE = args.from_code
TO_CODE = args.to_code
MODEL_PATH = r"C:\Users\nikit\Desktop\Flowl_necessary_files\vosk-en" if args.from_code == "en" else r"C:\Users\nikit\Desktop\Flowl_necessary_files\vosk-ru"
MT_MODEL_PATH = "Helsinki-NLP/opus-mt-en-ru" if args.from_code == "en" else "Helsinki-NLP/opus-mt-ru-en"


def filter_partial(text: str) -> str:
    """Trim a partial string to the last MAX_PARTIAL_WORDS words."""
    words = text.split()
    if len(words) > MAX_PARTIAL_WORDS:
        text = " ".join(words[-MAX_PARTIAL_WORDS:])
    return text