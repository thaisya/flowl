import time
import json
import queue
import threading
import argparse

import pyaudio
from vosk import Model, KaldiRecognizer
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


# ------------------- parameters.py + arg_parser.py + QUEUES -------------------

# TODO min, max validation (not necessary for now)
def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Flowl - a real-time lightweight offline translator",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--rate", type=int, default=16000, help = "Audio rate Hz")
    parser.add_argument("--frames-per-buffer", type=int, default=1024, help="How many frames processed at once")
    parser.add_argument("--throttle-ms", type=int, default=200, help="Interval for PARTIAL-output")
    parser.add_argument("--max-part-words", type=int, default=20, help="Max words to buildup in partial")
    parser.add_argument("--min-part-words", type=int, default=1, help="Min words to translate at once (NOT recommended to change)")
    parser.add_argument("--min-part-chars", type=int, default=1, help="Min chars to translate at once (NOT recommended to change)")
    parser.add_argument("--from-code", choices=["en", "ru"], default="ru", help="From language")
    parser.add_argument("--to-code", choices=["en", "ru"], default="en", help="To language")
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
audio_q = queue.Queue(maxsize=100)
events_q = queue.Queue(maxsize=200)

# ------------------- models.py -------------------

model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, AUDIO_RATE)

# TODO convert to ONNX later
tokenizer = AutoTokenizer.from_pretrained(MT_MODEL_PATH)
mt_model = AutoModelForSeq2SeqLM.from_pretrained(MT_MODEL_PATH)

def translate(text):
    inputs = tokenizer(text, return_tensors="pt")
    outputs = mt_model.generate(**inputs)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# ------------------- callback.py -------------------

def audio_callback(in_data, frame_count, time_info, status):
    try:
        audio_q.put_nowait(in_data)
    except queue.Full:
        pass
    return (None, pyaudio.paContinue)

# ------------------- utils.py -------------------

def filter_partial(text: str) -> str:
    words = text.split()
    if len(words) > MAX_PARTIAL_WORDS:
        text = " ".join(words[-MAX_PARTIAL_WORDS:])
    return text

# ------------------- ASR thread -------------------

def asr_thread():
    prev_partial = ""
    data = ""
    while True:
        try:
            data = audio_q.get(timeout=0.1)
            if data is None:
                break
        except queue.Empty:
            pass

        try:
            if recognizer.AcceptWaveform(data):
                res = json.loads(recognizer.Result())
                final_text = res.get("text", "").strip()
                if final_text:
                    events_q.put(("final", final_text))
                prev_partial = ""

            else:
                pres = json.loads(recognizer.PartialResult())
                partial_text = pres.get("partial", "").strip()
                if not partial_text or partial_text == prev_partial:
                    continue
                events_q.put(("partial", partial_text))
                prev_partial = partial_text

        except Exception as e:
            print(f"[ASR ERROR] --> {e}")

# ------------------- MT thread -------------------

def mt_thread():
    last_emit_time = 0
    last_shown_partial = ""

    while True:
        try:
            ev_type, text = events_q.get_nowait()
        except queue.Empty:
            continue

        if ev_type == "final":
            if text == "exit":
                print("[FINAL EXIT]")
                break

            try:
                translated_final = translate(text)
                print(f"[FINAL] {text} --> {translated_final}")
            except Exception as e:
                print(f"[FINAL ERROR] {text} --> {e}")

            last_emit_time = 0
            last_shown_partial = ""
            continue

        if len(text) < MIN_PARTIAL_CHARS and len(text.split()) < MIN_PARTIAL_WORDS:
            continue
        text = filter_partial(text)
        now_time_ms = time.time() * 1000.0
        if text == last_shown_partial:
            continue
        if now_time_ms - last_emit_time < THROTTLE_MS:
            continue

        try:
            translated_partial = translate(text)
            print(f"[PARTIAL] {text} --> {translated_partial}")
            last_emit_time = now_time_ms
            last_shown_partial = text
        except Exception as e:
            print(f"[PARTIAL ERROR] --> {e}")

# ------------------- threads.py -------------------

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=AUDIO_RATE,
                input=True,
                frames_per_buffer=FRAMES_PER_BUFFER,
                stream_callback=audio_callback)
t_asr = threading.Thread(target=asr_thread, daemon=True)
t_mt = threading.Thread(target=mt_thread, daemon=True)

def workers_init():
    try:
        stream.start_stream()
        t_asr.start()
        t_mt.start()
        print("Initialization successful. Start talking (say 'exit' to quit).")
    except Exception as e:
        print(f"An error had occurred during initialization --> {e}")

# ------------------- main.py -------------------

def main():
    workers_init()
    try:
        while stream.is_active():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Manual exit")

    stream.stop_stream()
    stream.close()

    audio_q.put(None)
    events_q.put(("final", "exit"))

    t_asr.join(timeout=1.0)
    t_mt.join(timeout=1.0)

    p.terminate()

if __name__ == "__main__":
    main()
