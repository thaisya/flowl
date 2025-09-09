"""Application entry point for Flowl real-time translator."""

import time
from src.audio import (
    workers_init,
    stream,
    t_asr,
    t_mt,
    p,
    audio_q,
    events_q,
)

def main():
    """Initialize audio workers and keep the main loop alive until interrupted."""
    workers_init()
    try:
        while stream.is_active():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Manual exit")
    finally:
        shutdown()

def shutdown():
    """Gracefully stop audio stream, signal threads to exit, and cleanup resources."""
    stream.stop_stream()
    stream.close()
    audio_q.put(None)
    events_q.put(("final", "exit"))
    t_asr.join(timeout=1.0)
    t_mt.join(timeout=1.0)
    p.terminate()

if __name__ == "__main__":
    main()

