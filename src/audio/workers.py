"""Worker threads for ASR and MT."""

import threading
import queue
import time
import json
import numpy as np

from utils import (
    THROTTLE_MS,
    MIN_PARTIAL_CHARS,
    MIN_PARTIAL_WORDS,
    filter_partial,
)


class ASRWorker(threading.Thread):
    def __init__(self, audio_q: queue.Queue, events_q: queue.Queue, recognizer):
        super().__init__(daemon=True)
        self._audio_q = audio_q
        self._events_q = events_q
        self._rec = recognizer

    def run(self) -> None:
        prev_partial = ""
        while True:
            try:
                data = self._audio_q.get(timeout=0.1)
                if data is None:
                    break
            except queue.Empty:
                continue

            try:
                if self._rec.AcceptWaveform(data):
                    res = json.loads(self._rec.Result())
                    final_text = res.get("text", "").strip()
                    if final_text:
                        self._events_q.put(("final", final_text))
                    prev_partial = ""
                else:
                    pres = json.loads(self._rec.PartialResult())
                    partial_text = pres.get("partial", "").strip()
                    if partial_text and partial_text != prev_partial:
                        self._events_q.put(("partial", partial_text))
                        prev_partial = partial_text
            except Exception as e:
                print(f"[ASR ERROR] --> {e}")


class MTWorker(threading.Thread):
    def __init__(self, events_q: queue.Queue, translate_fn):
        super().__init__(daemon=True)
        self._events_q = events_q
        self._translate = translate_fn

    def run(self) -> None:
        last_emit_time = 0.0
        last_shown_partial = ""

        while True:
            try:
                ev_type, text = self._events_q.get(timeout=0.1)
            except queue.Empty:
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


#TODO not mine logic and will be deleted soon
class MixerWorker(threading.Thread):
    def __init__(self, mic_q: queue.Queue, loop_q: queue.Queue, out_q: queue.Queue):
        super().__init__(daemon=True)
        self._mic_q = mic_q
        self._loop_q = loop_q
        self._out_q = out_q
        self._mic_done = False
        self._loop_done = False

    def _mix_int16(self, a_bytes: bytes | None, b_bytes: bytes | None) -> bytes | None:
        if a_bytes is None and b_bytes is None:
            return None
        if a_bytes is None:
            return b_bytes
        if b_bytes is None:
            return a_bytes
        
        try:
            # Validate input data length (must be even for int16)
            if len(a_bytes) % 2 != 0 or len(b_bytes) % 2 != 0:
                print(f"[MIXER WARNING] Invalid audio data length - skipping frame")
                return None
            
            a = np.frombuffer(a_bytes, dtype=np.int16)
            b = np.frombuffer(b_bytes, dtype=np.int16)
            
            # Ensure we have valid audio data
            if len(a) == 0 or len(b) == 0:
                print(f"[MIXER WARNING] Empty audio data - skipping frame")
                return None
                
            if a.shape != b.shape:
                n = min(a.shape[0], b.shape[0])
                a = a[:n]
                b = b[:n]
            
            mixed = a.astype(np.int32) + b.astype(np.int32)
            np.clip(mixed, -32768, 32767, out=mixed)
            return mixed.astype(np.int16).tobytes()
            
        except (ValueError, TypeError) as e:
            print(f"[MIXER ERROR] Invalid audio data format: {e}")
            return None

    def run(self) -> None:
        while True:
            mic_chunk = None
            loop_chunk = None

            if not self._mic_done:
                try:
                    item = self._mic_q.get(timeout=0.05)
                    if item is None:
                        self._mic_done = True
                    else:
                        mic_chunk = item
                except queue.Empty:
                    pass

            if not self._loop_done:
                try:
                    item = self._loop_q.get(timeout=0.05)
                    if item is None:
                        self._loop_done = True
                    else:
                        loop_chunk = item
                except queue.Empty:
                    pass

            if self._mic_done and self._loop_done:
                self._out_q.put(None)
                break

            mixed = self._mix_int16(mic_chunk, loop_chunk)
            if mixed is None:
                continue
            try:
                self._out_q.put_nowait(mixed)
            except queue.Full:
                continue

