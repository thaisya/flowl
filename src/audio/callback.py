"""PyAudio stream callback that forwards raw audio frames to the audio queue."""

import queue
import pyaudio
from .queues import audio_q

def audio_callback(in_data, frame_count, time_info, status):
    """Push input audio frames to `audio_q`; continue streaming regardless of queue state."""
    try:
        audio_q.put_nowait(in_data)
    except queue.Full:
        pass
    return (None, pyaudio.paContinue)