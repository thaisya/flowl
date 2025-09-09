"""Thread-safe queues for audio data and ASR/MT events."""

import queue

audio_q = queue.Queue(maxsize=100)
"""Raw audio chunks captured by PyAudio callback."""

events_q = queue.Queue(maxsize=200)
"""Events emitted by ASR (partial/final) consumed by the MT thread."""