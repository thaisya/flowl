import threading
import json
import time
from queues import *

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