import queue
import pyaudio
from .queues import audio_q

def audio_callback(in_data, frame_count, time_info, status):
    try:
        audio_q.put_nowait(in_data)
    except queue.Full:
        pass
    return (None, pyaudio.paContinue)