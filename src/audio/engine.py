"""Audio engine: manages sounddevice and pushes frames to a queue via callback."""

from typing import Callable, Tuple
import queue
import sounddevice as sd
import numpy as np

from utils import AUDIO_RATE, FRAMES_PER_BUFFER, DeviceManager


class AudioEngine:
    def __init__(self, on_audio: Callable[[bytes], None], input_device_kind: str):
        self._on_audio = on_audio 
        self._stream = None
        if input_device_kind == "microphone":
            self._input_device_index = DeviceManager().get_input_microphone_index()
        elif input_device_kind == "loopback":
            self._input_device_index = DeviceManager().get_input_loopback_index()
        else:
            raise ValueError(f"Invalid input device kind: {input_device_kind}")

    
    def _callback(self, in_data: np.ndarray, frame_count: int, time_info, status) -> None:
        if status:
            print("Audio callback Status:", status)
        try:
            self._on_audio(in_data.tobytes())
        except queue.Full:
            pass

    def start(self) -> None:
        if self._input_device_index is None:
            raise RuntimeError("No valid input device found")
        
        if self._stream is None:
            self._stream = sd.InputStream(device=self._input_device_index, 
                                frames_per_buffer=FRAMES_PER_BUFFER,
                                 samplerate=AUDIO_RATE,
                                 channels=1,
                                 dtype=np.float32,
                                 callback=self._callback)
        self._stream.start()

    def is_active(self) -> bool:
        return self._stream is not None and self._stream.active

    def stop(self) -> None:
        if self._stream is not None:
            if self._stream.active:
                self._stream.stop()
            self._stream.close()
            self._stream = None


