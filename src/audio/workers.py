"""Worker threads for ASR and MT."""

import threading
import time
import json
import numpy as np
from collections import deque

from utils import (
    THROTTLE_MS,
    MIN_PARTIAL_CHARS,
    MIN_PARTIAL_WORDS,
    filter_partial,
)


class ASRWorker(threading.Thread):
    def __init__(self, audio_q: deque, events_q: deque, recognizer):
        super().__init__(daemon=True)
        self._audio_q = audio_q
        self._events_q = events_q
        self._rec = recognizer

    def run(self) -> None:
        prev_partial = ""
        while True:
            try:
                if not self._audio_q:
                    time.sleep(0.1)
                    continue
                data = self._audio_q.popleft()
                if data is None:
                    break
            except IndexError:
                time.sleep(0.1)
                continue

            try:
                if self._rec.AcceptWaveform(data):
                    res = json.loads(self._rec.Result())
                    final_text = res.get("text", "").strip()
                    if final_text:
                        self._events_q.append(("final", final_text))
                    prev_partial = ""
                else:
                    pres = json.loads(self._rec.PartialResult())
                    partial_text = pres.get("partial", "").strip()
                    if partial_text and partial_text != prev_partial:
                        self._events_q.append(("partial", partial_text))
                        prev_partial = partial_text
            except Exception as e:
                print(f"[ASR ERROR] --> {e}")


class MTWorker(threading.Thread):
    def __init__(self, events_q: deque, translate_fn):
        super().__init__(daemon=True)
        self._events_q = events_q
        self._translate = translate_fn

    def run(self) -> None:
        last_emit_time = 0.0
        last_shown_partial = ""

        while True:
            try:
                if not self._events_q:
                    time.sleep(0.1)
                    continue
                ev_type, text = self._events_q.popleft()
            except IndexError:
                time.sleep(0.1)
                continue

            if ev_type == "final":
                if text == "exit":
                    print("[FINAL EXIT]")
                    break
                try:
                    translated_final = self._translate(text)
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
                translated_partial = self._translate(text)
                print(f"[PARTIAL] {text} --> {translated_partial}")
                last_emit_time = now_time_ms
                last_shown_partial = text
            except Exception as e:
                print(f"[PARTIAL ERROR] --> {e}")
