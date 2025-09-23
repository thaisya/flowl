"""Worker threads for ASR and MT."""

import threading
import time
import json
from collections import deque

from utils import (
    THROTTLE_MS,
    MIN_PARTIAL_CHARS,
    MIN_PARTIAL_WORDS,
    filter_partial,
    exec_time_wrap,
)


class ASRWorker(threading.Thread):
    def __init__(self, audio_q: deque, events_q: deque, recognizer, audio_lock: threading.Lock, events_lock: threading.Lock):
        super().__init__(daemon=True)
        self._audio_q = audio_q
        self._events_q = events_q
        self._rec = recognizer
        self._prev_partial = ""
        self._last_partial_time = 0.0
        self._audio_lock = audio_lock
        self._events_lock = events_lock

    @exec_time_wrap
    def generate_final_result(self, data: bytes) -> None:
            res = json.loads(self._rec.Result())
            final_text = res.get("text", "").strip()

            if final_text:
                with self._events_lock:
                    self._events_q.append(("final", final_text))
            self._prev_partial = ""

    def generate_partial_result(self, data: bytes) -> None:
        now = time.time() * 1000
        if now - self._last_partial_time < THROTTLE_MS:
            return

        self._last_partial_time = now

        pres = json.loads(self._rec.PartialResult())
        partial_text = pres.get("partial", "").strip()

        if not partial_text or partial_text == self._prev_partial or (len(partial_text) < MIN_PARTIAL_CHARS and len(partial_text.split()) < MIN_PARTIAL_WORDS):
            return

        with self._events_lock:
            self._events_q.append(("partial", partial_text))
        self._prev_partial = partial_text


    def run(self) -> None:
        while True:
            try:
                with self._audio_lock:
                    if not self._audio_q:
                        time.sleep(0.001)
                        continue
                    data = self._audio_q.popleft()
                    if data is None:
                        print("[ASR EXIT]")
                        break
            except IndexError:
                time.sleep(0.001)
                continue

            try:
                if self._rec.AcceptWaveform(data):
                    self.generate_final_result(data)
                else:
                    self.generate_partial_result(data)
            except Exception as e:
                print(f"[ASR ERROR] --> {e}")


class MTWorker(threading.Thread):
    def __init__(self, events_q: deque, translate_fn, events_lock: threading.Lock):
        super().__init__(daemon=True)
        self._events_q = events_q
        self._translate = translate_fn
        self._events_lock = events_lock
        self._last_emit_time = 0.0
        self._last_shown_partial = ""

    @exec_time_wrap
    def output_final_result(self, text) -> None:
        final_text_sliced = ""
        partial_text_sliced = ""
        try:
            partial_half_word_count = len(self._last_shown_partial.split()) // 2
            
            text_words = text.split()
            if 0 < partial_half_word_count <= len(text_words):
                final_text_sliced = " ".join(text_words[-partial_half_word_count:])
            else:
                final_text_sliced = text
            partial_words = self._last_shown_partial.split()
            if 0 < partial_half_word_count <= len(partial_words):
                partial_text_sliced = " ".join(partial_words[-partial_half_word_count:])
            else:
                partial_text_sliced = self._last_shown_partial

        except (IndexError, ValueError):
            pass
        if final_text_sliced != partial_text_sliced and len(final_text_sliced) >= MIN_PARTIAL_CHARS:
            try:
                print(f"[FINAL] {final_text_sliced} --> {self._translate(final_text_sliced)}")
            except Exception as e:
                print(f"[FINAL ERROR] {final_text_sliced} --> {e}")
        self._last_emit_time = 0
        self._last_shown_partial = ""


    def output_partial_result(self, text: str) -> None:
        now = time.time() * 1000.0
        if now - self._last_emit_time < THROTTLE_MS:
            return

        if text == self._last_shown_partial:
            return

        if len(text) < MIN_PARTIAL_CHARS and len(text.split()) < MIN_PARTIAL_WORDS:
            return

        text = filter_partial(text)
        try:
            translated_partial = self._translate(text)
            print(f"[PARTIAL] {text} --> {translated_partial}")
            self._last_emit_time = now
            self._last_shown_partial = text
        except Exception as e:
            print(f"[PARTIAL ERROR] --> {e}")
        

    def run(self) -> None:
        while True:
            try:
                with self._events_lock:
                    if not self._events_q:
                        time.sleep(0.001)
                        continue
                    text_type, text = self._events_q.popleft()
            except IndexError:
                time.sleep(0.001)
                continue

            if text_type == "final":
                if text is None:
                    print("[FINAL EXIT]")
                    break
                self.output_final_result(text)

            elif text_type == "partial":
                self.output_partial_result(text)


            
