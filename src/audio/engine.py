"""Audio engine: manages PyAudio and pushes frames to a queue via callback."""

from typing import Callable, Tuple
import queue
import sounddevice as sd
import numpy as np

from utils import AUDIO_RATE, FRAMES_PER_BUFFER


class AudioEngine:
    def __init__(self, on_audio: Callable[[bytes], None], input_device_kind: str):
        self._on_audio = on_audio 
        self._stream = None
        self._input_device_index = input_device_kind

    
    def _callback(self, in_data: bytes, frame_count: int, time_info, status) -> None:
        if status:
            print("Audio callback Status:", status)
        try:
            self._on_audio(in_data.tobytes())
        except queue.Full:
            pass

    def start(self) -> None:
        if self._stream is None:
            self._stream = sd.inputStream(device=self._input_device_kind.index, 
                                frames_per_buffer=FRAMES_PER_BUFFER,
                                 samplerate=AUDIO_RATE,
                                 channels=1,
                                 dtype=np.float32,
                                 callback=self._callback)
        self._stream.start()

    def is_active(self) -> bool:
        return self._stream is not None and self._stream.is_active()

    def stop(self) -> None:
        if self._stream is None:
            if self._stream.is_active():
                self._stream.stop_stream()
            self._stream.close()
            self._stream = None


